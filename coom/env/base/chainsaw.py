from argparse import Namespace
from collections import deque
from typing import Dict, List

import numpy as np
from scipy import spatial

from coom.env.base.scenario import DoomEnv
from coom.env.utils.utils import distance_traversed
from coom.env.utils.wrappers import WrapperHolder, GameVariableRewardWrapper, MovementRewardWrapper


class Chainsaw(DoomEnv):

    def __init__(self, args: Namespace, env: str, task_id: int, num_tasks=1):
        super().__init__(args, env, task_id, num_tasks)
        self.distance_buffer = []
        self.hits_taken = 0
        self.reward_kill = args.reward_kill
        self.reward_scaler_traversal = args.reward_scaler_traversal

    def store_statistics(self, game_var_buf: deque) -> None:
        distance = distance_traversed(game_var_buf, 2, 3)
        self.distance_buffer.append(distance)

        current_vars = game_var_buf[-1]
        previous_vars = game_var_buf[-2]
        if current_vars[0] < previous_vars[0]:
            self.hits_taken += 1

    def reward_wrappers(self) -> List[WrapperHolder]:
        return [
            WrapperHolder(GameVariableRewardWrapper, self.reward_kill, 1),
            WrapperHolder(MovementRewardWrapper),
        ]

    def get_statistics(self, mode: str = '') -> Dict[str, float]:
        variables = self.game_variable_buffer[-1]
        return {f'{mode}/health': variables[0],
                f'{mode}/kills': variables[1],
                f'{mode}/movement': np.mean(self.distance_buffer).round(3),
                f'{mode}/hits_taken': self.hits_taken}

    def clear_episode_statistics(self) -> None:
        self.hits_taken = 0
        self.distance_buffer.clear()
