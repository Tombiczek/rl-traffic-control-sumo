import csv
from pathlib import Path
from typing import cast
import xml.etree.ElementTree as ET

import traci

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "out"

TRACI_PORT = 8813
TLS_ID = "GS_cluster_300048112_300048176_300048179_32126015"

INBOUND_LANES = {
    "N": ["450749096#0_0", "450749096#0_1", "450749096#0_2", "450749096#0_3"],
    "S": ["1029639687#0_0", "1029639687#0_1", "1029639687#0_2"],
    "E": ["1454977049#0_0", "1454977049#0_1", "1454977049#0_2"],
    "W": ["231737246#0_0", "231737246#0_1", "231737246#0_2"],
}


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

    sim_duration = rows[-1]["time"] - rows[0]["time"] if len(rows) > 1 else rows[-1]["time"]
    switch_count = rows[-1]["switch_count"]
    switching_frequency = (switch_count / sim_duration * 3600) if sim_duration > 0 else 0

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
        ["switching frequency", switching_frequency],
    ]


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    traci.init(port=TRACI_PORT, host="127.0.0.1")

    rows = []
    prev_phase = None
    switch_count = 0

    try:
        while cast(int, traci.simulation.getMinExpectedNumber()) > 0:
            traci.simulationStep()

            phase = traci.trafficlight.getPhase(TLS_ID)
            if prev_phase is not None and phase != prev_phase:
                switch_count += 1
            prev_phase = phase

            queues = get_queue_per_approach()

            rows.append({
                "time": traci.simulation.getTime(),
                "phase": phase,
                "queue_N": queues["N"],
                "queue_S": queues["S"],
                "queue_E": queues["E"],
                "queue_W": queues["W"],
                "queue_total": sum(queues.values()),
                "switch_count": switch_count,
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