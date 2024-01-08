import re
from pypdf import PdfReader, PdfWriter, PageObject

from hrgpt.utils import get_applicant_document_paths


def is_text_content_line(string_content_line: str) -> bool:
    return string_content_line.endswith('TJ')


def replace_text_content(string_content_line: str) -> str:
    pattern = '\\[<([0-9A-F]+)>] TJ'
    matches = re.findall(pattern, string_content_line)
    if len(matches) != 1:
        raise RuntimeError
    text_bytes = bytes.fromhex(matches[0])
    character_encoding = 'utf-16be'
    text = text_bytes.decode(character_encoding)
    modified_text = text
    modified_content_line = re.sub(
        pattern,
        f'[<{modified_text.encode(character_encoding).hex().upper()}>] TJ',
        string_content_line)
    return modified_content_line


def anonymize_string_content(string_content: str):
    string_content_lines = string_content.split('\n')
    modified_content_lines = []
    for string_content_line in string_content_lines:
        if is_text_content_line(string_content_line):
            modified_string_content_line = replace_text_content(string_content_line)
            modified_content_lines.append(modified_string_content_line)
        else:
            modified_content_lines.append(string_content_line)
    return '\n'.join(modified_content_lines)


def anonymize_applicant_document_page(page: PageObject) -> None:
    page_contents = page.get_contents()
    decoded_page_contents = page_contents.get_data().decode('utf-8')
    anonymized_string_content = anonymize_string_content(decoded_page_contents)
    encoded_page_contents = anonymized_string_content.encode('utf-8')
    page_contents.set_data(encoded_page_contents)
    page.replace_contents(page_contents)


def anonymize_applicant_document(applicant_document_path: str) -> None:
    pdf_reader = PdfReader(stream=applicant_document_path)
    pdf_writer = PdfWriter(clone_from=pdf_reader)
    for page in pdf_writer.pages:
        anonymize_applicant_document_page(page)
    pdf_writer.write(applicant_document_path)
    pdf_writer.close()


def anonymize_applicant_documents() -> None:
    for applicant_document_path in get_applicant_document_paths():
        anonymize_applicant_document(applicant_document_path)
