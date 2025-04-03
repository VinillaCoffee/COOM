from COOM.env.continual import ContinualLearningEnv
from COOM.utils.config import Sequence

cl_env = ContinualLearningEnv(Sequence.CO8)
for env in cl_env.tasks:
    env.reset()
    done = False
    while not done:
        action = env.action_space.sample()
        state, reward, done, truncated, info = env.step(action)
        env.render()
        if done:
            break
    env.close()