import os
import pathlib


def get_repo_root_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def get_applicant_document_paths() -> list[str]:
    return [os.path.abspath(x) for x in
            pathlib.Path(os.path.join(get_repo_root_path(), 'sample_screening_documents')).rglob('candidate_*.pdf') if
            x.is_file()]
