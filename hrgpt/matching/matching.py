import collections
import statistics
import typing

import pydantic

from hrgpt.chat.chat_factory import get_answer_messages, get_answer_message
from hrgpt.config.config import AppConfig, get_job_requirement_weightings, JobRequirementType, get_job_requirement_definitions
from hrgpt.extraction.extraction import Requirement, get_pdf_document_text, extract_json_object_string_from_string
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import StrippedString

ScoreValue: typing.TypeAlias = float


class Score(pydantic.BaseModel):
    value: ScoreValue
    explanation: StrippedString


class RequirementMatch(pydantic.BaseModel):
    score: Score
    requirement: Requirement


class PromisingResult(pydantic.BaseModel):
    promising: bool
    explanation: StrippedString


class ApplicantMatch(pydantic.BaseModel):
    total_score: ScoreValue
    promising_result: PromisingResult
    requirement_matches: dict[str, list[RequirementMatch]]


def get_empty_score(app_config: AppConfig) -> Score:
    return Score(value=app_config.generic_config.score_config.minimum_score_value, explanation='')


def get_empty_promising_result() -> PromisingResult:
    return PromisingResult(promising=False, explanation='')


def get_prompt_to_match_requirement(requirement: Requirement,
                                    requirement_type: JobRequirementType,
                                    cv_text: str,
                                    app_config: AppConfig) -> str:
    minimum_score_value = app_config.generic_config.score_config.minimum_score_value
    maximum_score_value = app_config.generic_config.score_config.maximum_score_value
    return f'Please match the following requirement "{requirement.specification}" with the provided application document and fill the score and the explanation of the score in the following JSON object {dumps(get_empty_score(app_config))}. The score should be {minimum_score_value} if the requirement is completely unfulfilled and {maximum_score_value} if the requirement is fully covered. Assign a score between {minimum_score_value} and {maximum_score_value} if the requirement is only partially covered and a higher score means a higher degree of coverage. A description of the type of requirement called "{requirement_type}" is provided here: {dumps(get_job_requirement_definitions(app_config.generic_config.job_requirements_config)[requirement_type])}. Explain the chosen score with the explanation field in the JSON object. The response must contain the filled JSON object. Here is the CV for which the described requirement should be scored and explained:\n\n{cv_text.strip()}.'


def get_prompt_if_candidate_is_promising(requirement_matches: dict[str, list[RequirementMatch]], app_config: AppConfig) -> PromisingResult:
    minimum_score_value = app_config.generic_config.score_config.minimum_score_value
    maximum_score_value = app_config.generic_config.score_config.maximum_score_value
    return f'Please report if the following candidate is promising and should proceed in the application process or if the candidate is not promising. The candidate was evaluated to the various job requirements and this was the result: {dumps(requirement_matches)}. A score of {minimum_score_value} means a complete mismatch of the requirement and a score of {maximum_score_value} means a perfect match of the requirement. The higher the score, the better is the requirement matched by the candidate. Furthermore, an explanation is given and if the requirement is mandatory or optional. Please provide the answer in from of a JSON object that looks like this {dumps(get_empty_promising_result())}. Please fill in the promising field with "true" if you think the candidate is promising and with "false" otherwise. Please provide an explanation why this decision was made in the JSON return value in the respective field.'


def compute_total_score(requirement_matches: dict[str, list[RequirementMatch]], app_config: AppConfig) -> ScoreValue:
    requirement_type_weightings = get_job_requirement_weightings(app_config.generic_config.job_requirements_config)
    minimum_score_value = app_config.generic_config.score_config.minimum_score_value
    requirement_types_maximum = sum(requirement_type_weightings.values())
    present_requirement_types_maximum = sum([value for key, value in requirement_type_weightings.items() if len(requirement_matches[key]) > 0])
    if present_requirement_types_maximum == 0:
        present_requirement_types_maximum = requirement_types_maximum
    correction_factor = requirement_types_maximum / present_requirement_types_maximum
    total_score = minimum_score_value
    for requirement_type, requirement_match_list in requirement_matches.items():
        if len(requirement_match_list) == 0:
            continue
        total_score += statistics.mean(
            [x.score.value - minimum_score_value for x in requirement_match_list]
        ) * requirement_type_weightings[requirement_type] * correction_factor / requirement_types_maximum
    return total_score


def match_job_requirements_to_candidate_cv(
    job_requirements: dict[str, list[Requirement, ...]],
    candidate_cv_file_path: str,
    app_config: AppConfig
) -> ApplicantMatch:
    cv_text = get_pdf_document_text(candidate_cv_file_path, app_config)
    requirement_matches = collections.defaultdict(list)
    prompts = []
    for requirement_type in app_config.generic_config.job_requirements_config.keys():
        for requirement in job_requirements[requirement_type]:
            prompt = get_prompt_to_match_requirement(requirement, requirement_type, cv_text, app_config)
            prompts.append((requirement_type, requirement, prompt))
    prompt_answers = zip([x[0] for x in prompts], [x[1] for x in prompts], get_answer_messages([x[2] for x in prompts], app_config))
    for requirement_type, requirement, answer in prompt_answers:
        requirement_score = Score.model_validate_json(extract_json_object_string_from_string(answer.text))
        requirement_match = RequirementMatch(score=requirement_score, requirement=requirement)
        requirement_matches[requirement_type].append(requirement_match)
    answer = get_answer_message(get_prompt_if_candidate_is_promising(requirement_matches, app_config), app_config)
    promising_result = PromisingResult.model_validate_json(extract_json_object_string_from_string(answer.text))
    total_score = compute_total_score(requirement_matches, app_config)
    applicant_match = ApplicantMatch(total_score=total_score, promising_result=promising_result, requirement_matches=requirement_matches)
    return applicant_match
