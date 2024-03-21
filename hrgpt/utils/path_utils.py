import collections
import os
import pathlib
import random
import string

from hrgpt.utils.type_utils import get_supported_file_types


def get_repo_root_path() -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )


def get_screening_documents_path() -> str:
    return os.path.join(get_repo_root_path(), "screening_documents")


def get_job_folder_path_by_job_index(job_index: int) -> str:
    return os.path.join(get_screening_documents_path(), f"job_{job_index}")


def get_responses_csv_path() -> str:
    return os.path.join(get_repo_root_path(), "online_form_responses", "responses.csv")


def get_module_root_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def get_default_model_config_json_path() -> str:
    return os.path.join(get_module_root_path(), "default_config.json")


def get_default_environment_secrets_file_path() -> str:
    return os.path.join(get_module_root_path(), ".env.json")


def get_job_document_path_from_applicant_document_path(
    applicant_document_path: pathlib.Path,
) -> str:
    job_document_candidate_paths = [
        pathlib.Path(
            os.path.join(
                *applicant_document_path.parts[:-2], f"job_description{suffix}"
            )
        )
        for suffix in get_supported_file_types()
    ]
    for candidate_path in job_document_candidate_paths:
        if candidate_path.exists():
            return os.path.abspath(candidate_path)
    raise RuntimeError


def get_applicant_document_paths(
    filter_job_indices: tuple[str, ...] = (),
    filter_candidate_indices: tuple[str, ...] = (),
) -> dict[str, list[str]]:
    result_dict = collections.defaultdict(list)
    screening_documents_folder_path = pathlib.Path(get_screening_documents_path())
    for applicant_document_path in screening_documents_folder_path.rglob("candidate_*"):
        if (
            not applicant_document_path.is_file()
            or applicant_document_path.suffix not in get_supported_file_types()
        ):
            continue
        if filter_job_indices != () and all(
            [
                f"job_{filter_job_index}" not in str(applicant_document_path)
                for filter_job_index in filter_job_indices
            ]
        ):
            continue
        if filter_candidate_indices != () and all(
            [
                f"candidate_{filter_candidate_index}"
                not in str(applicant_document_path)
                for filter_candidate_index in filter_candidate_indices
            ]
        ):
            continue
        job_document_path = get_job_document_path_from_applicant_document_path(
            applicant_document_path
        )
        result_dict[job_document_path].append(os.path.abspath(applicant_document_path))
    return result_dict


def get_random_file_name(length: int = 64) -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))
