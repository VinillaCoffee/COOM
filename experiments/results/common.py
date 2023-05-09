import argparse
import numpy as np
from scipy.ndimage import gaussian_filter1d
from typing import List

from experiments.results.plot_actions_by_method import TRANSLATIONS

TRANSLATIONS = {
    'sac': 'SAC',
    'packnet': 'PackNet',
    'mas': 'MAS',
    'agem': 'AGEM',
    'l2': 'L2',
    'vcl': 'VCL',
    'fine_tuning': 'Fine-tuning',
    'perfect_memory': 'Perfect Memory',

    'pitfall': 'Pitfall',
    'arms_dealer': 'Arms Dealer',
    'hide_and_seek': 'Hide and Seek',
    'floor_is_lava': 'Floor is Lava',
    'chainsaw': 'Chainsaw',
    'raise_the_roof': 'Raise the Roof',
    'run_and_gun': 'Run and Gun',
    'health_gathering': 'Health Gathering',

    'obstacles': 'Obstacles',
    'green': 'Green',
    'resized': 'Resized',
    'invulnerable': 'Monsters',
    'default': 'Default',
    'red': 'Red',
    'blue': 'Blue',
    'shadows': 'Shadows',

    'success': 'Success',
    'kills': 'Kill Count',
    'ep_length': 'Frames Alive',
    'arms_dealt': 'Weapons Delivered',
    'distance': 'Distance',

    'single': 'Single',
    'CD4': 'CD4',
    'CD8': 'CD8',
    'CO4': 'CO4',
    'CO8': 'CO8',
    'COC': 'COC',
}

SEQUENCES = {
    'CD4': ['default', 'red', 'blue', 'shadows'],
    'CD8': ['obstacles', 'green', 'resized', 'invulnerable', 'default', 'red', 'blue', 'shadows'],
    'CO4': ['chainsaw', 'raise_the_roof', 'run_and_gun', 'health_gathering'],
    'CO8': ['pitfall', 'arms_dealer', 'hide_and_seek', 'floor_is_lava', 'chainsaw', 'raise_the_roof', 'run_and_gun',
            'health_gathering'],
    'COC': ['pitfall', 'arms_dealer', 'hide_and_seek', 'floor_is_lava', 'chainsaw', 'raise_the_roof', 'run_and_gun',
            'health_gathering'],
}

COLORS = {
    'CD4': ['#55A868', '#C44E52', '#4C72B0', '#8172B2'],
    'CO4': ['#4C72B0', '#55A868', '#C44E52', '#8172B2'],
    'CD8': ['#64B5CD', '#55A868', '#777777', '#8172B2', '#CCB974', '#C44E52', '#4C72B0', '#917113'],
    'CO8': ['#4C72B0', '#55A868', '#C44E52', '#8172B2', '#CCB974', '#64B5CD', '#777777', '#917113'],
    'COC': ['#4C72B0', '#55A868', '#C44E52', '#8172B2', '#CCB974', '#64B5CD', '#777777', '#917113']
}

PLOT_COLORS = ['#4C72B0', '#55A868', '#C44E52', '#8172B2', '#CCB974', '#64B5CD', '#777777', '#917113']

METRICS = {
    'pitfall': 'distance',
    'arms_dealer': 'arms_dealt',
    'hide_and_seek': 'ep_length',
    'floor_is_lava': 'ep_length',
    'chainsaw': 'kills',
    'raise_the_roof': 'ep_length',
    'run_and_gun': 'kills',
    'health_gathering': 'ep_length',
    'default': 'kills',
}

ENVS = {
    'CO4': 'default',
    'CO8': 'default',
    'COC': 'hard',
}

SEPARATE_STORAGE_TAGS = ['REG_CRITIC', 'NO_REG_CRITIC', 'SINGLE_HEAD']
FORBIDDEN_TAGS = ['SINGLE_HEAD', 'REG_CRITIC', 'NO_REG_CRITIC', 'SPARSE', 'TEST']

METHODS = ['packnet', 'mas', 'agem', 'l2', 'vcl', 'fine_tuning', 'perfect_memory']
KERNEL_SIGMA = 3
INTERVAL_INTENSITY = 0.25
CRITICAL_VALUES = {
    0.9: 1.833,
    0.95: 1.96,
    0.99: 2.576
}


def common_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence", type=str, default='CO8', choices=['CD4', 'CO4', 'CD8', 'CO8', 'COC'],
                        help="Name of the task sequence")
    parser.add_argument("--seeds", type=int, nargs='+', default=[1, 2, 3, 4, 5], help="Seed(s) of the run(s) to plot")
    parser.add_argument("--metric", type=str, default='success', help="Name of the metric to store/plot")
    return parser

def common_plot_args() -> argparse.ArgumentParser:
    parser = common_args()
    parser.add_argument("--method", type=str, default='packnet', help="CL method name")
    parser.add_argument("--confidence", type=float, default=0.95, choices=[0.9, 0.95, 0.99], help="Confidence interval")
    parser.add_argument("--task_length", type=int, default=200, help="Number of iterations x 1000 per task")
    return parser


def common_dl_args() -> argparse.ArgumentParser:
    parser = common_args()
    parser.add_argument("--project", type=str, required=True, help="Name of the WandB project")
    parser.add_argument("--method", type=str, help="Optional filter by CL method")
    parser.add_argument("--type", type=str, default='test', choices=['train', 'test'], help="Type of data to download")
    parser.add_argument("--test_envs", type=int, nargs='+', help="Test environment ID of the actions to download")
    parser.add_argument("--wandb_tags", type=str, nargs='+', help="WandB tags to filter runs")
    parser.add_argument("--include_runs", type=str, nargs="+", default=[],
                        help="List of runs that shouldn't be filtered out")
    return parser


def add_task_labels(ax: np.ndarray, envs: List[str], sequence: str, max_steps: int, n_envs: int):
    env_steps = max_steps // n_envs
    task_indicators = np.arange(0 + env_steps // 2, max_steps + env_steps // 2, env_steps)
    fontsize = 10 if n_envs == 4 else 8
    tick_labels = [TRANSLATIONS[env] for env in envs]
    ax2 = ax[0].twiny()
    ax2.set_xlim(ax[0].get_xlim())
    ax2.set_xticks(task_indicators)
    ax2.set_xticklabels(tick_labels, fontsize=fontsize)
    ax2.tick_params(axis='both', which='both', length=0)
    for xtick, color in zip(ax2.get_xticklabels(), COLORS[sequence]):
        xtick.set_color(color)
        xtick.set_fontweight('bold')


def plot_curve(ax, confidence: float, color, label: str, plot_idx: int, iterations: int,
               seed_data: np.ndarray, n_seeds: int):
    mean = np.nanmean(seed_data, axis=0)
    std = np.nanstd(seed_data, axis=0)
    mean = gaussian_filter1d(mean, sigma=KERNEL_SIGMA)
    std = gaussian_filter1d(std, sigma=KERNEL_SIGMA)
    ci = CRITICAL_VALUES[confidence] * std / np.sqrt(n_seeds)
    ax[plot_idx].plot(mean, label=label, color=color)
    ax[plot_idx].tick_params(labelbottom=True)
    ax[plot_idx].fill_between(np.arange(iterations), mean - ci, mean + ci, alpha=INTERVAL_INTENSITY, color=color)


def add_main_ax(fig):
    main_ax = fig.add_subplot(1, 1, 1, frameon=False)
    main_ax.get_xaxis().set_ticks([])
    main_ax.get_yaxis().set_ticks([])
    main_ax.set_xlabel('Timesteps (K)', fontsize=11)
    main_ax.xaxis.labelpad = 25


def get_cl_method(run):
    method = run.config["cl_method"]
    if not method:
        method = 'perfect_memory' if run.config['buffer_type'] == 'reservoir' else 'fine_tuning'
    return method
