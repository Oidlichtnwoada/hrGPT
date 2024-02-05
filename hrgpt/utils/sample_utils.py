from hrgpt.config.config import AppConfig, JobRequirementType
from hrgpt.utils.type_utils import Requirement, RequirementType, Score, PromisingResult


def get_sample_requirement() -> Requirement:
    return Requirement(type=RequirementType.MANDATORY, specification='Here should stand the specification text of the requirement')


def get_empty_requirements(app_config: AppConfig) -> dict[JobRequirementType, list[Requirement, ...]]:
    result_dict = {}
    for key in app_config.generic_config.job_requirements_config:
        result_dict[key] = []
    return result_dict


def get_empty_score(app_config: AppConfig) -> Score:
    return Score(value=app_config.generic_config.score_config.minimum_score_value, explanation='')


def get_empty_promising_result() -> PromisingResult:
    return PromisingResult(promising=False, explanation='')
