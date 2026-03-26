import csv
from pathlib import Path
import shutil
import time
from typing import cast
import xml.etree.ElementTree as ET

import traci

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "out"
RESULTS_CSV_PATH = PROJECT_ROOT / "data" / "results.csv"

TRACI_PORT = 8813
TLS_ID = "GS_cluster_300048112_300048176_300048179_32126015"


INBOUND_LANES = {
    "N": ["450749096#0_0", "450749096#0_1", "450749096#0_2", "450749096#0_3"],
    "S": ["1029639687#0_0", "1029639687#0_1", "1029639687#0_2"],
    "E": ["1454977049#0_0", "1454977049#0_1", "1454977049#0_2"],
    "W": ["231737246#0_0", "231737246#0_1", "231737246#0_2"],
}

# metadata
SEED = 105
METHOD = "actuated"
DEMAND = "low"

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


def wait_for_output_files(timeout_seconds=30.0, poll_interval=0.25):
    deadline = time.time() + timeout_seconds
    required_paths = [OUT_DIR / file_name for file_name in OUTPUT_FILES]
    while time.time() < deadline:
        if all(path.exists() for path in required_paths):
            return
        time.sleep(poll_interval)
    missing = [str(path) for path in required_paths if not path.exists()]
    raise FileNotFoundError(f"Missing output files after run: {', '.join(missing)}")


def parse_summary_metrics(summary_path):
    metric_to_value = {}
    with summary_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metric_to_value[row["metric"].strip().lower()] = float(row["value"])
    return metric_to_value


def percentile(values, q):
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


def parse_tripinfo_metrics(tripinfo_path):
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


def build_results_row():
    summary_metrics = parse_summary_metrics(OUT_DIR / "summary.csv")
    tripinfo_metrics = parse_tripinfo_metrics(OUT_DIR / "tripinfo.xml")

    timeseries_path = OUT_DIR / "timeseries.csv"
    with timeseries_path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    duration = max(float(rows[-1]["time"]) - float(rows[0]["time"]), 1.0)
    switching_freq = summary_metrics["total phase switches"] / duration * 3600.0

    return {
        "method": METHOD,
        "demand": DEMAND,
        "seed": SEED,
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


def append_results_row(results_csv_path):
    row = build_results_row()
    needs_header = not results_csv_path.exists() or results_csv_path.stat().st_size == 0
    with results_csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULTS_HEADERS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)


def archive_run_outputs():
    target_dir = OUT_DIR / f"run_{DEMAND}_{SEED}_{METHOD}"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    for file_name in OUTPUT_FILES:
        src = OUT_DIR / file_name
        if not src.exists():
            raise FileNotFoundError(f"Expected output file not found: {src}")
        shutil.move(str(src), str(target_dir / file_name))

def get_queue_per_approach():
    return {
        approach: sum(cast(int, traci.lane.getLastStepHaltingNumber(lane)) for lane in lanes)
        for approach, lanes in INBOUND_LANES.items()
    }


def build_summary_stats(rows):
    queue_totals = [row["queue_total"] for row in rows]
    queue_n = [row["queue_N"] for row in rows]
    queue_s = [row["queue_S"] for row in rows]
    queue_e = [row["queue_E"] for row in rows]
    queue_w = [row["queue_W"] for row in rows]
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
        ["total phase switches", rows[-1]["phase_switches"]]
    ]


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    traci.init(port=TRACI_PORT, host="127.0.0.1")

    rows = []
    last_phase = None
    last_main_phase = None
    main_phase_switches = 0

    try:
        while cast(int, traci.simulation.getMinExpectedNumber()) > 0:
            traci.simulationStep()

            phase = traci.trafficlight.getPhase(TLS_ID)
            
            state = cast(str, traci.trafficlight.getRedYellowGreenState(TLS_ID))

            if phase != last_phase:
                if 'y' not in state.lower():
                    if last_main_phase is not None and phase != last_main_phase:
                        main_phase_switches += 1
                    last_main_phase = phase
            last_phase = phase

            queues = get_queue_per_approach()
            rows.append({
                "time": traci.simulation.getTime(),
                "queue_N": queues["N"],
                "queue_S": queues["S"],
                "queue_E": queues["E"],
                "queue_W": queues["W"],
                "queue_total": sum(queues.values()),
                "phase": phase,
                "phase_switches": main_phase_switches
            })
    finally:
        traci.close()

    if not rows:
        return

    stats = build_summary_stats(rows)
    with (OUT_DIR / "summary.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(stats)

    with (OUT_DIR / "timeseries.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    run()
    wait_for_output_files()
    append_results_row(RESULTS_CSV_PATH)
    archive_run_outputs()