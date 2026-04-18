from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import gymnasium as gym
import numpy as np
from sumo_rl import SumoEnvironment

from .results import EpisodeRecorder


class DqnSumoEnv(gym.Env[np.ndarray, int]):
    def __init__(
        self,
        *,
        net_file: Path,
        route_files: Sequence[Path],
        tls_id: str,
        decision_interval: int,
        yellow_time: int,
        min_green: int,
        num_seconds: int,
        reward_fn: str,
        use_gui: bool,
        sumo_seed: int | str,
        terminate_on_no_vehicles: bool = False,
        output_dir: Path | None = None,
        inbound_lanes: dict[str, list[str]] | None = None,
        record_steps: bool = False,
    ) -> None:
        super().__init__()

        if not route_files:
            raise ValueError("route_files cannot be empty.")

        self.net_file = net_file.resolve()
        self.route_files = [route_file.resolve() for route_file in route_files]
        self.tls_id = tls_id
        self.decision_interval = decision_interval
        self.yellow_time = yellow_time
        self.min_green = min_green
        self.num_seconds = num_seconds
        self.reward_fn = reward_fn
        self.use_gui = use_gui
        self.sumo_seed = sumo_seed
        self.terminate_on_no_vehicles = terminate_on_no_vehicles
        self.output_dir = output_dir
        self.inbound_lanes = inbound_lanes or {}
        self.record_steps = record_steps

        self._route_index = 0
        self._current_route_file: Path = self.route_files[0]
        self._env = self._build_env(self._current_route_file)
        self._recorder: EpisodeRecorder | None = None
        self._last_sim_step = 0.0

        self.action_space = self._env.action_space
        self.observation_space = self._env.observation_space

    def _build_env(self, route_file: Path) -> SumoEnvironment:
        additional_sumo_cmd = None
        if self.output_dir is not None:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            additional_sumo_cmd = (
                f"--tripinfo-output {self.output_dir / 'tripinfo.xml'} "
                f"--statistic-output {self.output_dir / 'statistic.xml'} "
            )

        return SumoEnvironment(
            net_file=str(self.net_file),
            route_file=str(route_file),
            out_csv_name=None,
            single_agent=True,
            use_gui=self.use_gui,
            num_seconds=self.num_seconds,
            delta_time=self.decision_interval,
            yellow_time=self.yellow_time,
            min_green=self.min_green,
            reward_fn=self.reward_fn,
            add_system_info=False,
            add_per_agent_info=False,
            ts_ids=[self.tls_id],
            sumo_seed=self.sumo_seed,
            sumo_warnings=False,
            additional_sumo_cmd=additional_sumo_cmd,
        )

    def _select_route_file(self, options: dict[str, Any] | None) -> Path:
        if options is not None and "route_file" in options:
            return Path(options["route_file"]).resolve()

        route_file = self.route_files[self._route_index % len(self.route_files)]
        self._route_index += 1
        return route_file

    def _set_route_file_if_needed(self, route_file: Path) -> None:
        if self._current_route_file == route_file:
            return
        # sumo-rl reads this field when starting simulation in reset()
        self._env._route = str(route_file)  # type: ignore[attr-defined]
        self._current_route_file = route_file

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        route_file = self._select_route_file(options)
        self._set_route_file_if_needed(route_file)

        if self.record_steps:
            self._recorder = EpisodeRecorder(
                tls_id=self.tls_id,
                inbound_lanes={approach: list(lanes) for approach, lanes in self.inbound_lanes.items()},
            )
        else:
            self._recorder = None

        observation, info = self._env.reset(seed=seed)
        info = dict(info)
        self._last_sim_step = float(info.get("step", 0.0))
        info["route_file"] = str(route_file)
        return observation, info

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        traffic_signal = self._env.traffic_signals[self.tls_id]
        if traffic_signal.time_to_act:
            traffic_signal.set_next_phase(int(action))

        # sumo-rl already exposes the traffic signal state machine, but its public
        # step() advances the whole decision window at once. Stepping the internal
        # simulation second-by-second keeps training semantics aligned with sumo-rl
        # while letting evaluation log queues exactly like the baseline code.

        max_inner_steps = max(1, self._env.delta_time + self._env.yellow_time + self._env.min_green + 5)
        for _ in range(max_inner_steps):
            terminated, truncated = self._episode_flags()
            if terminated or truncated:
                break

            self._env._sumo_step()

            self._last_sim_step = float(self._env.sim_step)

            for ts in self._env.ts_ids:
                self._env.traffic_signals[ts].update()

            if self._recorder is not None:
                self._recorder.record_step(self._env.sumo)

            terminated, truncated = self._episode_flags()
            if terminated or truncated:
                break

            if any(self._env.traffic_signals[ts].time_to_act for ts in self._env.ts_ids):
                break
        else:
            raise RuntimeError(
                f"Inner step loop exceeded {max_inner_steps} seconds without reaching "
                f"time_to_act or termination. sim_step={self._last_sim_step}, tls_id={self.tls_id}"
            )

        traffic_signal = self._env.traffic_signals[self.tls_id]
        observation = traffic_signal.compute_observation()
        reward = traffic_signal.compute_reward()
        min_expected_number = self._min_expected_number()
        info = {
            "step": self._last_sim_step,
            "tls_id": self.tls_id,
            "time_to_act": traffic_signal.time_to_act,
            "min_expected_number": min_expected_number,
            "terminated": terminated,
            "truncated": truncated,
            "episode_end_reason": (
                "time_limit"
                if truncated
                else "no_more_vehicles"
                if terminated
                else "in_progress"
            ),
        }

        return observation, reward, terminated, truncated, info

    def _episode_flags(self) -> tuple[bool, bool]:
        self._last_sim_step = float(self._env.sim_step)
        truncated = self._last_sim_step >= self._env.sim_max_time
        terminated = self.terminate_on_no_vehicles and not truncated and self._min_expected_number() <= 0
        return terminated, truncated

    def _min_expected_number(self) -> int:
        return int(self._env.sumo.simulation.getMinExpectedNumber())

    def pop_recorded_rows(self) -> list[dict[str, Any]]:
        if self._recorder is None:
            return []
        return list(self._recorder.rows)

    def close(self) -> None:
        self._env.close()
