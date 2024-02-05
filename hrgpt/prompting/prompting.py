from hrgpt.config.config import AppConfig, get_job_requirement_definitions
from hrgpt.utils.sample_utils import get_empty_requirements, get_sample_requirement
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import RequirementType


def get_prettify_prompt(text: str):
    return f'Please format the following text more nicely but do not change its contents. Group lines that belong together in a paragraph and format it to improve readability. This is the text:\n{text}'


def get_prompt_to_extract_requirements(job_description: str, app_config: AppConfig) -> str:
    return f'Please extract the job requirements from the following job description as a JSON object and fill the requirements into the arrays in {get_empty_requirements(app_config)}. Please respect the type of the requirement. An explanation how to fill the arrays with the requirements of the correct type is provided here:\n{dumps(get_job_requirement_definitions(app_config.generic_config.job_requirements_config))}.\nIf there are no suitable requirements for a category, the respective array can stay empty. If there are suitable requirements for a requirement, fill in one or more requirements into the array. All requirements must be unique. The JSON objects in the array must have the following structure {dumps(get_sample_requirement())} and the type must be either "{RequirementType.MANDATORY.value}" or "{RequirementType.OPTIONAL.value}". Here is the job description from which the described JSON object should be extracted:\n\n{job_description.strip()}'
