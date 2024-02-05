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


def score_applicants_for_job_path(
    job_path: str, candidate_paths: list[str]
) -> tuple[ApplicantMatch, ...]:
    job_requirements = get_requirements_from_job_description(job_path)
    matching_function = functools.partial(
        match_job_requirements_to_candidate_cv, job_requirements
    )
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return tuple(executor.map(matching_function, candidate_paths))


def score_applicants(
    job_ids: tuple[str, ...], candidate_ids: tuple[str, ...]
) -> dict[str, dict[str, ApplicantMatch]]:
    arguments = list(get_applicant_document_paths(job_ids, candidate_ids).items())
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mapped_arguments = tuple(
            executor.map(lambda x: score_applicants_for_job_path(*x), arguments)
        )
    result_dict = collections.defaultdict(dict)
    for arguments, match_results in zip(arguments, mapped_arguments):
        job_path = arguments[0]
        for candidate_path, match_result in zip(arguments[1], match_results):
            result_dict[job_path][candidate_path] = match_result
    create_output_files(result_dict)
    return result_dict
