from collections import deque

from argparse import Namespace
from typing import Dict, List
from vizdoom import DEAD

from coom.env.scenario.scenario import DoomEnv
from coom.env.wrappers.reward import WrapperHolder, ProportionalVariableRewardWrapper, BooleanVariableRewardWrapper, \
    GoalRewardWrapper


class Pitfall(DoomEnv):
    """
    In this scenario, the agent is located in a very long rectangular corridor. The surface of the area is divided into
    squares, which there are 7 of in each row. At the beginning of an episode, each of those sections have a 30% chance
    of being turned into a pit by lowering the height of the floor in the given area. The floor layout is randomized
    every episode, so there is no one optimal route to take. Falling into a pit instantly terminates the episode and
    should be avoided at all cost. Reaching the other end of the corridor also terminates the episode. The agent is
    tasked to traverse along the corridor as far as possible and potentially reach the other end. Note that there is a
    ~10^-5 chance that a section of the corridor becomes untraversable due to the stochastic nature of the layout. The
    agent ought to identify a safe path through the corridor and speedily navigate forwards. The agent can turn left and
    right, move forward, and accelerate. In the sparse reward case, the agent only acquires a reward for having reached
    the other end of the corridor. With dense rewards, the agent is proportionally rewarded for how much it has
    travelled forward in the corridor, and penalized for falling into a pit.
    """

    def __init__(self, args: Namespace, env: str, task_id: int, num_tasks: int = 1):
        super().__init__(args, env, task_id, num_tasks)
        self.reward_goal = args.reward_platform_reached
        self.reward_scaler = args.reward_scaler_pitfall
        self.penalty_death = args.penalty_death
        self.frames = 0
        self.total_dist = 0
        self.current_dist = 0
        self.distance_buffer = []

    def store_statistics(self, game_var_buf: deque) -> None:
        self.frames += 1
        self.current_dist = game_var_buf[-1][0]
        self.total_dist += self.current_dist
        self.distance_buffer.append(self.current_dist)

    def get_success(self) -> float:
        return self.total_dist

    def reward_wrappers_dense(self) -> List[WrapperHolder]:
        return [WrapperHolder(ProportionalVariableRewardWrapper, scaler=self.reward_scaler, var_index=0, keep_lb=True),
                WrapperHolder(BooleanVariableRewardWrapper, reward=self.penalty_death, game_var=DEAD)]

    def reward_wrappers_sparse(self) -> List[WrapperHolder]:
        return [WrapperHolder(GoalRewardWrapper, reward=self.reward_goal, goal=self.performance_upper_bound)]

    @property
    def performance_upper_bound(self) -> float:
        return 150000

    @property
    def performance_lower_bound(self) -> float:
        return 20000

    def extra_statistics(self, mode: str = '') -> Dict[str, float]:
        return {f'{mode}/distance': self.get_success(), f'{mode}/movement': self.get_success() / max(self.frames, 1)}

    def clear_episode_statistics(self) -> None:
        super().clear_episode_statistics()
        self.distance_buffer.clear()
        self.total_dist = 0
