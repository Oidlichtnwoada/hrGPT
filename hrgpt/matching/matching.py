import collections
import statistics

from hrgpt.chat.chat_factory import get_answer_messages, get_answer_message
from hrgpt.config.config import AppConfig, get_job_requirement_weightings
from hrgpt.extraction.extraction import Requirement, get_pdf_document_text, extract_json_object_string_from_string
from hrgpt.prompting.prompting import get_prompt_to_match_requirement, get_prompt_to_check_if_candidate_is_promising
from hrgpt.utils.type_utils import Score, PromisingResult, RequirementMatch, ScoreValue, ApplicantMatch


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
    answer = get_answer_message(get_prompt_to_check_if_candidate_is_promising(requirement_matches, app_config), app_config)
    promising_result = PromisingResult.model_validate_json(extract_json_object_string_from_string(answer.text))
    total_score = compute_total_score(requirement_matches, app_config)
    applicant_match = ApplicantMatch(total_score=total_score, promising_result=promising_result, requirement_matches=requirement_matches)
    return applicant_match
