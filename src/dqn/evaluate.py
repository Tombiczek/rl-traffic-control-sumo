from __future__ import annotations

import argparse
from pathlib import Path

from stable_baselines3 import DQN

from .config import (
    DEFAULT_MODEL_PATH,
    DEFAULT_OUT_DIR,
    DEFAULT_RESULTS_CSV_PATH,
    DEFAULT_SUMOCFG_PATH,
    DEFAULT_TLS_ID,
    load_inbound_lanes,
    resolve_eval_route_file,
    resolve_net_file,
)
from .env import DqnSumoEnv
from .results import (
    append_results_row,
    archive_run_outputs,
    clear_output_files,
    wait_for_output_files,
    write_summary_and_timeseries,
)


def add_evaluate_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("evaluate", help="Evaluate a trained DQN model on one SUMO route file.")
    parser.set_defaults(handler=run_evaluate)

    parser.add_argument("--sumocfg-file", type=Path, default=DEFAULT_SUMOCFG_PATH)
    parser.add_argument("--net-file", type=Path, default=None)
    parser.add_argument("--route-file", type=Path, default=None)
    parser.add_argument("--lane-map-file", type=Path, default=None)
    parser.add_argument("--tls-id", type=str, default=DEFAULT_TLS_ID)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS_CSV_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--method", type=str, default="dqn")
    parser.add_argument("--demand", type=str, default="high")
    parser.add_argument("--seed", type=int, default=305)
    parser.add_argument("--decision-interval", type=int, default=5)
    parser.add_argument("--yellow-time", type=int, default=3)
    parser.add_argument("--min-green", type=int, default=10)
    parser.add_argument("--num-seconds", type=int, default=20_000)
    parser.add_argument("--reward-fn", type=str, default="diff-waiting-time")
    parser.add_argument("--use-gui", action="store_true")


def run_evaluate(args: argparse.Namespace) -> None:
    net_file = resolve_net_file(args.sumocfg_file, args.net_file)
    route_file = resolve_eval_route_file(args.sumocfg_file, args.route_file)
    inbound_lanes = load_inbound_lanes(args.lane_map_file)
    rows = []

    args.out_dir.mkdir(parents=True, exist_ok=True)
    clear_output_files(args.out_dir)

    env = DqnSumoEnv(
        net_file=net_file,
        route_files=[route_file],
        tls_id=args.tls_id,
        decision_interval=args.decision_interval,
        yellow_time=args.yellow_time,
        min_green=args.min_green,
        num_seconds=args.num_seconds,
        reward_fn=args.reward_fn,
        use_gui=args.use_gui,
        sumo_seed=args.seed,
        output_dir=args.out_dir,
        inbound_lanes=inbound_lanes,
        record_steps=True,
    )

    model = DQN.load(str(args.model_path))
    try:
        observation, _ = env.reset(seed=args.seed)
        done = False

        while not done:
            action, _ = model.predict(observation, deterministic=True)
            observation, _, terminated, truncated, _ = env.step(int(action))
            done = terminated or truncated

        rows = env.pop_recorded_rows()
    finally:
        env.close()

    if not rows:
        raise RuntimeError("No rows collected during evaluation.")

    write_summary_and_timeseries(args.out_dir, rows)
    wait_for_output_files(args.out_dir)

    append_results_row(
        out_dir=args.out_dir,
        results_csv_path=args.results_csv,
        method=args.method,
        demand=args.demand,
        seed=args.seed,
    )
    archive_dir = archive_run_outputs(
        out_dir=args.out_dir,
        demand=args.demand,
        seed=args.seed,
        method=args.method,
    )
    print(f"Evaluation finished. Archived outputs in: {archive_dir}")
