from hrgpt.utils import get_applicant_document_paths


def score_applicants(job_id: int, candidate_id: int) -> None:
    applicant_document_paths = get_applicant_document_paths(job_id, candidate_id)
