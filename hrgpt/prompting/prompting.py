from hrgpt.utils.prompting_utils import (
    replace_placeholders,
    DynamicPlaceholder,
    create_dynamic_placeholders_from_requirement_matches,
    create_dynamic_placeholders_from_requirement,
    create_dynamic_placeholders_from_requirement_type,
)
from hrgpt.utils.type_utils import (
    Requirement,
    RequirementMatch,
    JobRequirementType,
)


def get_prompt_to_prettify_text(text: str) -> str:
    return replace_placeholders(
        "Please format the following text more nicely but do not change its contents. Group lines that belong together in a paragraph and format it to improve readability. This is the text:\n\n{TEXT}",
        dynamic_placeholders=((DynamicPlaceholder.TEXT, text),),
    )


def get_prompt_to_extract_requirements(job_text: str) -> str:
    return replace_placeholders(
        'Please extract the job requirements from the following job description as a JSON object that has the schema of {EMPTY_REQUIREMENTS} and fill the job requirements into the empty arrays. Please respect the job requirement type of the extracted job requirement. A mapping how to fill the empty arrays with the job requirements of the correct job requirement type is provided here:\n{REQUIREMENT_TYPE_DEFINITIONS}.\nIf there are no suitable job requirements for a job requirement type, the respective array for this job requirement type can stay empty. If there are suitable job requirements for a job requirement type, fill in one or more job requirements into the empty array. All job requirements must be unique. The JSON objects in the array must have the following structure {SAMPLE_REQUIREMENT}, the "type" field must be either "{REQUIREMENT_TYPE_MANDATORY}" or "{REQUIREMENT_TYPE_OPTIONAL}", and the "specification" field should contain a verbal text describing the job requirement. Here is the job description from which the described JSON object should be extracted:\n\n{JOB_TEXT}',
        dynamic_placeholders=((DynamicPlaceholder.JOB_TEXT, job_text),),
    )


def get_prompt_to_match_requirement(
    cv_text: str,
    requirement: Requirement,
    requirement_type: JobRequirementType,
) -> str:
    return replace_placeholders(
        'Please match the following given job requirement "{REQUIREMENT_SPECIFICATION}" with the provided CV and fill the "value" and the "explanation" field of the following JSON object {EMPTY_SCORE}. The value should be {MINIMUM_SCORE_VALUE} if the requirement is completely unfulfilled and {MAXIMUM_SCORE_VALUE} if the requirement is fully covered. Assign a value between {MINIMUM_SCORE_VALUE} and {MAXIMUM_SCORE_VALUE} if the requirement is only partially covered and a higher value means a higher degree of coverage. A description of the job requirement type of the given job requirement called "{REQUIREMENT_TYPE_NAME}" is provided here: {REQUIREMENT_TYPE_DEFINITION}. Explain the chosen "value" field in the JSON object with the "explanation" field in the JSON object. The response must contain the filled JSON object. Here is the CV for which the described JSON object should be constructed:\n\n{CV_TEXT}.',
        dynamic_placeholders=(
            (DynamicPlaceholder.CV_TEXT, cv_text),
            *create_dynamic_placeholders_from_requirement(requirement),
            *create_dynamic_placeholders_from_requirement_type(requirement_type),
        ),
    )


def get_prompt_to_check_if_candidate_is_promising(
    requirement_matches: dict[JobRequirementType, list[RequirementMatch]]
) -> str:
    return replace_placeholders(
        'Please report if the following candidate is promising and should proceed in the application process or if the candidate is not promising. Be forgiving for missing mandatory requirements if the candidate is able to acquire the missing requirements quickly. However, if there are many missing mandatory requirements, this might not be possible. The candidate was evaluated to all job requirements and this was the result: {REQUIREMENT_MATCHES}. A value of {MINIMUM_SCORE_VALUE} means a complete mismatch between the job requirement and the applicant and a value of {MAXIMUM_SCORE_VALUE} means a perfect match between the job requirement and the applicant. The higher the value, the better is the requirement satisfied by the candidate. Furthermore, an explanation is given and if the requirement is mandatory or optional. Please provide the answer as a JSON object that looks like this {EMPTY_PROMISING_RESULT}. Please fill in the "promising" field with "true" if the candidate is promising and with "false" otherwise. Please provide an explanation why this decision was made in the "explanation" field in the JSON return value. Please return the described JSON object.',
        dynamic_placeholders=(
            *create_dynamic_placeholders_from_requirement_matches(requirement_matches),
        ),
    )
