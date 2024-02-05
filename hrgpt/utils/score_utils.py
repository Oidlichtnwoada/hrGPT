import statistics

from hrgpt.config.config import JobRequirementType, AppConfigFactory
from hrgpt.utils.config_utils import get_job_requirement_weightings
from hrgpt.utils.type_utils import RequirementMatch, TotalScoreValue


def compute_total_score(requirement_matches: dict[JobRequirementType, list[RequirementMatch]]) -> TotalScoreValue:
    app_config = AppConfigFactory.get_app_config()
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
