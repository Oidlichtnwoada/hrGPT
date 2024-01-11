import concurrent.futures
import os
import random
import shutil
import string

import asposepdfcloud
import fitz
import pandas

from hrgpt.utils import get_applicant_document_paths, get_module_root_path


def generate_random_names(amount: int = 1,
                          forenames_csv_path: str = os.path.join(get_module_root_path(), 'forenames.csv'),
                          surnames_csv_path: str = os.path.join(get_module_root_path(), 'surnames.csv')) -> list[str]:
    forenames = pandas.read_csv(forenames_csv_path)['name'].tolist()
    surnames = pandas.read_csv(surnames_csv_path)['name'].tolist()
    random_names = set()
    while len(random_names) < amount:
        random_forename = random.choice(forenames)
        random_surname = random.choice(surnames)
        random_name = f'{random_forename.capitalize()} {random_surname.capitalize()}'
        if len(random_name.split(' ')) != 2:
            continue
        random_names.add(random_name)
    return list(random_names)


def get_random_file_name(length: int = 64) -> str:
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def get_text_replacement_list(replacements_path: str = os.path.join(get_module_root_path(),
                                                                    'replacements.txt')) -> list[tuple[str, str]]:
    with open(replacements_path) as file:
        file_content_lines = file.read().strip().split('\n')
    return [tuple(line.split('>')) for line in file_content_lines if not line.startswith('#')]


def get_text_replacements() -> asposepdfcloud.TextReplaceListRequest:
    text_replaces = [asposepdfcloud.models.TextReplace(
        old_value=old_value, new_value=new_value, regex='false') for old_value, new_value in
        get_text_replacement_list()]
    text_replace_list = asposepdfcloud.models.TextReplaceListRequest(text_replaces=text_replaces)
    return text_replace_list


def clean_pdf_document(pdf_document_path: str,
                       clean: bool = True,
                       compress: bool = True,
                       linearize: bool = True,
                       prettify: bool = True):
    pdf_document = fitz.open(pdf_document_path)
    kwargs = {}
    if clean:
        kwargs.update({'garbage': 4, 'clean': True})
    if compress:
        kwargs.update({'deflate': True})
    else:
        kwargs.update({'expand': 255})
    if linearize:
        kwargs.update({'linear': True})
    if prettify:
        kwargs.update({'pretty': True})
    random_file_name = get_random_file_name()
    pdf_document.save(random_file_name, **kwargs, encryption=fitz.PDF_ENCRYPT_NONE)
    shutil.copyfile(random_file_name, pdf_document.name)
    os.remove(random_file_name)


def remove_links(pdf_document_path: str) -> None:
    pdf_document = fitz.open(pdf_document_path)
    for page in pdf_document:
        links = page.get_links()
        for link in links:
            page.delete_link(link)
    pdf_document.save(pdf_document_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)


def anonymize_applicant_document(pdf_api: asposepdfcloud.apis.pdf_api.PdfApi,
                                 applicant_document_path: str,
                                 replace_text: bool = True) -> None:
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
    pdf_api_client = asposepdfcloud.api_client.ApiClient(
        app_key=os.getenv('ASPOSE_APP_KEY'),
        app_sid=os.getenv('ASPOSE_APP_SID'))
    pdf_api = asposepdfcloud.apis.pdf_api.PdfApi(pdf_api_client)
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.getenv('PARALLEL_PDF_WORKERS'))) as executor:
        for applicant_document_path in get_applicant_document_paths():
            executor.submit(anonymize_applicant_document, pdf_api, applicant_document_path)
