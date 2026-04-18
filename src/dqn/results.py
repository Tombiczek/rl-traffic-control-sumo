from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
import shutil
import time
from typing import Any
import xml.etree.ElementTree as ET

from .config import OUTPUT_FILES, RESULTS_HEADERS


def clear_output_files(out_dir: Path) -> None:
    for file_name in OUTPUT_FILES:
        file_path = out_dir / file_name
        if file_path.exists():
            file_path.unlink()


def wait_for_output_files(
    out_dir: Path,
    timeout_seconds: float = 30.0,
    poll_interval: float = 0.25,
    expected_files: list[str] | tuple[str, ...] | None = None,
) -> None:
    deadline = time.time() + timeout_seconds
    required = expected_files or OUTPUT_FILES
    required_paths = [out_dir / file_name for file_name in required]
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


def build_results_row(
    *,
    out_dir: Path,
    method: str,
    demand: str,
    seed: int,
) -> dict[str, Any]:
    summary_metrics = parse_summary_metrics(out_dir / "summary.csv")
    tripinfo_metrics = parse_tripinfo_metrics(out_dir / "tripinfo.xml")

    with (out_dir / "timeseries.csv").open(newline="") as file_obj:
        rows = list(csv.DictReader(file_obj))

    duration = max(float(rows[-1]["time"]) - float(rows[0]["time"]), 1.0)
    switching_freq = summary_metrics["total phase switches"] / duration * 3600.0

    return {
        "method": method,
        "demand": demand,
        "seed": seed,
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


def append_results_row(
    *,
    out_dir: Path,
    results_csv_path: Path,
    method: str,
    demand: str,
    seed: int,
) -> None:
    row = build_results_row(out_dir=out_dir, method=method, demand=demand, seed=seed)
    needs_header = not results_csv_path.exists() or results_csv_path.stat().st_size == 0

    results_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with results_csv_path.open("a", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=RESULTS_HEADERS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)


def append_validation_row(
    *,
    validation_results_csv_path: Path,
    model_name: str,
    mean_delay: float,
    route_file: str,
) -> None:
    needs_header = (
        not validation_results_csv_path.exists()
        or validation_results_csv_path.stat().st_size == 0
    )

    validation_results_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with validation_results_csv_path.open("a", newline="") as file_obj:
        writer = csv.writer(file_obj)
        if needs_header:
            writer.writerow(["model_name", "route_file", "mean_delay"])
        writer.writerow([model_name, route_file, mean_delay])


def archive_run_outputs(*, out_dir: Path, demand: str, seed: int, method: str) -> Path:
    target_dir = out_dir / f"run_{demand}_{seed}_{method}"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    for file_name in OUTPUT_FILES:
        src = out_dir / file_name
        if not src.exists():
            raise FileNotFoundError(f"Expected output file not found: {src}")
        shutil.move(str(src), str(target_dir / file_name))

    return target_dir


def get_queue_per_approach(sumo: Any, inbound_lanes: dict[str, list[str]]) -> dict[str, int]:
    return {
        approach: sum(int(sumo.lane.getLastStepHaltingNumber(lane)) for lane in lanes)
        for approach, lanes in inbound_lanes.items()
    }


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


def write_summary_and_timeseries(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    with (out_dir / "summary.csv").open("w", newline="") as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(["metric", "value"])
        writer.writerows(build_summary_stats(rows))

    with (out_dir / "timeseries.csv").open("w", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


@dataclass
class EpisodeRecorder:
    tls_id: str
    inbound_lanes: dict[str, list[str]]
    rows: list[dict[str, Any]] = field(default_factory=list)
    last_phase: int | None = None
    last_main_phase: int | None = None
    main_phase_switches: int = 0

    def record_step(self, sumo: Any) -> None:
        phase = int(sumo.trafficlight.getPhase(self.tls_id))
        state = str(sumo.trafficlight.getRedYellowGreenState(self.tls_id))

        if phase != self.last_phase:
            if "y" not in state.lower():
                if self.last_main_phase is not None and phase != self.last_main_phase:
                    self.main_phase_switches += 1
                self.last_main_phase = phase
        self.last_phase = phase

        queues = get_queue_per_approach(sumo, self.inbound_lanes)
        self.rows.append(
            {
                "time": float(sumo.simulation.getTime()),
                "queue_N": queues["N"],
                "queue_S": queues["S"],
                "queue_E": queues["E"],
                "queue_W": queues["W"],
                "queue_total": sum(queues.values()),
                "phase": phase,
                "phase_switches": self.main_phase_switches,
            }
        )
