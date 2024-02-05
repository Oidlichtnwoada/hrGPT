import collections
import enum
import time

import math

from hrgpt.logger.logger import LoggerFactory


class TaskType(enum.StrEnum):
    REQUIREMENT_EXTRACTION = enum.auto()
    APPLICANT_MATCHING = enum.auto()
    JOB_SCORING = enum.auto()
    COMPLETE_SCORING = enum.auto()


class TimingClock:
    timing_dict: dict[TaskType, dict[str, float]] = collections.defaultdict(dict)

    @classmethod
    def start_timer(cls, task_type: TaskType, timing_id: str) -> None:
        cls.timing_dict[task_type][timing_id] = time.time()

    @classmethod
    def stop_timer(
        cls, task_type: TaskType, timing_id: str, log_time: bool = True
    ) -> float:
        if timing_id not in cls.timing_dict[task_type]:
            raise RuntimeError
        elapsed_seconds = time.time() - cls.timing_dict[task_type][timing_id]
        del cls.timing_dict[task_type][timing_id]
        if log_time:
            cls.log_completed_task(task_type, timing_id, elapsed_seconds)
        return elapsed_seconds

    @classmethod
    def log_completed_task(
        cls, task_type: TaskType, timing_id: str, elapsed_seconds: float
    ) -> None:
        logger = LoggerFactory.get_logger()
        message = f'Task of type "{task_type}" with id "{timing_id}" completed in {math.ceil(elapsed_seconds)} seconds'
        match task_type:
            case TaskType.REQUIREMENT_EXTRACTION | TaskType.APPLICANT_MATCHING:
                logger.debug(message)
            case TaskType.JOB_SCORING | TaskType.COMPLETE_SCORING:
                logger.info(message)
