__version__ = "0.0.1"

from browsergym.core.registration import register_task

from browsergym.visualwebarena.config import TASK_IDS
from . import task

ALL_WEBARENA_DEFENSE_TASK_IDS = []

# register all MMArena benchmark
for task_id in TASK_IDS:
    gym_id = f"webarena_defense.{task_id}"
    register_task(
        gym_id,
        task.WebArenaDefenseTask,
        task_kwargs={"task_id": task_id},
    )
    ALL_WEBARENA_DEFENSE_TASK_IDS.append(gym_id)
