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
    load_inbound_lanes,
    load_train_config,
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
    parser.add_argument(
        "--config-file",
        type=Path,
        required=True,
        help="YAML file with training hyperparameters and environment configuration.",
    )
    parser.add_argument("--lane-map-file", type=Path, default=None)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--upload-to-hub", action="store_true")


def run_train(args: argparse.Namespace) -> None:
    net_file = resolve_net_file(args.sumocfg_file, args.net_file)
    route_files = collect_route_files(args.train_route_glob)
    inbound_lanes = load_inbound_lanes(args.lane_map_file)
    config = load_train_config(args.config_file)
    env_config = config["environment"]
    training_config = config["training"]
    hub_config = config["hub"]

    env = DqnSumoEnv(
        net_file=net_file,
        route_files=route_files,
        tls_id=str(env_config["tls_id"]),
        decision_interval=int(env_config["decision_interval"]),
        yellow_time=int(env_config["yellow_time"]),
        min_green=int(env_config["min_green"]),
        num_seconds=int(env_config["num_seconds"]),
        reward_fn=str(env_config["reward_fn"]),
        use_gui=bool(env_config["use_gui"]),
        sumo_seed=int(training_config["seed"]),
        inbound_lanes=inbound_lanes,
        record_steps=False,
    )

    model = DQN(
        policy="MlpPolicy",
        env=env,
        learning_rate=float(training_config["learning_rate"]),
        buffer_size=int(training_config["buffer_size"]),
        learning_starts=int(training_config["learning_starts"]),
        batch_size=int(training_config["batch_size"]),
        gamma=float(training_config["gamma"]),
        train_freq=int(training_config["train_freq"]),
        target_update_interval=int(training_config["target_update_interval"]),
        exploration_fraction=float(training_config["exploration_fraction"]),
        exploration_initial_eps=float(training_config["exploration_initial_eps"]),
        exploration_final_eps=float(training_config["exploration_final_eps"]),
        verbose=1,
        seed=int(training_config["seed"]),
        device=str(training_config["device"]),
    )

    try:
        model.learn(total_timesteps=int(training_config["total_timesteps"]))
        args.model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(args.model_path))
        print(f"Model saved to: {args.model_path}")

        if args.upload_to_hub or bool(hub_config["upload_to_hub"]):
            upload_model_to_hub(
                model_path=args.model_path,
                model_name=str(hub_config["model_name"]),
            )
    finally:
        env.close()


def collect_route_files(patterns: list[str]) -> list[Path]:
    route_files = sorted({Path(path).resolve() for pattern in patterns for path in glob(pattern, recursive=True)})
    if not route_files:
        raise FileNotFoundError("No training route files matched the provided --train-route-glob patterns.")
    return route_files


def upload_model_to_hub(*, model_path: Path, model_name: str) -> None:
    token = os.environ["HF_TOKEN"]
    repo_id = os.environ["HF_REPO_ID"]
    suffix = model_path.suffix or ".zip"
    path_in_repo = model_name if Path(model_name).suffix else f"{model_name}{suffix}"

    api = HfApi(token=token)
    repo_url = api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
    resolved_repo_id = repo_url.repo_id
    api.upload_file(
        path_or_fileobj=str(model_path),
        path_in_repo=path_in_repo,
        repo_id=resolved_repo_id,
        token=token,
        repo_type="model",
    )
    print(f"Uploaded model to Hugging Face Hub: {resolved_repo_id}/{path_in_repo}")
