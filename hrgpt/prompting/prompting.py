from hrgpt.config.config import JobRequirementType
from hrgpt.utils.config_utils import get_job_requirement_definitions, AppConfigFactory
from hrgpt.utils.sample_utils import (
    get_empty_requirements,
    get_sample_requirement,
    get_empty_score,
    get_empty_promising_result,
)
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import (
    RequirementType,
    Requirement,
    RequirementMatch,
)


def get_prompt_to_prettify_text(text: str) -> str:
    return f"Please format the following text more nicely but do not change its contents. Group lines that belong together in a paragraph and format it to improve readability. This is the text:\n\n{text}"


def get_prompt_to_extract_requirements(job_description: str) -> str:
    app_config = AppConfigFactory.get_app_config()
    return f'Please extract the job requirements from the following job description as a JSON object and fill the requirements into the arrays in {get_empty_requirements()}. Please respect the type of the requirement. An explanation how to fill the arrays with the requirements of the correct type is provided here:\n{dumps(get_job_requirement_definitions(app_config.generic_config.job_requirements_config))}.\nIf there are no suitable requirements for a category, the respective array can stay empty. If there are suitable requirements for a requirement, fill in one or more requirements into the array. All requirements must be unique. The JSON objects in the array must have the following structure {dumps(get_sample_requirement())} and the type must be either "{RequirementType.MANDATORY.value}" or "{RequirementType.OPTIONAL.value}". Here is the job description from which the described JSON object should be extracted:\n\n{job_description.strip()}'


def get_prompt_to_match_requirement(
    requirement: Requirement, requirement_type: JobRequirementType, cv_text: str
) -> str:
    app_config = AppConfigFactory.get_app_config()
    minimum_score_value = app_config.generic_config.score_config.minimum_score_value
    maximum_score_value = app_config.generic_config.score_config.maximum_score_value
    return f'Please match the following requirement "{requirement.specification}" with the provided application document and fill the score and the explanation of the score in the following JSON object {dumps(get_empty_score())}. The score should be {minimum_score_value} if the requirement is completely unfulfilled and {maximum_score_value} if the requirement is fully covered. Assign a score between {minimum_score_value} and {maximum_score_value} if the requirement is only partially covered and a higher score means a higher degree of coverage. A description of the type of requirement called "{requirement_type}" is provided here: {dumps(get_job_requirement_definitions(app_config.generic_config.job_requirements_config)[requirement_type])}. Explain the chosen score with the explanation field in the JSON object. The response must contain the filled JSON object. Here is the CV for which the described requirement should be scored and explained:\n\n{cv_text.strip()}.'


def get_prompt_to_check_if_candidate_is_promising(
    requirement_matches: dict[JobRequirementType, list[RequirementMatch]]
) -> str:
    app_config = AppConfigFactory.get_app_config()
    minimum_score_value = app_config.generic_config.score_config.minimum_score_value
    maximum_score_value = app_config.generic_config.score_config.maximum_score_value
    return f'Please report if the following candidate is promising and should proceed in the application process or if the candidate is not promising. Be forgiving for missing mandatory requirements if the candidate is able to acquire the missing requirements quickly. However, if there are many missing mandatory requirements, this might not be possible. The candidate was evaluated to the various job requirements and this was the result: {dumps(requirement_matches)}. A score of {minimum_score_value} means a complete mismatch of the requirement and a score of {maximum_score_value} means a perfect match of the requirement. The higher the score, the better is the requirement matched by the candidate. Furthermore, an explanation is given and if the requirement is mandatory or optional. Please provide the answer in from of a JSON object that looks like this {dumps(get_empty_promising_result())}. Please fill in the promising field with "true" if the candidate is promising and with "false" otherwise. Please provide an explanation why this decision was made in the JSON return value in the respective field.'
