from hrgpt.extraction import get_requirements_from_job_description, DEFAULT_REQUIREMENT_TYPE_DEFINITIONS
from hrgpt.utils import get_applicant_document_paths


def score_applicants(job_id: int, candidate_id: int) -> None:
    for job_path, candidate_paths in get_applicant_document_paths(job_id, candidate_id).items():
        job_requirements = get_requirements_from_job_description(job_path, DEFAULT_REQUIREMENT_TYPE_DEFINITIONS)
        print(job_requirements)
