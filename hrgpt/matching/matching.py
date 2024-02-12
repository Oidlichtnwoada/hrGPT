import collections

from hrgpt.prompting.prompting import (
    get_prompt_to_match_requirement,
    get_prompt_to_check_if_candidate_is_promising,
)
from hrgpt.utils.chat_utils import get_answer_messages, get_answer_message
from hrgpt.utils.config_utils import AppConfigFactory
from hrgpt.utils.extraction_utils import extract_json_object_from_string
from hrgpt.utils.math_utils import clamp_int
from hrgpt.utils.pdf_utils import get_pdf_document_text
from hrgpt.utils.score_utils import compute_total_score
from hrgpt.utils.timing_utils import TimingClock, TaskType
from hrgpt.utils.type_utils import (
    Score,
    PromisingResult,
    RequirementMatch,
    ApplicantMatch,
    JobRequirementType,
    Requirement,
)


def match_job_requirements_to_candidate_cv(
    job_requirements: dict[JobRequirementType, list[Requirement]],
    candidate_cv_file_path: str,
) -> ApplicantMatch:
    TimingClock.start_timer(TaskType.APPLICANT_MATCHING, candidate_cv_file_path)
    cv_text = get_pdf_document_text(candidate_cv_file_path)
    requirement_matches = collections.defaultdict(list)
    app_config = AppConfigFactory.get_app_config()
    prompts = []
    for requirement_type in app_config.generic_config.job_requirements_config.keys():
        if requirement_type not in job_requirements:
            continue
        for requirement in job_requirements[requirement_type]:
            prompt = get_prompt_to_match_requirement(
                cv_text, requirement, requirement_type
            )
            prompts.append((requirement_type, requirement, prompt))
    prompt_answers = zip(
        [x[0] for x in prompts],
        [x[1] for x in prompts],
        get_answer_messages(tuple([x[2] for x in prompts])),
    )
    for requirement_type, requirement, answer in prompt_answers:
        requirement_score = Score.model_validate(
            extract_json_object_from_string(answer.text)
        )
        requirement_score.value = clamp_int(
            requirement_score.value,
            min_value=app_config.generic_config.score_config.minimum_score_value,
            max_value=app_config.generic_config.score_config.maximum_score_value,
        )
        requirement_match = RequirementMatch(
            score=requirement_score, requirement=requirement
        )
        requirement_matches[requirement_type].append(requirement_match)
    answer = get_answer_message(
        get_prompt_to_check_if_candidate_is_promising(requirement_matches)
    )
    promising_result = PromisingResult.model_validate(
        extract_json_object_from_string(answer.text)
    )
    total_score = compute_total_score(requirement_matches)
    applicant_match = ApplicantMatch(
        total_score=total_score,
        promising_result=promising_result,
        requirement_matches=requirement_matches,
    )
    TimingClock.stop_timer(TaskType.APPLICANT_MATCHING, candidate_cv_file_path)
    return applicant_match
