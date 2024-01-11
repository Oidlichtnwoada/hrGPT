import os
import pathlib


def get_repo_root_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def get_environment_file_path() -> str:
    return os.path.join(get_repo_root_path(), '.env')


def get_module_root_path() -> str:
    return os.path.join(get_repo_root_path(), 'hrgpt')


def get_applicant_document_paths(filter_job_index: int = 0,
                                 filter_candidate_index: int = 0) -> list[str]:
    return [os.path.abspath(x) for x in
            pathlib.Path(os.path.join(get_repo_root_path(), 'sample_screening_documents')).rglob('candidate_*.pdf') if
            x.is_file() and
            (filter_job_index == 0 or f'job_{filter_job_index}' in str(x)) and
            (filter_candidate_index == 0 or f'candidate_{filter_candidate_index}' in str(x))]
