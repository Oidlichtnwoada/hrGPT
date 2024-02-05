from hrgpt.config.config import AppConfig, JobRequirementType
from hrgpt.utils.type_utils import Requirement, RequirementType


def get_sample_requirement() -> Requirement:
    return Requirement(type=RequirementType.MANDATORY, specification='Here should stand the specification text of the requirement')


def get_empty_requirements(app_config: AppConfig) -> dict[JobRequirementType, list[Requirement, ...]]:
    result_dict = {}
    for key in app_config.generic_config.job_requirements_config:
        result_dict[key] = []
    return result_dict
