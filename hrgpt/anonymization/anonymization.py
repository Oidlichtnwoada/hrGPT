import concurrent.futures
import os
import random
import shutil

import asposepdfcloud
import pandas

from hrgpt.utils.path_utils import (
    get_module_root_path,
    get_applicant_document_paths,
    get_random_file_name,
)
from hrgpt.utils.pdf_utils import clean_pdf_document, remove_links
from hrgpt.utils.secret_utils import get_aspose_pdf_cloud_credentials


def generate_random_names(
    amount: int = 1,
    forenames_csv_path: str = os.path.join(get_module_root_path(), "forenames.csv"),
    surnames_csv_path: str = os.path.join(get_module_root_path(), "surnames.csv"),
) -> list[str]:
    forenames = pandas.read_csv(forenames_csv_path)["name"].tolist()
    surnames = pandas.read_csv(surnames_csv_path)["name"].tolist()
    random_names: set[str] = set()
    while len(random_names) < amount:
        random_forename = random.choice(forenames)
        random_surname = random.choice(surnames)
        random_name = f"{random_forename.capitalize()} {random_surname.capitalize()}"
        if len(random_name.split(" ")) != 2:
            continue
        random_names.add(random_name)
    return list(random_names)


def check_tuple_length_and_return(value: tuple[str, ...]) -> tuple[str, str]:
    if len(value) != 2:
        raise ValueError
    return value


def get_text_replacement_list(
    replacements_path: str = os.path.join(get_module_root_path(), "replacements.txt")
) -> list[tuple[str, str]]:
    with open(replacements_path) as file:
        file_content_lines = file.read().strip().split("\n")
    return [
        check_tuple_length_and_return(tuple(line.split(">")))
        for line in file_content_lines
        if not line.startswith("#")
    ]


def get_text_replacements() -> asposepdfcloud.TextReplaceListRequest:
    text_replaces = [
        asposepdfcloud.models.TextReplace(
            old_value=old_value, new_value=new_value, regex="false"
        )
        for old_value, new_value in get_text_replacement_list()
    ]
    text_replace_list = asposepdfcloud.models.TextReplaceListRequest(
        text_replaces=text_replaces
    )
    return text_replace_list


def anonymize_applicant_document(
    applicant_document_path: str, replace_text: bool = True
) -> None:
    # create the api
    credentials = get_aspose_pdf_cloud_credentials()
    pdf_api_client = asposepdfcloud.api_client.ApiClient(
        app_key=credentials[0], app_sid=credentials[1]
    )
    pdf_api = asposepdfcloud.apis.pdf_api.PdfApi(pdf_api_client)

    # clean the document at the start
    clean_pdf_document(applicant_document_path)

    # remove all hyperlinks from the pdf documents
    remove_links(applicant_document_path)

    if replace_text:
        # apply the text replacements
        remote_name = get_random_file_name()
        pdf_api.upload_file(remote_name, applicant_document_path)
        pdf_api.post_document_text_replace(remote_name, get_text_replacements())
        downloaded_file_path = pdf_api.download_file(remote_name)
        shutil.copyfile(downloaded_file_path, applicant_document_path)

    # clean the document at the end
    clean_pdf_document(applicant_document_path)


def anonymize_applicant_documents() -> None:
    paths = []
    for applicant_document_paths in get_applicant_document_paths().values():
        for applicant_document_path in applicant_document_paths:
            paths.append(applicant_document_path)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(anonymize_applicant_document, paths)
