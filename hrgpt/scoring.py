import collections
import concurrent.futures
import functools
import logging

from hrgpt.extraction import get_requirements_from_job_description, DEFAULT_REQUIREMENT_TYPE_DEFINITIONS
from hrgpt.matcher import match_job_requirements_to_candidate_cv, DEFAULT_REQUIREMENT_TYPE_WEIGHTINGS, ApplicantMatch
from hrgpt.utils import get_applicant_document_paths


def score_applicants_for_job_path(job_path: str, candidate_paths: list[str]) -> tuple[ApplicantMatch]:
    job_requirements = get_requirements_from_job_description(job_path, DEFAULT_REQUIREMENT_TYPE_DEFINITIONS)
    matching_function = functools.partial(match_job_requirements_to_candidate_cv,
                                          job_requirements,
                                          DEFAULT_REQUIREMENT_TYPE_DEFINITIONS,
                                          DEFAULT_REQUIREMENT_TYPE_WEIGHTINGS, )
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return tuple(executor.map(matching_function, candidate_paths))


def score_applicants(job_id: int, candidate_id: int) -> dict[str, dict[str, ApplicantMatch]]:
    arguments = list(get_applicant_document_paths(job_id, candidate_id).items())
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mapped_arguments = tuple(executor.map(lambda x: score_applicants_for_job_path(*x), arguments))
    result_dict = collections.defaultdict(dict)
    for arguments, match_results in zip(arguments, mapped_arguments):
        job_path = arguments[0]
        for candidate_path, match_result in zip(arguments[1], match_results):
            result_dict[job_path][candidate_path] = match_result
    logging.debug(result_dict)
    return result_dict
