import fitz

from hrgpt.chat.chat_factory import get_answer_message
from hrgpt.config.config import AppConfig
from hrgpt.prompting.prompting import get_prompt_to_prettify_text


def get_pdf_document_text(pdf_document_path: str,
                          app_config: AppConfig,
                          replacements: tuple[tuple[str, str]] = ((chr(160), ' '),),
                          prettify: bool = True) -> str:
    with fitz.open(pdf_document_path) as pdf_document:
        page_texts = []
        for page in pdf_document:
            page_text = page.get_text().strip()
            for search_string, replacement_string in replacements:
                page_text = page_text.replace(search_string, replacement_string)
            page_texts.append(page_text)
        text = '\n'.join(page_texts)
    if prettify:
        answer = get_answer_message(get_prompt_to_prettify_text(text), app_config)
        text = answer.text
    return text
