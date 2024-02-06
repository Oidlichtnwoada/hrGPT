from hrgpt.utils.config_utils import AppConfigFactory
from hrgpt.utils.type_utils import (
    Requirement,
    RequirementType,
    Score,
    PromisingResult,
    JobRequirementType,
)


def get_sample_requirement() -> Requirement:
    return Requirement(
        type=RequirementType.MANDATORY,
        specification="Here should stand the specification text of the requirement",
    )


def get_empty_requirements() -> dict[JobRequirementType, list[Requirement]]:
    app_config = AppConfigFactory.get_app_config()
    result_dict: dict[JobRequirementType, list[Requirement]] = {}
    for key in app_config.generic_config.job_requirements_config:
        result_dict[key] = []
    return result_dict


def get_empty_score() -> Score:
    app_config = AppConfigFactory.get_app_config()
    return Score(
        value=app_config.generic_config.score_config.minimum_score_value, explanation=""
    )


def get_empty_promising_result() -> PromisingResult:
    return PromisingResult(promising=False, explanation="")
