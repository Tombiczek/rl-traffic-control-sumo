from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUMOCFG_PATH = PROJECT_ROOT / "data" / "osm.sumocfg"
DEFAULT_RESULTS_CSV_PATH = PROJECT_ROOT / "data" / "results.csv"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "out"
DEFAULT_MODELS_DIR = PROJECT_ROOT / "data" / "models" / "dqn"
DEFAULT_MODEL_PATH = DEFAULT_MODELS_DIR / "dqn_model.zip"

DEFAULT_TLS_ID = "GS_cluster_300048112_300048176_300048179_32126015"

# The baseline result format assumes four named approaches.
# This mapping matches the current thesis scenario and can be overridden
# with --lane-map-file when a different mounted network is used.
DEFAULT_INBOUND_LANES = {
    "N": ["450749096#0_0", "450749096#0_1", "450749096#0_2", "450749096#0_3"],
    "S": ["1029639687#0_0", "1029639687#0_1", "1029639687#0_2"],
    "E": ["1454977049#0_0", "1454977049#0_1", "1454977049#0_2"],
    "W": ["231737246#0_0", "231737246#0_1", "231737246#0_2"],
}

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


def default_inbound_lanes() -> dict[str, list[str]]:
    return {approach: list(lanes) for approach, lanes in DEFAULT_INBOUND_LANES.items()}


def load_inbound_lanes(lane_map_file: Path | None) -> dict[str, list[str]]:
    if lane_map_file is None:
        return default_inbound_lanes()

    with lane_map_file.open() as file_obj:
        raw_data: dict[str, Any] = json.load(file_obj)

    return {approach: [str(lane) for lane in raw_data[approach]] for approach in ["N", "S", "E", "W"]}


def _read_sumocfg_value(sumocfg_file: Path, tag_name: str) -> str | None:
    tree = ET.parse(sumocfg_file)
    root = tree.getroot()
    input_section = root.find("input")
    if input_section is None:
        return None

    tag = input_section.find(tag_name)
    if tag is None:
        return None

    value = tag.attrib.get("value")
    if value is None or not value.strip():
        return None

    return value.strip()


def resolve_net_file(sumocfg_file: Path | None, net_file: Path | None) -> Path:
    if net_file is not None:
        return net_file.resolve()
    if sumocfg_file is None:
        raise ValueError("Provide --net-file or --sumocfg-file.")

    net_value = _read_sumocfg_value(sumocfg_file, "net-file")
    if net_value is None:
        raise ValueError(f"Could not resolve <net-file> from {sumocfg_file}.")

    return (sumocfg_file.parent / net_value).resolve()


def resolve_eval_route_file(sumocfg_file: Path | None, route_file: Path | None) -> Path:
    if route_file is not None:
        return route_file.resolve()
    if sumocfg_file is None:
        raise ValueError("Provide --route-file or --sumocfg-file.")

    route_value = _read_sumocfg_value(sumocfg_file, "route-files")
    if route_value is None:
        raise ValueError(f"Could not resolve <route-files> from {sumocfg_file}.")

    # SUMO accepts comma-separated route files. Baseline rows are created per scenario,
    # so evaluation uses the first configured route file unless the caller overrides it.
    first_route = route_value.split(",")[0].strip()
    return (sumocfg_file.parent / first_route).resolve()


def load_train_config(config_file: Path) -> dict[str, Any]:
    with config_file.open() as file_obj:
        return yaml.safe_load(file_obj)
