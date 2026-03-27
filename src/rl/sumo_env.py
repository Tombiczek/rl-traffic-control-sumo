from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import traci

from phase_mapping import ACTION_TO_PHASE, GREEN_TO_YELLOW, TLS_ID


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUMOCFG = PROJECT_ROOT / "data" / "osm.sumocfg"


DEFAULT_INBOUND_LANES = {
	"N": ["450749096#0_0", "450749096#0_1", "450749096#0_2", "450749096#0_3"],
	"S": ["1029639687#0_0", "1029639687#0_1", "1029639687#0_2"],
	"E": ["1454977049#0_0", "1454977049#0_1", "1454977049#0_2"],
	"W": ["231737246#0_0", "231737246#0_1", "231737246#0_2"],
}


@dataclass
class SumoEnvConfig:
	sumocfg_path: Path = DEFAULT_SUMOCFG
	tls_id: str = TLS_ID
	remote_host: str = "127.0.0.1"
	remote_port: int = 8813
	sumo_extra_args: tuple[str, ...] = ()
	decision_interval: int = 5
	yellow_duration: int = 3
	min_green_duration: int = 10
	max_episode_steps: int = 3600
	reward_switch_penalty: float = 0.2
	queue_bins: tuple[int, ...] = (0, 3, 8)


class SumoTrafficEnv:
	"""Environment wrapper between SUMO and a DQN-like traffic signal agent.

	Action space is defined by `ACTION_TO_PHASE` from `phase_mapping.py`.
	Each action points to one SUMO green phase index.

	Observation is a discrete tuple:
	(queue_bin_N, queue_bin_S, queue_bin_E, queue_bin_W, active_action, green_time_bin)
	"""

	def __init__(
		self,
		config: SumoEnvConfig | None = None,
		inbound_lanes: dict[str, list[str]] | None = None,
		seed: int | None = None,
	) -> None:
		self.config = config or SumoEnvConfig()
		self.inbound_lanes = inbound_lanes or DEFAULT_INBOUND_LANES
		self.seed = seed
		self.action_to_phase = dict(ACTION_TO_PHASE)
		self.green_to_yellow = dict(GREEN_TO_YELLOW)
		self.phase_to_action = {phase: action for action, phase in self.action_to_phase.items()}
		self._default_action = min(self.action_to_phase)

		self._label = f"sumo-rl-{id(self)}"
		self._episode_steps = 0
		self._active_action = self._default_action
		self._current_green_phase = self.action_to_phase[self._default_action]
		self._time_since_switch = 0
		self._last_queue_total = 0
		self._started = False

	def reset(self) -> tuple[tuple[int, int, int, int, int, int], dict[str, Any]]:
		"""Start a fresh SUMO episode and return initial state."""
		if not self._started:
			self._connect_remote()

		self._load_simulation()

		self._episode_steps = 0
		self._active_action = self._default_action
		self._current_green_phase = self.action_to_phase[self._default_action]
		self._time_since_switch = 0

		traci.trafficlight.setPhase(self.config.tls_id, self._current_green_phase)

		# One step to populate lane stats after a fresh reset.
		traci.simulationStep()
		self._episode_steps += 1
		self._time_since_switch += 1

		queues = self._get_queue_per_approach()
		self._last_queue_total = sum(queues.values())
		state = self._build_state(queues)
		info = {
			"time": traci.simulation.getTime(),
			"queue_total": self._last_queue_total,
			"active_action": self._active_action,
			"current_green_phase": self._current_green_phase,
		}
		return state, info

	def step(self, action: int) -> tuple[tuple[int, int, int, int, int, int], float, bool, dict[str, Any]]:
		"""Apply action, run simulation window, and return transition tuple.

		Returns:
			next_state, reward, done, info
		"""
		if not self._started:
			raise RuntimeError("Environment not started. Call reset() before step().")
		if action not in self.action_to_phase:
			raise ValueError(f"Unsupported action: {action}. Valid actions: {sorted(self.action_to_phase)}")

		switched = False
		target_green_phase = self.action_to_phase[action]
		requested_switch = target_green_phase != self._current_green_phase
		can_switch = self._time_since_switch >= self.config.min_green_duration

		if requested_switch and can_switch:
			self._switch_phase_with_yellow(target_green_phase)
			switched = True

		for _ in range(self.config.decision_interval):
			if cast(int, traci.simulation.getMinExpectedNumber()) <= 0:
				break
			traci.simulationStep()
			self._episode_steps += 1
			self._time_since_switch += 1

		queues = self._get_queue_per_approach()
		queue_total = sum(queues.values())
		reward = self._compute_reward(queue_total=queue_total, switched=switched)
		self._last_queue_total = queue_total

		done = self._is_done()
		next_state = self._build_state(queues)
		info = {
			"time": traci.simulation.getTime(),
			"queue_total": queue_total,
			"queues": queues,
			"switched": switched,
			"can_switch": can_switch,
			"active_action": self._active_action,
			"current_green_phase": self._current_green_phase,
		}
		return next_state, reward, done, info

	def close(self) -> None:
		"""Close an active SUMO connection for this env."""
		if not self._started:
			return
		try:
			traci.close()
		except traci.TraCIException:
			pass
		finally:
			self._started = False

	def _connect_remote(self) -> None:
		traci.init(port=self.config.remote_port, host=self.config.remote_host)
		self._started = True

	def _load_simulation(self) -> None:
		load_args = ["-c", str(self.config.sumocfg_path)]
		if self.config.sumo_extra_args:
			load_args.extend(self.config.sumo_extra_args)
		if self.seed is not None:
			load_args.extend(["--seed", str(self.seed)])
		traci.load(load_args)

	def _switch_phase_with_yellow(self, target_green_phase: int) -> None:
		current_green_phase = self._current_green_phase
		yellow_phase = self.green_to_yellow[current_green_phase]

		traci.trafficlight.setPhase(self.config.tls_id, yellow_phase)
		for _ in range(self.config.yellow_duration):
			if cast(int, traci.simulation.getMinExpectedNumber()) <= 0:
				break
			traci.simulationStep()
			self._episode_steps += 1

		traci.trafficlight.setPhase(self.config.tls_id, target_green_phase)
		self._current_green_phase = target_green_phase
		self._active_action = self.phase_to_action[target_green_phase]
		self._time_since_switch = 0

	def _get_queue_per_approach(self) -> dict[str, int]:
		return {
			approach: sum(cast(int, traci.lane.getLastStepHaltingNumber(lane)) for lane in lanes)
			for approach, lanes in self.inbound_lanes.items()
		}

	def _bin_value(self, value: int) -> int:
		for idx, threshold in enumerate(self.config.queue_bins):
			if value <= threshold:
				return idx
		return len(self.config.queue_bins)

	def _build_state(self, queues: dict[str, int]) -> tuple[int, int, int, int, int, int]:
		green_time_bin = min(self._time_since_switch // self.config.decision_interval, 12)
		return (
			self._bin_value(queues["N"]),
			self._bin_value(queues["S"]),
			self._bin_value(queues["E"]),
			self._bin_value(queues["W"]),
			self._active_action,
			green_time_bin,
		)

	def _compute_reward(self, queue_total: int, switched: bool) -> float:
		# Base objective: reduce queue accumulation.
		reward = -float(queue_total)

		# Small shaping term for queue improvement from previous step.
		reward += float(self._last_queue_total - queue_total) * 0.1

		if switched:
			reward -= self.config.reward_switch_penalty
		return reward

	def _is_done(self) -> bool:
		if self._episode_steps >= self.config.max_episode_steps:
			return True
		return cast(int, traci.simulation.getMinExpectedNumber()) <= 0
