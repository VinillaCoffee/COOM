import tensorflow as tf
from argparse import Namespace
from datetime import datetime
from pathlib import Path

from cl.sac.replay_buffers import BufferType
from coom.envs import get_single_env
from cl.sac.sac import SAC
from cl.utils.logx import EpochLogger
from coom.utils.enums import DoomScenario
from cl.utils.run_utils import get_activation_from_str
from cl.utils.wandb_utils import init_wandb
from input_args import parse_args


def main(args: Namespace):
    policy_kwargs = dict(
        hidden_sizes=args.hidden_sizes,
        activation=get_activation_from_str(args.activation),
        use_layer_norm=args.use_layer_norm,
    )

    if args.gpu:
        # Restrict TensorFlow to only use the specified GPU
        tf.config.experimental.set_visible_devices(args.gpu, 'GPU')
        print("Using GPU: ", args.gpu)

    args.experiment_dir = Path(__file__).parent.resolve()
    args.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Logging
    init_wandb(args, args.scenarios)
    logger = EpochLogger(args.logger_output, config=vars(args), group_id=args.group_id)

    # Task
    one_hot_idx = 0  # one-hot identifier (indicates order among different tasks that we consider)
    one_hot_len = 1  # number of tasks, i.e., length of the one-hot encoding, number of tasks that we consider

    # Environment
    scenario_class = DoomScenario[args.scenarios[0].upper()].value
    env = get_single_env(args, scenario_class, args.envs[0], one_hot_idx, one_hot_len)
    test_envs = [get_single_env(args, scenario_class, task, one_hot_idx, one_hot_len) for task in args.test_envs]
    if not test_envs and args.test_only:
        test_envs = [env]

    sac = SAC(
        env,
        test_envs,
        logger,
        scenarios=args.scenarios,
        seed=args.seed,
        steps_per_env=args.steps_per_env,
        start_steps=args.start_steps,
        log_every=args.log_every,
        update_after=args.update_after,
        update_every=args.update_every,
        n_updates=args.n_updates,
        replay_size=args.replay_size,
        batch_size=args.batch_size,
        policy_kwargs=policy_kwargs,
        lr=args.lr,
        lr_decay=args.lr_decay,
        lr_decay_rate=args.lr_decay_rate,
        lr_decay_steps=args.lr_decay_steps,
        alpha=args.alpha,
        gamma=args.gamma,
        target_output_std=args.target_output_std,
        render=args.render,
        render_sleep=args.render_sleep,
        save_freq_epochs=args.save_freq_epochs,
        experiment_dir=args.experiment_dir,
        model_path=args.model_path,
        timestamp=args.timestamp,
        test_only=args.test_only,
        num_test_eps_stochastic=args.test_episodes,
        buffer_type=BufferType(args.buffer_type),
    )
    sac.run()


if __name__ == "__main__":
    main(parse_args())
