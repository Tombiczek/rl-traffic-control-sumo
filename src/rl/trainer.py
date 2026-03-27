from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import shutil
import time
from typing import Any
import xml.etree.ElementTree as ET
import torch

from dqn_agent import DQNAgent, DQNConfig
from phase_mapping import ACTION_TO_PHASE
from sumo_env import SumoEnvConfig, SumoTrafficEnv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "data" / "out"
RESULTS_CSV_PATH = PROJECT_ROOT / "data" / "results.csv"
MODELS_DIR = PROJECT_ROOT / "data" / "models"

OUTPUT_FILES = ["tripinfo.xml", "statistic.xml", "summary.csv", "timeseries.csv"]
RESULTS_HEADERS = [
	"method",
	"demand",
	"seed",
	"mean_delay",
	"mean_waiting",
	"p95_waiting",
	"max_waiting",
	"mean_queue",
	"max_queue",
	"mean_queue_N",
	"mean_queue_S",
	"mean_queue_E",
	"mean_queue_W",
	"max_queue_N",
	"max_queue_S",
	"max_queue_E",
	"max_queue_W",
	"throughput",
	"switching_freq",
]


@dataclass
class TrainerConfig:
	method: str = "dqn"
	demand: str = "high"
	seed: int = 305
	episodes: int = 100
	model_path: Path = MODELS_DIR / "dqn_tls.pt"
	sumocfg_path: Path = PROJECT_ROOT / "data" / "osm.sumocfg"
	decision_interval: int = 5
	min_green_duration: int = 10
	yellow_duration: int = 3
	max_episode_steps: int = 3600
	reward_switch_penalty: float = 0.2


def wait_for_output_files(timeout_seconds: float = 30.0, poll_interval: float = 0.25) -> None:
	deadline = time.time() + timeout_seconds
	required_paths = [OUT_DIR / file_name for file_name in OUTPUT_FILES]
	while time.time() < deadline:
		if all(path.exists() for path in required_paths):
			return
		time.sleep(poll_interval)
	missing = [str(path) for path in required_paths if not path.exists()]
	raise FileNotFoundError(f"Missing output files after run: {', '.join(missing)}")


def parse_summary_metrics(summary_path: Path) -> dict[str, float]:
	metric_to_value: dict[str, float] = {}
	with summary_path.open(newline="") as file_obj:
		reader = csv.DictReader(file_obj)
		for row in reader:
			metric_to_value[row["metric"].strip().lower()] = float(row["value"])
	return metric_to_value


def percentile(values: list[float], q: float) -> float:
	if not values:
		return 0.0
	sorted_values = sorted(values)
	if len(sorted_values) == 1:
		return float(sorted_values[0])
	position = (len(sorted_values) - 1) * q
	lower_index = int(position)
	upper_index = min(lower_index + 1, len(sorted_values) - 1)
	if lower_index == upper_index:
		return float(sorted_values[lower_index])
	weight = position - lower_index
	return float(sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight)


def parse_tripinfo_metrics(tripinfo_path: Path) -> dict[str, float]:
	tree = ET.parse(tripinfo_path)
	root = tree.getroot()
	tripinfos = root.findall("tripinfo")

	if not tripinfos:
		return {
			"mean_delay": 0.0,
			"mean_waiting": 0.0,
			"p95_waiting": 0.0,
			"max_waiting": 0.0,
			"throughput": 0.0,
		}

	time_losses = [float(elem.attrib.get("timeLoss", 0.0)) for elem in tripinfos]
	waiting_times = [float(elem.attrib.get("waitingTime", 0.0)) for elem in tripinfos]
	depart_times = [float(elem.attrib.get("depart", 0.0)) for elem in tripinfos]
	arrival_times = [float(elem.attrib.get("arrival", 0.0)) for elem in tripinfos]

	sim_span = max(max(arrival_times) - min(depart_times), 1.0)
	throughput_per_hour = len(tripinfos) / sim_span * 3600.0

	return {
		"mean_delay": sum(time_losses) / len(time_losses),
		"mean_waiting": sum(waiting_times) / len(waiting_times),
		"p95_waiting": percentile(waiting_times, 0.95),
		"max_waiting": max(waiting_times),
		"throughput": throughput_per_hour,
	}


def build_results_row(config: TrainerConfig) -> dict[str, Any]:
	summary_metrics = parse_summary_metrics(OUT_DIR / "summary.csv")
	tripinfo_metrics = parse_tripinfo_metrics(OUT_DIR / "tripinfo.xml")

	timeseries_path = OUT_DIR / "timeseries.csv"
	with timeseries_path.open(newline="") as file_obj:
		rows = list(csv.DictReader(file_obj))

	duration = max(float(rows[-1]["time"]) - float(rows[0]["time"]), 1.0)
	switching_freq = summary_metrics["total phase switches"] / duration * 3600.0

	return {
		"method": config.method,
		"demand": config.demand,
		"seed": config.seed,
		"mean_delay": tripinfo_metrics["mean_delay"],
		"mean_waiting": tripinfo_metrics["mean_waiting"],
		"p95_waiting": tripinfo_metrics["p95_waiting"],
		"max_waiting": tripinfo_metrics["max_waiting"],
		"mean_queue": summary_metrics["mean queue length"],
		"max_queue": summary_metrics["max queue length"],
		"mean_queue_N": summary_metrics["mean queue n"],
		"mean_queue_S": summary_metrics["mean queue s"],
		"mean_queue_E": summary_metrics["mean queue e"],
		"mean_queue_W": summary_metrics["mean queue w"],
		"max_queue_N": summary_metrics["max queue n"],
		"max_queue_S": summary_metrics["max queue s"],
		"max_queue_E": summary_metrics["max queue e"],
		"max_queue_W": summary_metrics["max queue w"],
		"throughput": tripinfo_metrics["throughput"],
		"switching_freq": switching_freq,
	}


def append_results_row(config: TrainerConfig, results_csv_path: Path = RESULTS_CSV_PATH) -> None:
	row = build_results_row(config)
	needs_header = not results_csv_path.exists() or results_csv_path.stat().st_size == 0
	with results_csv_path.open("a", newline="") as file_obj:
		writer = csv.DictWriter(file_obj, fieldnames=RESULTS_HEADERS)
		if needs_header:
			writer.writeheader()
		writer.writerow(row)


def archive_run_outputs(config: TrainerConfig) -> None:
	target_dir = OUT_DIR / f"run_{config.demand}_{config.seed}_{config.method}"
	if target_dir.exists():
		shutil.rmtree(target_dir)
	target_dir.mkdir(parents=True, exist_ok=True)

	for file_name in OUTPUT_FILES:
		src = OUT_DIR / file_name
		if not src.exists():
			raise FileNotFoundError(f"Expected output file not found: {src}")
		shutil.move(str(src), str(target_dir / file_name))


def build_summary_stats(rows: list[dict[str, Any]]) -> list[list[float | str]]:
	queue_totals = [float(row["queue_total"]) for row in rows]
	queue_n = [float(row["queue_N"]) for row in rows]
	queue_s = [float(row["queue_S"]) for row in rows]
	queue_e = [float(row["queue_E"]) for row in rows]
	queue_w = [float(row["queue_W"]) for row in rows]
	return [
		["mean queue length", sum(queue_totals) / len(queue_totals)],
		["max queue length", max(queue_totals)],
		["mean queue N", sum(queue_n) / len(queue_n)],
		["mean queue S", sum(queue_s) / len(queue_s)],
		["mean queue E", sum(queue_e) / len(queue_e)],
		["mean queue W", sum(queue_w) / len(queue_w)],
		["max queue N", max(queue_n)],
		["max queue S", max(queue_s)],
		["max queue E", max(queue_e)],
		["max queue W", max(queue_w)],
		["total phase switches", float(rows[-1]["phase_switches"])],
	]


def write_summary_and_timeseries(rows: list[dict[str, Any]]) -> None:
	with (OUT_DIR / "summary.csv").open("w", newline="") as file_obj:
		writer = csv.writer(file_obj)
		writer.writerow(["metric", "value"])
		writer.writerows(build_summary_stats(rows))

	with (OUT_DIR / "timeseries.csv").open("w", newline="") as file_obj:
		writer = csv.DictWriter(file_obj, fieldnames=rows[0].keys())
		writer.writeheader()
		writer.writerows(rows)


class Trainer:
	def __init__(self, config: TrainerConfig) -> None:
		self.config = config
		OUT_DIR.mkdir(parents=True, exist_ok=True)
		MODELS_DIR.mkdir(parents=True, exist_ok=True)

		device = "cuda" if torch.cuda.is_available() else "cpu"
		self.agent = DQNAgent(
			DQNConfig(
				state_dim=6,
				action_dim=len(ACTION_TO_PHASE),
				device=device,
			)
		)

	def _make_env(self, seed: int | None, with_outputs: bool) -> SumoTrafficEnv:
		extra_args: tuple[str, ...] = ()
		if with_outputs:
			extra_args = (
				"--tripinfo-output",
				str(OUT_DIR / "tripinfo.xml"),
				"--statistic-output",
				str(OUT_DIR / "statistic.xml"),
			)

		env_config = SumoEnvConfig(
			sumocfg_path=self.config.sumocfg_path,
			decision_interval=self.config.decision_interval,
			yellow_duration=self.config.yellow_duration,
			min_green_duration=self.config.min_green_duration,
			max_episode_steps=self.config.max_episode_steps,
			reward_switch_penalty=self.config.reward_switch_penalty,
			sumo_extra_args=extra_args,
		)
		return SumoTrafficEnv(config=env_config, seed=seed)

	def train(self) -> None:
		episode_rewards: list[float] = []
		env = self._make_env(seed=self.config.seed, with_outputs=False)

		for episode in range(self.config.episodes):
			env.seed = self.config.seed + episode
			state, _ = env.reset()
			done = False
			total_reward = 0.0

			while not done:
				action = self.agent.choose_action(state, explore=True)
				next_state, reward, done, _ = env.step(action)
				self.agent.update(state, action, reward, next_state, done)
				state = next_state
				total_reward += reward

			self.agent.decay_epsilon()
			episode_rewards.append(total_reward)

			if (episode + 1) % 10 == 0:
				avg_reward = sum(episode_rewards[-10:]) / min(10, len(episode_rewards))
				print(
					f"Episode {episode + 1}/{self.config.episodes} | "
					f"avg_reward_10={avg_reward:.2f} | epsilon={self.agent.epsilon:.4f}"
				)

		env.close()

		self.agent.save(self.config.model_path)
		print(f"Model saved to: {self.config.model_path}")

	def simulate(self) -> None:
		self.agent.load(self.config.model_path)

		env = self._make_env(seed=self.config.seed, with_outputs=True)
		state, _ = env.reset()
		done = False
		rows: list[dict[str, Any]] = []
		phase_switches = 0

		while not done:
			action = self.agent.choose_action(state, explore=False)
			next_state, reward, done, info = env.step(action)
			_ = reward

			if info["switched"]:
				phase_switches += 1

			queues = info["queues"]
			rows.append(
				{
					"time": info["time"],
					"queue_N": queues["N"],
					"queue_S": queues["S"],
					"queue_E": queues["E"],
					"queue_W": queues["W"],
					"queue_total": info["queue_total"],
					"phase": info["current_green_phase"],
					"phase_switches": phase_switches,
				}
			)

			state = next_state

		env.close()

		if not rows:
			raise RuntimeError("No rows collected during simulation.")

		write_summary_and_timeseries(rows)
		wait_for_output_files()
		append_results_row(self.config)
		archive_run_outputs(self.config)
		print("Simulation finished, metrics appended, and outputs archived.")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="DQN trainer/simulator for SUMO traffic signal control")
	parser.add_argument(
		"--mode",
		choices=["train", "simulate", "train_and_simulate"],
		default="train_and_simulate",
		help="Run only training, only simulation, or both in sequence.",
	)
	parser.add_argument("--episodes", type=int, default=100, help="Number of training episodes.")
	parser.add_argument("--seed", type=int, default=305, help="Base random seed.")
	parser.add_argument("--demand", type=str, default="high", help="Demand label for results.csv row.")
	parser.add_argument("--method", type=str, default="dqn", help="Method label for results.csv row.")
	parser.add_argument(
		"--sumocfg",
		type=Path,
		default=PROJECT_ROOT / "data" / "osm.sumocfg",
		help="Path to SUMO configuration file.",
	)
	parser.add_argument(
		"--model-path",
		type=Path,
		default=MODELS_DIR / "dqn_tls.pt",
		help="Path for saving/loading model checkpoint.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	config = TrainerConfig(
		method=args.method,
		demand=args.demand,
		seed=args.seed,
		episodes=args.episodes,
		model_path=args.model_path,
		sumocfg_path=args.sumocfg,
	)
	trainer = Trainer(config)

	if args.mode in ("train", "train_and_simulate"):
		trainer.train()
	if args.mode in ("simulate", "train_and_simulate"):
		trainer.simulate()


if __name__ == "__main__":
	main()
