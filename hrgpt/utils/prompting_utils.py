import enum
import typing

from hrgpt.utils.config_utils import get_job_requirement_definitions, AppConfigFactory
from hrgpt.utils.sample_utils import (
    get_empty_score,
    get_empty_promising_result,
    get_empty_requirements,
    get_sample_requirement,
)
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import (
    Requirement,
    JobRequirementType,
    RequirementMatch,
    RequirementType,
)


class StaticPlaceholder(enum.StrEnum):
    EMPTY_SCORE = enum.auto()
    EMPTY_PROMISING_RESULT = enum.auto()
    EMPTY_REQUIREMENTS = enum.auto()
    SAMPLE_REQUIREMENT = enum.auto()
    MINIMUM_SCORE_VALUE = enum.auto()
    MAXIMUM_SCORE_VALUE = enum.auto()
    REQUIREMENT_TYPE_OPTIONAL = enum.auto()
    REQUIREMENT_TYPE_MANDATORY = enum.auto()
    REQUIREMENT_TYPE_DEFINITIONS = enum.auto()


class DynamicPlaceholder(enum.StrEnum):
    TEXT = enum.auto()
    JOB_TEXT = enum.auto()
    CV_TEXT = enum.auto()
    REQUIREMENT_SPECIFICATION = enum.auto()
    REQUIREMENT_TYPE_NAME = enum.auto()
    REQUIREMENT_TYPE_DEFINITION = enum.auto()
    REQUIREMENT_MATCHES = enum.auto()


Placeholder = typing.Union[StaticPlaceholder, DynamicPlaceholder]

DynamicPlaceholderConfiguration = tuple[tuple[DynamicPlaceholder, str], ...]

StaticPlaceholderConfiguration = tuple[tuple[StaticPlaceholder, str], ...]

PlaceholderConfiguration = tuple[tuple[Placeholder, str], ...]


def get_static_placeholder_configuration() -> StaticPlaceholderConfiguration:
    app_config = AppConfigFactory.get_app_config()
    config: StaticPlaceholderConfiguration = ()
    for placeholder in StaticPlaceholder:
        match placeholder:
            case StaticPlaceholder.EMPTY_SCORE:
                value = dumps(get_empty_score())
            case StaticPlaceholder.EMPTY_PROMISING_RESULT:
                value = dumps(get_empty_promising_result())
            case StaticPlaceholder.EMPTY_REQUIREMENTS:
                value = dumps(get_empty_requirements())
            case StaticPlaceholder.SAMPLE_REQUIREMENT:
                value = dumps(get_sample_requirement())
            case StaticPlaceholder.MINIMUM_SCORE_VALUE:
                value = str(app_config.generic_config.score_config.minimum_score_value)
            case StaticPlaceholder.MAXIMUM_SCORE_VALUE:
                value = str(app_config.generic_config.score_config.maximum_score_value)
            case StaticPlaceholder.REQUIREMENT_TYPE_OPTIONAL:
                value = RequirementType.OPTIONAL.value
            case StaticPlaceholder.REQUIREMENT_TYPE_MANDATORY:
                value = RequirementType.MANDATORY.value
            case StaticPlaceholder.REQUIREMENT_TYPE_DEFINITIONS:
                value = dumps(
                    get_job_requirement_definitions(
                        app_config.generic_config.job_requirements_config
                    )
                )
            case _:
                raise RuntimeError
        config += ((placeholder, value),)
    return config


def create_dynamic_placeholders_from_requirement(
    requirement: Requirement,
) -> DynamicPlaceholderConfiguration:
    return ((DynamicPlaceholder.REQUIREMENT_SPECIFICATION, requirement.specification),)


def create_dynamic_placeholders_from_requirement_type(
    requirement_type: JobRequirementType,
) -> DynamicPlaceholderConfiguration:
    app_config = AppConfigFactory.get_app_config()
    return (
        (
            DynamicPlaceholder.REQUIREMENT_TYPE_NAME,
            requirement_type,
        ),
        (
            DynamicPlaceholder.REQUIREMENT_TYPE_DEFINITION,
            dumps(
                get_job_requirement_definitions(
                    app_config.generic_config.job_requirements_config
                )[requirement_type]
            ),
        ),
    )


def create_dynamic_placeholders_from_requirement_matches(
    requirement_matches: dict[JobRequirementType, list[RequirementMatch]]
) -> DynamicPlaceholderConfiguration:
    return ((DynamicPlaceholder.REQUIREMENT_MATCHES, dumps(requirement_matches)),)


def replace_placeholders(
    template_text: str,
    dynamic_placeholders: DynamicPlaceholderConfiguration = (),
) -> str:
    placeholder_configuration: PlaceholderConfiguration = (
        *get_static_placeholder_configuration(),
        *dynamic_placeholders,
    )
    replaced_text = template_text
    for placeholder_config in placeholder_configuration:
        placeholder, text = placeholder_config
        placeholder_value = f"{{{placeholder.value.upper()}}}"
        replaced_text = replaced_text.replace(placeholder_value, text.strip())
    return replaced_text
