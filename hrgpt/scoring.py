from hrgpt.utils import get_applicant_document_paths


def score_applicants(job_id: int, candidate_id: int) -> None:
    for job_path, candidate_paths in get_applicant_document_paths(job_id, candidate_id).items():
        print(job_path, candidate_paths)
