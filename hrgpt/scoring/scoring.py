import collections
import concurrent.futures
import functools

import polars as pl

from hrgpt.extraction.extraction import get_requirements_from_job_description
from hrgpt.matching.matching import match_job_requirements_to_cv_file
from hrgpt.utils.reporting_utils import create_output_files
from hrgpt.utils.timing_utils import TimingClock, TaskType
from hrgpt.utils.type_utils import ApplicantMatch, ScoreWorkload


def score_applicants_for_workload(
    score_workload: ScoreWorkload,
) -> tuple[ApplicantMatch, ...]:
    TimingClock.start_timer(TaskType.JOB_SCORING, score_workload.job_file.name)
    result_tuple: tuple[ApplicantMatch, ...]
    job_requirements = get_requirements_from_job_description(score_workload.job_file)
    matching_function = functools.partial(
        match_job_requirements_to_cv_file, job_requirements
    )
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result_tuple = tuple(executor.map(matching_function, score_workload.cv_files))
    TimingClock.stop_timer(TaskType.JOB_SCORING, score_workload.job_file.name)
    return result_tuple


def score_applicants(
    score_workloads: tuple[ScoreWorkload, ...]
) -> dict[str, tuple[pl.DataFrame, dict[str, ApplicantMatch]]]:
    TimingClock.start_timer(TaskType.COMPLETE_SCORING, TaskType.COMPLETE_SCORING.value)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mapped_arguments = tuple(
            executor.map(lambda x: score_applicants_for_workload(x), score_workloads)
        )
    score_result: dict[str, dict[str, ApplicantMatch]] = collections.defaultdict(dict)
    for workload, match_results in zip(score_workloads, mapped_arguments):
        job_name = workload.job_file.name
        for cv_file, match_result in zip(workload.cv_files, match_results):
            score_result[job_name][cv_file.name] = match_result
    job_dfs = create_output_files(score_result)
    result_dict: dict[str, tuple[pl.DataFrame, dict[str, ApplicantMatch]]] = {}
    for job_name, job_result in score_result.items():
        result_dict[job_name] = (job_dfs[job_name], job_result)
    TimingClock.stop_timer(TaskType.COMPLETE_SCORING, TaskType.COMPLETE_SCORING.value)
    return result_dict
