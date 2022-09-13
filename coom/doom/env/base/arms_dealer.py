from argparse import Namespace
from typing import List

from vizdoom import GameVariable

from coom.doom.env.base.scenario import DoomEnv


class ArmsDealer(DoomEnv):

    def __init__(self, args: Namespace, task: str, task_id: int, num_tasks: int = 1, reward_delivery: float = 1.0,
                 penalty_frame_passed: float = 0.01):
        self.penalty_frame_passed = penalty_frame_passed
        self.reward_delivery = reward_delivery
        self.arms_dealt = 0
        super().__init__(args, task, task_id, num_tasks)

    def get_available_actions(self) -> List[List[float]]:
        actions = []
        m_forward = [[0.0], [1.0]]
        t_left_right = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0]]
        for m in m_forward:
            for t in t_left_right:
                actions.append(t + m)
        return actions

    def calc_reward(self) -> float:
        reward = -self.penalty_frame_passed
        arms_dealt = self.game.get_game_variable(GameVariable.USER2)
        if arms_dealt > self.arms_dealt:
            reward = self.reward_delivery
            self.arms_dealt = arms_dealt

        return reward
