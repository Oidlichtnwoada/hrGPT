import enum
import json

import fitz
import pydantic

from hrgpt.chat.chat_factory import get_answer_message
from hrgpt.config.config import AppConfig, JobRequirementType, get_job_requirement_definitions
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import StrippedString


class RequirementType(enum.StrEnum):
    MANDATORY = enum.auto()
    OPTIONAL = enum.auto()


class Requirement(pydantic.BaseModel):
    type: RequirementType
    specification: StrippedString


def get_sample_requirement() -> Requirement:
    return Requirement(type=RequirementType.MANDATORY, specification='Here should stand the specification text of the requirement')


def get_empty_requirements(app_config: AppConfig) -> dict[JobRequirementType, list[Requirement, ...]]:
    result_dict = {}
    for key in app_config.generic_config.job_requirements_config:
        result_dict[key] = []
    return result_dict


def get_prettify_prompt(text: str):
    return f'Please format the following text more nicely but do not change its contents. Group lines that belong together in a paragraph and format it to improve readability. This is the text:\n{text}'


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


def extract_json_object_string_from_string(text: str) -> str:
    json_start_string = text.find('{')
    json_end_string = text.rfind('}')
    if json_start_string != -1 and json_end_string != -1:
        return text[json_start_string:json_end_string + 1]
    else:
        raise ValueError


def get_prompt_to_extract_requirements(job_description: str, app_config: AppConfig) -> str:
    return f'Please extract the job requirements from the following job description as a JSON object and fill the requirements into the arrays in {get_empty_requirements(app_config)}. Please respect the type of the requirement. An explanation how to fill the arrays with the requirements of the correct type is provided here:\n{dumps(get_job_requirement_definitions(app_config.generic_config.job_requirements_config))}.\nIf there are no suitable requirements for a category, the respective array can stay empty. If there are suitable requirements for a requirement, fill in one or more requirements into the array. All requirements must be unique. The JSON objects in the array must have the following structure {dumps(get_sample_requirement())} and the type must be either "{RequirementType.MANDATORY.value}" or "{RequirementType.OPTIONAL.value}". Here is the job description from which the described JSON object should be extracted:\n\n{job_description.strip()}'


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
