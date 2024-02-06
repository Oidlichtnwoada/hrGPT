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
    JobRequirementType,
)


def get_prompt_to_prettify_text(text: str) -> str:
    return f"Please format the following text more nicely but do not change its contents. Group lines that belong together in a paragraph and format it to improve readability. This is the text:\n\n{text}"


def get_prompt_to_extract_requirements(job_description: str) -> str:
    app_config = AppConfigFactory.get_app_config()
    return f'Please extract the job requirements from the following job description as a JSON object that has the schema of {get_empty_requirements()} and fill the job requirements into the empty arrays. Please respect the job requirement type of the extracted job requirement. A mapping how to fill the empty arrays with the job requirements of the correct job requirement type is provided here:\n{dumps(get_job_requirement_definitions(app_config.generic_config.job_requirements_config))}.\nIf there are no suitable job requirements for a job requirement type, the respective array for this job requirement type can stay empty. If there are suitable job requirements for a job requirement type, fill in one or more job requirements into the empty array. All job requirements must be unique. The JSON objects in the array must have the following structure {dumps(get_sample_requirement())}, the "type" field must be either "{RequirementType.MANDATORY.value}" or "{RequirementType.OPTIONAL.value}", and the "specification" field should contain a verbal text describing the job requirement. Here is the job description from which the described JSON object should be extracted:\n\n{job_description.strip()}'


def get_prompt_to_match_requirement(
    requirement: Requirement, requirement_type: JobRequirementType, cv_text: str
) -> str:
    app_config = AppConfigFactory.get_app_config()
    minimum_score_value = app_config.generic_config.score_config.minimum_score_value
    maximum_score_value = app_config.generic_config.score_config.maximum_score_value
    return f'Please match the following given job requirement "{requirement.specification}" with the provided CV and fill the "value" and the "explanation" field of the following JSON object {dumps(get_empty_score())}. The value should be {minimum_score_value} if the requirement is completely unfulfilled and {maximum_score_value} if the requirement is fully covered. Assign a value between {minimum_score_value} and {maximum_score_value} if the requirement is only partially covered and a higher value means a higher degree of coverage. A description of the job requirement type of the given job requirement called "{requirement_type}" is provided here: {dumps(get_job_requirement_definitions(app_config.generic_config.job_requirements_config)[requirement_type])}. Explain the chosen "value" field in the JSON object with the "explanation" field in the JSON object. The response must contain the filled JSON object. Here is the CV for which the described JSON object should be constructed:\n\n{cv_text.strip()}.'


def get_prompt_to_check_if_candidate_is_promising(
    requirement_matches: dict[JobRequirementType, list[RequirementMatch]]
) -> str:
    app_config = AppConfigFactory.get_app_config()
    minimum_score_value = app_config.generic_config.score_config.minimum_score_value
    maximum_score_value = app_config.generic_config.score_config.maximum_score_value
    return f'Please report if the following candidate is promising and should proceed in the application process or if the candidate is not promising. Be forgiving for missing mandatory requirements if the candidate is able to acquire the missing requirements quickly. However, if there are many missing mandatory requirements, this might not be possible. The candidate was evaluated to all job requirements and this was the result: {dumps(requirement_matches)}. A value of {minimum_score_value} means a complete mismatch between the job requirement and the applicant and a value of {maximum_score_value} means a perfect match between the job requirement and the applicant. The higher the value, the better is the requirement satisfied by the candidate. Furthermore, an explanation is given and if the requirement is mandatory or optional. Please provide the answer as a JSON object that looks like this {dumps(get_empty_promising_result())}. Please fill in the "promising" field with "true" if the candidate is promising and with "false" otherwise. Please provide an explanation why this decision was made in the "explanation" field in the JSON return value. Please return the described JSON object.'
