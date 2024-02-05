import collections

from hrgpt.config.config import AppConfig, JobRequirementType
from hrgpt.extraction.extraction import Requirement, extract_json_object_string_from_string
from hrgpt.prompting.prompting import get_prompt_to_match_requirement, get_prompt_to_check_if_candidate_is_promising
from hrgpt.utils.chat_utils import get_answer_messages, get_answer_message
from hrgpt.utils.pdf_utils import get_pdf_document_text
from hrgpt.utils.score_utils import compute_total_score
from hrgpt.utils.type_utils import Score, PromisingResult, RequirementMatch, ApplicantMatch


def match_job_requirements_to_candidate_cv(
    job_requirements: dict[JobRequirementType, list[Requirement, ...]],
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
