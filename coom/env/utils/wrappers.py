from typing import Dict, Any, Tuple, Callable

import tensorflow as tf

import cv2
import gym
import numpy as np
from gym.spaces import Box
from vizdoom import GameVariable


class WrapperHolder:
    def __init__(self, wrapper_class, *args):
        self.wrapper_class = wrapper_class
        self.args = args


class ConstantRewardWrapper(gym.RewardWrapper):
    def __init__(self, env, reward: float, penalty: bool = False):
        super(ConstantRewardWrapper, self).__init__(env)
        self.rew = reward
        self.penalty = penalty

    def reward(self, reward):
        delta = -self.rew if self.penalty else self.rew
        reward += delta
        return reward


class MovementRewardWrapper(gym.RewardWrapper):
    def __init__(self, env):
        super(MovementRewardWrapper, self).__init__(env)
        self.reward_scaler = env.reward_scaler_traversal

    def reward(self, reward):
        if len(self.distance_buffer) < 2:
            return reward
        distance = self.distance_buffer[-1]
        reward += distance * self.reward_scaler_traversal  # Increase the reward for movement linearly
        return reward


class GameVariableRewardWrapper(gym.RewardWrapper):
    def __init__(self, env, reward: float, var_index: int = 0, decrease: bool = False, penalty: bool = False):
        super(GameVariableRewardWrapper, self).__init__(env)
        self.rew = reward
        self.var_index = var_index
        self.decrease = decrease
        self.penalty = penalty

    def reward(self, reward):
        if len(self.game_variable_buffer) < 2:
            return reward
        vars_cur = self.game_variable_buffer[-1]
        vars_prev = self.game_variable_buffer[-2]

        var_cur = vars_cur[self.var_index]
        var_prev = vars_prev[self.var_index]

        if not self.decrease and var_cur > var_prev or self.decrease and var_cur < var_prev:
            delta = -self.rew if self.penalty else self.rew
            reward += delta
        return reward


class UserVariableRewardWrapper(gym.RewardWrapper):
    def __init__(self, env, reward: float, game_var: GameVariable, decrease: bool = False, penalty: bool = False,
                 update_callback: Callable = None):
        super(UserVariableRewardWrapper, self).__init__(env)
        self.rew = reward
        self.game_var = game_var
        self.decrease = decrease
        self.penalty = penalty
        self.update_callback = update_callback

    def reward(self, reward):
        var_cur = self.game.get_game_variable(self.game_var)
        var_prev = self.get_and_update_user_var(self.game_var)

        if not self.decrease and var_cur > var_prev or self.decrease and var_cur < var_prev:
            delta = -self.rew if self.penalty else self.rew
            reward += delta
        return reward


class RescaleWrapper(gym.Wrapper):
    """Rescale the observation space to [-1, 1]."""

    def __init__(self, env):
        gym.Wrapper.__init__(self, env)

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        state, info = self.env.reset()
        return state / 255. * 2 - 1, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        state, reward, done, truncated, info = self.env.step(action)
        return state / 255. * 2 - 1, reward, done, truncated, info


class NormalizeWrapper(gym.Wrapper):
    """Normalize the observation space."""

    def __init__(self, env, eps=1e-6):
        gym.Wrapper.__init__(self, env)
        self.eps = eps

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        state, info = self.env.reset()
        mean = self.states.mean()
        std = self.states.std() + self.eps
        state = (state - mean) / std
        return state / 255. * 2 - 1, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        state, reward, done, truncated, info = self.env.step(action)
        mean = self.states.mean()
        std = self.states.std() + self.eps
        state = (state - mean) / std
        return state, reward, done, truncated, info


class ResizeWrapper(gym.Wrapper):
    """Resize the observation space."""

    def __init__(self, env, height=84, width=84):
        gym.Wrapper.__init__(self, env)
        self.shape = (height, width)

        obs_shape = self.shape + self.observation_space.shape[2:]
        self.observation_space = Box(low=0, high=255, shape=obs_shape, dtype=np.uint8)

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        state, info = self.env.reset()
        return cv2.resize(state, self.shape), info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        state, reward, done, truncated, info = self.env.step(action)
        return cv2.resize(state, self.shape), reward, done, truncated, info


class RGBStack(gym.Wrapper):
    """Combine the stacked frames with RGB colours. [n_stack, h, w, 3] -> [h, w, n_stack * 3]"""

    def __init__(self, env):
        super(RGBStack, self).__init__(env)
        obs_shape = self.observation_space.shape
        self.observation_space = Box(
            low=0, high=255, shape=(obs_shape[1], obs_shape[2], obs_shape[0] * obs_shape[3]), dtype=np.uint8
        )

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        state, info = self.env.reset()
        state = combine_frames(state)
        return state, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        state, reward, done, truncated, info = self.env.step(action)
        state = combine_frames(state)
        return state, reward, done, truncated, info


def combine_frames(obs):
    return tf.reshape(obs, [obs.shape[1], obs.shape[2], obs.shape[0] * obs.shape[3]])
