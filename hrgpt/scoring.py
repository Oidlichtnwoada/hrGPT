import concurrent.futures
import functools

from hrgpt.extraction import get_requirements_from_job_description, DEFAULT_REQUIREMENT_TYPE_DEFINITIONS
from hrgpt.matcher import match_job_requirements_to_candidate_cv, DEFAULT_REQUIREMENT_TYPE_WEIGHTINGS
from hrgpt.utils import get_applicant_document_paths


def score_applicants(job_id: int, candidate_id: int) -> None:
    for job_path, candidate_paths in get_applicant_document_paths(job_id, candidate_id).items():
        job_requirements = get_requirements_from_job_description(job_path, DEFAULT_REQUIREMENT_TYPE_DEFINITIONS)
        matching_function = functools.partial(match_job_requirements_to_candidate_cv,
                                              job_requirements,
                                              DEFAULT_REQUIREMENT_TYPE_DEFINITIONS,
                                              DEFAULT_REQUIREMENT_TYPE_WEIGHTINGS, )
        with concurrent.futures.ThreadPoolExecutor() as executor:
            candidate_matches = executor.map(matching_function, candidate_paths)
        for candidate_match in candidate_matches:
            print(candidate_match)
