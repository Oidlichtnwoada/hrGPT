import concurrent.futures
import os
import random
import shutil
import string

import asposepdfcloud

from hrgpt.utils import get_applicant_document_paths, get_module_root_path


def get_random_name(length: int = 64) -> str:
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def get_text_replacement_list(replacements_path: str = os.path.join(get_module_root_path(),
                                                                    'replacements.txt')) -> list[tuple[str, str]]:
    with open(replacements_path) as file:
        file_content_lines = file.read().strip().split()
    return [tuple(line.split('>')) for line in file_content_lines]


def get_text_replacements() -> asposepdfcloud.TextReplaceListRequest:
    text_replaces = [asposepdfcloud.models.TextReplace(
        old_value=old_value, new_value=new_value, regex='false') for old_value, new_value in
        get_text_replacement_list()]
    text_replace_list = asposepdfcloud.models.TextReplaceListRequest(text_replaces=text_replaces)
    return text_replace_list


def anonymize_applicant_document(pdf_api: asposepdfcloud.apis.pdf_api.PdfApi, applicant_document_path: str) -> None:
    remote_name = get_random_name()
    pdf_api.upload_file(remote_name, applicant_document_path)
    pdf_api.post_document_text_replace(remote_name, get_text_replacements())
    downloaded_file_path = pdf_api.download_file(remote_name)
    shutil.copyfile(downloaded_file_path, applicant_document_path)


def anonymize_applicant_documents() -> None:
    pdf_api_client = asposepdfcloud.api_client.ApiClient(
        app_key=os.getenv('ASPOSE_APP_KEY'),
        app_sid=os.getenv('ASPOSE_APP_SID'))
    pdf_api = asposepdfcloud.apis.pdf_api.PdfApi(pdf_api_client)
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.getenv('PARALLEL_PDF_WORKERS'))) as executor:
        for applicant_document_path in get_applicant_document_paths():
            executor.submit(anonymize_applicant_document, pdf_api, applicant_document_path)