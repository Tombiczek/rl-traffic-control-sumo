from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import random
from typing import Deque
import torch
from torch import nn


@dataclass
class DQNConfig:
	state_dim: int
	action_dim: int
	hidden_dim: int = 128
	learning_rate: float = 1e-3
	gamma: float = 0.99
	batch_size: int = 64
	replay_capacity: int = 50_000
	target_sync_steps: int = 1_000
	epsilon_start: float = 1.0
	epsilon_min: float = 0.05
	epsilon_decay: float = 0.995
	device: str = "cpu"


class QNetwork(nn.Module):
	def __init__(self, state_dim: int, action_dim: int, hidden_dim: int) -> None:
		super().__init__()
		self.net = nn.Sequential(
			nn.Linear(state_dim, hidden_dim),
			nn.ReLU(),
			nn.Linear(hidden_dim, hidden_dim),
			nn.ReLU(),
			nn.Linear(hidden_dim, action_dim),
		)

	def forward(self, x):
		return self.net(x)


class ReplayBuffer:
	def __init__(self, capacity: int) -> None:
		self._buffer: Deque[tuple[tuple[int, ...], int, float, tuple[int, ...], bool]] = deque(
			maxlen=capacity
		)

	def push(
		self,
		state: tuple[int, ...],
		action: int,
		reward: float,
		next_state: tuple[int, ...],
		done: bool,
	) -> None:
		self._buffer.append((state, action, reward, next_state, done))

	def sample(self, batch_size: int) -> list[tuple[tuple[int, ...], int, float, tuple[int, ...], bool]]:
		return random.sample(self._buffer, batch_size)

	def __len__(self) -> int:
		return len(self._buffer)


class DQNAgent:
	"""Deep Q-Learning agent with replay buffer and target network."""

	def __init__(self, config: DQNConfig) -> None:
		self.config = config
		self.device = torch.device(config.device)

		self.policy_net = QNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
		self.target_net = QNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
		self.target_net.load_state_dict(self.policy_net.state_dict())
		self.target_net.eval()

		self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=config.learning_rate)
		self.loss_fn = nn.MSELoss()
		self.replay = ReplayBuffer(config.replay_capacity)

		self.epsilon = config.epsilon_start
		self.training_steps = 0

	def choose_action(self, state: tuple[int, ...], explore: bool = True) -> int:
		if explore and random.random() < self.epsilon:
			return random.randrange(self.config.action_dim)

		state_tensor = self._state_to_tensor(state).unsqueeze(0)
		with torch.no_grad():
			q_values = self.policy_net(state_tensor)
			return int(torch.argmax(q_values, dim=1).item())

	def update(
		self,
		state: tuple[int, ...],
		action: int,
		reward: float,
		next_state: tuple[int, ...],
		done: bool = False,
	) -> dict[str, float] | None:
		self.replay.push(state, action, reward, next_state, done)

		if len(self.replay) < self.config.batch_size:
			return None

		batch = self.replay.sample(self.config.batch_size)
		states, actions, rewards, next_states, dones = zip(*batch)

		states_tensor = torch.stack([self._state_to_tensor(s) for s in states])
		actions_tensor = torch.tensor(actions, dtype=torch.long, device=self.device).unsqueeze(1)
		rewards_tensor = torch.tensor(rewards, dtype=torch.float32, device=self.device)
		next_states_tensor = torch.stack([self._state_to_tensor(s) for s in next_states])
		dones_tensor = torch.tensor(dones, dtype=torch.float32, device=self.device)

		q_values = self.policy_net(states_tensor).gather(1, actions_tensor).squeeze(1)
		with torch.no_grad():
			next_q_values = self.target_net(next_states_tensor).max(1).values
			targets = rewards_tensor + (1.0 - dones_tensor) * self.config.gamma * next_q_values

		loss = self.loss_fn(q_values, targets)

		self.optimizer.zero_grad()
		loss.backward()
		self.optimizer.step()

		self.training_steps += 1
		if self.training_steps % self.config.target_sync_steps == 0:
			self.target_net.load_state_dict(self.policy_net.state_dict())

		return {"loss": float(loss.item())}

	def decay_epsilon(self) -> float:
		self.epsilon = max(self.config.epsilon_min, self.epsilon * self.config.epsilon_decay)
		return self.epsilon

	def set_learning_rate(self, learning_rate: float) -> None:
		for param_group in self.optimizer.param_groups:
			param_group["lr"] = learning_rate
		self.config.learning_rate = learning_rate

	def save(self, path: str | Path) -> None:
		path_obj = Path(path)
		path_obj.parent.mkdir(parents=True, exist_ok=True)
		payload = {
			"config": self.config.__dict__,
			"policy_state_dict": self.policy_net.state_dict(),
			"target_state_dict": self.target_net.state_dict(),
			"optimizer_state_dict": self.optimizer.state_dict(),
			"epsilon": self.epsilon,
			"training_steps": self.training_steps,
		}
		torch.save(payload, path_obj)

	def load(self, path: str | Path) -> None:
		payload = torch.load(Path(path), map_location=self.device)
		self.policy_net.load_state_dict(payload["policy_state_dict"])
		self.target_net.load_state_dict(payload["target_state_dict"])
		self.optimizer.load_state_dict(payload["optimizer_state_dict"])
		self.epsilon = float(payload.get("epsilon", self.config.epsilon_start))
		self.training_steps = int(payload.get("training_steps", 0))

	def _state_to_tensor(self, state: tuple[int, ...]):
		return torch.tensor(state, dtype=torch.float32, device=self.device)
