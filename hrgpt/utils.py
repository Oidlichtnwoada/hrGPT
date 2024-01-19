import collections
import os
import pathlib

import jsonpickle


def dumps(x: object, include_types: bool = False, separators: tuple[str, str] = (', ', ': '), indent: int = 4) -> str:
    return jsonpickle.dumps(x, unpicklable=include_types, separators=separators, indent=indent).strip()


def get_repo_root_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def get_environment_file_path() -> str:
    return os.path.join(get_repo_root_path(), '.env')


def get_module_root_path() -> str:
    return os.path.join(get_repo_root_path(), 'hrgpt')


def get_applicant_document_paths(filter_job_indices: tuple[int, ...] = (0,),
                                 filter_candidate_indices: tuple[int, ...] = (0,)) -> dict[str, list[str]]:
    result_dict = collections.defaultdict(list)
    screening_documents_folder_path = pathlib.Path(os.path.join(get_repo_root_path(), 'screening_documents'))
    for applicant_document_path in screening_documents_folder_path.rglob('candidate_*.pdf'):
        if not applicant_document_path.is_file():
            continue
        if filter_job_indices != (0,) and all([f'job_{filter_job_index}' not in str(applicant_document_path) for filter_job_index in filter_job_indices]):
            continue
        if filter_candidate_indices != (0,) and all([f'candidate_{filter_candidate_index}' not in str(applicant_document_path) for filter_candidate_index in filter_candidate_indices]):
            continue
        job_document_path = os.path.abspath(os.path.join(*applicant_document_path.parts[:-2], 'job_description.pdf'))
        result_dict[job_document_path].append(os.path.abspath(applicant_document_path))
    return result_dict
