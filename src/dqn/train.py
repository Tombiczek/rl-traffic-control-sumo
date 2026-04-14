from __future__ import annotations

import argparse
from glob import glob
import os
from pathlib import Path

from huggingface_hub import HfApi
from stable_baselines3 import DQN

from .config import (
    DEFAULT_MODEL_PATH,
    DEFAULT_SUMOCFG_PATH,
    DEFAULT_TLS_ID,
    load_inbound_lanes,
    resolve_net_file,
)
from .env import DqnSumoEnv


def add_train_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("train", help="Train a DQN traffic-signal controller.")
    parser.set_defaults(handler=run_train)

    parser.add_argument("--sumocfg-file", type=Path, default=DEFAULT_SUMOCFG_PATH)
    parser.add_argument("--net-file", type=Path, default=None)
    parser.add_argument(
        "--train-route-glob",
        nargs="+",
        required=True,
        help="One or more glob patterns pointing to training *.rou.xml files.",
    )
    parser.add_argument("--lane-map-file", type=Path, default=None)
    parser.add_argument("--tls-id", type=str, default=DEFAULT_TLS_ID)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--total-timesteps", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--decision-interval", type=int, default=5)
    parser.add_argument("--yellow-time", type=int, default=3)
    parser.add_argument("--min-green", type=int, default=10)
    parser.add_argument("--num-seconds", type=int, default=20_000)
    parser.add_argument("--reward-fn", type=str, default="diff-waiting-time")
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--buffer-size", type=int, default=50_000)
    parser.add_argument("--learning-starts", type=int, default=1_000)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--train-freq", type=int, default=1)
    parser.add_argument("--target-update-interval", type=int, default=500)
    parser.add_argument("--exploration-fraction", type=float, default=0.2)
    parser.add_argument("--exploration-initial-eps", type=float, default=1.0)
    parser.add_argument("--exploration-final-eps", type=float, default=0.05)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--use-gui", action="store_true")
    parser.add_argument("--upload-to-hub", action="store_true")


def run_train(args: argparse.Namespace) -> None:
    net_file = resolve_net_file(args.sumocfg_file, args.net_file)
    route_files = collect_route_files(args.train_route_glob)
    inbound_lanes = load_inbound_lanes(args.lane_map_file)

    env = DqnSumoEnv(
        net_file=net_file,
        route_files=route_files,
        tls_id=args.tls_id,
        decision_interval=args.decision_interval,
        yellow_time=args.yellow_time,
        min_green=args.min_green,
        num_seconds=args.num_seconds,
        reward_fn=args.reward_fn,
        use_gui=args.use_gui,
        sumo_seed=args.seed,
        inbound_lanes=inbound_lanes,
        record_steps=False,
    )

    model = DQN(
        policy="MlpPolicy",
        env=env,
        learning_rate=args.learning_rate,
        buffer_size=args.buffer_size,
        learning_starts=args.learning_starts,
        batch_size=args.batch_size,
        gamma=args.gamma,
        train_freq=args.train_freq,
        target_update_interval=args.target_update_interval,
        exploration_fraction=args.exploration_fraction,
        exploration_initial_eps=args.exploration_initial_eps,
        exploration_final_eps=args.exploration_final_eps,
        verbose=1,
        seed=args.seed,
        device=args.device,
    )

    try:
        model.learn(total_timesteps=args.total_timesteps)
        args.model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(args.model_path))
        print(f"Model saved to: {args.model_path}")

        if args.upload_to_hub:
            upload_model_to_hub(args.model_path)
    finally:
        env.close()


def collect_route_files(patterns: list[str]) -> list[Path]:
    route_files = sorted({Path(path).resolve() for pattern in patterns for path in glob(pattern, recursive=True)})
    if not route_files:
        raise FileNotFoundError("No training route files matched the provided --train-route-glob patterns.")
    return route_files


def upload_model_to_hub(model_path: Path) -> None:
    token = os.environ["HF_TOKEN"]
    repo_id = os.environ["HF_REPO_ID"]
    path_in_repo = os.environ.get("HF_PATH_IN_REPO", model_path.name)

    api = HfApi(token=token)
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
    api.upload_file(
        path_or_fileobj=str(model_path),
        path_in_repo=path_in_repo,
        repo_id=repo_id,
        repo_type="model",
    )
    print(f"Uploaded model to Hugging Face Hub: {repo_id}/{path_in_repo}")
