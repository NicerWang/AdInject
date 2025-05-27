import json
import logging
from typing import Literal
import fire
import numpy as np
from browsergym.experiments.benchmark.configs import DEFAULT_HIGHLEVEL_ACTION_SET_ARGS
from browsergym.experiments.benchmark.utils import make_env_args_list_from_repeat_tasks
from browsergym.experiments.benchmark import Benchmark
from agentlab.experiments.study import Study
from agentlab.llm.chat_api import OpenAIModelArgs
from agentlab.agents import dynamic_prompting as dp
from agentlab.agents.generic_agent.generic_agent_prompt import GenericPromptFlags
from agentlab.agents.generic_agent.generic_agent import GenericAgentArgs

import sys

import browsergym.vwa_defense

sys.path.append("..")

logging.getLogger().setLevel(logging.INFO)

tasks = json.load(open("./defense/vwa_defense/src/browsergym/vwa_defense/task.json"))
ALL_DEFENSE_TASKS = []

for task in tasks:
    task_id = task["task_id"]
    task_name = f"webarena_defense.{task_id}"
    ALL_DEFENSE_TASKS.append(task_name)


def launch(
    model,
    type: Literal["a11y_tree", "screenshot_a11y_tree", "screenshot_som"],
    relaunch_path: str = None,
    n_jobs: int = 1,
):
    use_a11y_tree = type in ["a11y_tree", "screenshot_a11y_tree"]
    use_screenshot = type in ["screenshot_som", "screenshot_a11y_tree"]
    use_som = type == "screenshot_som"

    flags = GenericPromptFlags(
        obs=dp.ObsFlags(
            use_html=False,
            use_ax_tree=use_a11y_tree,
            use_focused_element=True,
            use_error_logs=True,
            use_history=True,
            use_past_error_logs=False,
            use_action_history=True,
            use_think_history=True,
            use_diff=False,
            html_type="pruned_html",
            use_screenshot=use_screenshot,
            use_som=use_som,
            extract_visible_tag=True,
            extract_clickable_tag=True,
            extract_coords="False",
            filter_visible_elements_only=False,
        ),
        action=dp.ActionFlags(
            multi_actions=False,
            action_set="visualwebarena",
            long_description=False,
            individual_examples=False,
        ),
        use_plan=False,
        use_criticise=False,
        use_thinking=True,
        use_memory=False,
        use_concrete_example=True,
        use_abstract_example=True,
        use_hints=True,
        enable_chat=False,
        max_prompt_tokens=40_000,
        be_cautious=True,
        extra_instructions=None,
    )

    agent_arg = GenericAgentArgs(
        chat_model_args=OpenAIModelArgs(
            model_name=model,
            temperature=0.5,
            max_new_tokens=1000,
            vision_support=True,
        ),
        flags=flags,
    )

    benchmark = Benchmark(
        name="visualwebarena",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["visualwebarena"],
        is_multi_tab=True,
        supports_parallel_seeds=False,
        backends=["visualwebarena"],
        # backends=[],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=ALL_DEFENSE_TASKS,
            # task_list=[ALL_DEFENSE_TASKS[0]],
            max_steps=30,
            n_repeats=1,
            seeds_rng=np.random.RandomState(42),
        ),
    )

    if relaunch_path is not None:
        study = Study.load(relaunch_path)
        study.find_incomplete(include_errors=True)

    else:
        study = Study([agent_arg], benchmark, logging_level_stdout=logging.WARNING)

    study.run(
        n_jobs=n_jobs,
        parallel_backend="sequential",
        strict_reproducibility=False,
        n_relaunch=1,
    )


if __name__ == "__main__":
    fire.Fire(launch)
