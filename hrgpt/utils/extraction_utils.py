import json
import os.path
import tempfile
import typing

import docx
import fitz

from hrgpt.prompting.prompting import get_prompt_to_prettify_text
from hrgpt.utils.chat_utils import get_answer_message
from hrgpt.utils.config_utils import AppConfigFactory
from hrgpt.utils.translation_utils import (
    detect_language,
    get_native_language_of_model,
    translate_text,
)
from hrgpt.utils.type_utils import get_supported_file_types, DocumentFileType, File


def extract_json_object_from_string(text: str) -> dict[str, typing.Any]:
    json_start_string = text.find("{")
    json_end_string = text.rfind("}")
    if json_start_string != -1 and json_end_string != -1:
        json_string = text[json_start_string : json_end_string + 1]
        return typing.cast(dict[str, typing.Any], json.loads(json_string, strict=False))
    else:
        raise ValueError


def apply_replacements(text: str, replacements: tuple[tuple[str, str], ...]) -> str:
    for search_string, replacement_string in replacements:
        text = text.replace(search_string, replacement_string)
    return text


def get_document_text(
    file: File,
    replacements: tuple[tuple[str, str], ...] = ((chr(160), " "), (chr(8203), " ")),
    translate: bool = True,
) -> str:
    suffix = file.type.value
    with tempfile.NamedTemporaryFile(prefix=file.name, suffix=suffix) as temp_file:
        temp_file.write(file.content)
        file_path = os.path.abspath(temp_file.name)
        if suffix not in get_supported_file_types():
            raise RuntimeError
        text_parts: list[str] = []
        match suffix:
            case DocumentFileType.PDF:
                with fitz.open(file_path) as pdf_document:
                    for page in pdf_document:
                        page_text = page.get_text()
                        text_parts.append(page_text)
            case DocumentFileType.DOCX:
                word_document = docx.Document(file_path)
                for paragraph in word_document.paragraphs:
                    paragraph_text = paragraph.text
                    text_parts.append(paragraph_text)
            case DocumentFileType.TEXT:
                with open(file_path) as text_file:
                    file_text = text_file.read()
                    text_parts.append(file_text)
            case _:
                raise RuntimeError
        text = "\n".join(map(str.strip, text_parts))
        text = apply_replacements(text, replacements)
        if translate:
            text_language = detect_language(text)
            if text_language != get_native_language_of_model():
                text = translate_text(
                    text, target_language=get_native_language_of_model()
                )
        text = apply_replacements(text, replacements)
        config = AppConfigFactory.get_app_config()
        if config.generic_config.prettify_config.enable_llm_prettification:
            answer = get_answer_message(get_prompt_to_prettify_text(text))
            text = answer.text
        text = apply_replacements(text, replacements)
        return text
