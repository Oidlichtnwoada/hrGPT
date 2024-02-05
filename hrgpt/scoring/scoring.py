import collections
import concurrent.futures
import functools

from hrgpt.extraction.extraction import get_requirements_from_job_description
from hrgpt.matching.matching import (
    match_job_requirements_to_candidate_cv,
    ApplicantMatch,
)
from hrgpt.utils.path_utils import get_applicant_document_paths
from hrgpt.utils.reporting_utils import create_output_files
from hrgpt.utils.timing_utils import TimingClock, TaskType


def score_applicants_for_job_path(
    job_path: str, candidate_paths: list[str]
) -> tuple[ApplicantMatch, ...]:
    TimingClock.start_timer(TaskType.JOB_SCORING, job_path)
    result_tuple: tuple[ApplicantMatch, ...]
    job_requirements = get_requirements_from_job_description(job_path)
    matching_function = functools.partial(
        match_job_requirements_to_candidate_cv, job_requirements
    )
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result_tuple = tuple(executor.map(matching_function, candidate_paths))
    TimingClock.stop_timer(TaskType.JOB_SCORING, job_path)
    return result_tuple


def score_applicants(
    job_ids: tuple[str, ...], candidate_ids: tuple[str, ...]
) -> dict[str, dict[str, ApplicantMatch]]:
    TimingClock.start_timer(TaskType.COMPLETE_SCORING, TaskType.COMPLETE_SCORING.value)
    arguments = list(get_applicant_document_paths(job_ids, candidate_ids).items())
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mapped_arguments = tuple(
            executor.map(lambda x: score_applicants_for_job_path(*x), arguments)
        )
    result_dict: dict[str, dict[str, ApplicantMatch]] = collections.defaultdict(dict)
    for argument_tuple, match_results in zip(arguments, mapped_arguments):
        job_path = argument_tuple[0]
        for candidate_path, match_result in zip(argument_tuple[1], match_results):
            result_dict[job_path][candidate_path] = match_result
    create_output_files(result_dict)
    TimingClock.stop_timer(TaskType.COMPLETE_SCORING, TaskType.COMPLETE_SCORING.value)
    return result_dict
