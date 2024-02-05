import json

import fitz

from hrgpt.chat.chat_factory import get_answer_message
from hrgpt.config.config import AppConfig
from hrgpt.prompting.prompting import get_prettify_prompt, get_prompt_to_extract_requirements
from hrgpt.utils.extraction_utils import extract_json_object_string_from_string
from hrgpt.utils.sample_utils import get_empty_requirements
from hrgpt.utils.type_utils import Requirement


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
        answer = get_answer_message(get_prettify_prompt(text), app_config)
        text = answer.text
    return text


def get_requirements_from_job_description(
    job_description_pdf_file_path: str,
    app_config: AppConfig,
) -> dict[str, list[Requirement, ...]]:
    # generate the extraction prompt
    job_description_text = get_pdf_document_text(job_description_pdf_file_path, app_config)
    prompt = get_prompt_to_extract_requirements(job_description_text, app_config)
    # send the prompt to the model
    answer = get_answer_message(prompt, app_config)
    # extract the JSON object from the answer
    extracted_json_object = json.loads(extract_json_object_string_from_string(answer.text))
    # validate the structure and transform the JSON object from the answer
    job_requirements = get_empty_requirements(app_config)
    for requirement_type, requirements in extracted_json_object.items():
        if requirement_type not in job_requirements:
            # do not add unspecified requirement types
            continue
        if not isinstance(requirements, list):
            # the requirements should be given as a list
            continue
        for requirement in requirements:
            if not isinstance(requirement, dict):
                # each requirement should be an object
                continue
            # validate the requirement
            requirement_object = Requirement.model_validate(requirement)
            # add the requirement
            job_requirements[requirement_type].append(requirement_object)
    return job_requirements
