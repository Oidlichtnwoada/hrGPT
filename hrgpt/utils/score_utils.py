import statistics

from hrgpt.config.config import JobRequirementType
from hrgpt.utils.config_utils import get_job_requirement_weightings, AppConfigFactory
from hrgpt.utils.math_utils import clamp_int
from hrgpt.utils.type_utils import RequirementMatch, TotalScoreValue


def compute_total_score(
    requirement_matches: dict[JobRequirementType, list[RequirementMatch]]
) -> TotalScoreValue:
    app_config = AppConfigFactory.get_app_config()
    requirement_type_weightings = get_job_requirement_weightings(
        app_config.generic_config.job_requirements_config
    )
    minimum_score_value = app_config.generic_config.score_config.minimum_score_value
    maximum_score_value = app_config.generic_config.score_config.maximum_score_value
    present_requirement_types_maximum = sum(
        [
            value
            for key, value in requirement_type_weightings.items()
            if key in requirement_matches and len(requirement_matches[key]) > 0
        ]
    )
    if present_requirement_types_maximum == 0:
        present_requirement_types_maximum = sum(requirement_type_weightings.values())
    total_score = float(minimum_score_value)
    for requirement_type, requirement_match_list in requirement_matches.items():
        if len(requirement_match_list) == 0:
            continue
        score_values = [x.score.value for x in requirement_match_list]
        for score_value in score_values:
            if score_value != clamp_int(
                score_value,
                min_value=minimum_score_value,
                max_value=maximum_score_value,
            ):
                raise ValueError
        total_score += (
            statistics.mean([x - minimum_score_value for x in score_values])
            * requirement_type_weightings[requirement_type]
            / present_requirement_types_maximum
        )
    return total_score
