from hrgpt.utils.config_utils import AppConfigFactory
from hrgpt.utils.prompting_utils import (
    replace_placeholders,
    DynamicPlaceholder,
    create_dynamic_placeholders_from_requirement_matches,
    create_dynamic_placeholders_from_requirement,
    create_dynamic_placeholders_from_requirement_type,
)
from hrgpt.utils.type_utils import (
    Requirement,
    RequirementMatch,
    JobRequirementType,
)


def get_prompt_to_prettify_text(text: str) -> str:
    app_config = AppConfigFactory.get_app_config()
    return replace_placeholders(
        app_config.generic_config.prompt_config.prettify_text_prompt,
        dynamic_placeholders=((DynamicPlaceholder.TEXT, text),),
    )


def get_prompt_to_extract_requirements(job_text: str) -> str:
    app_config = AppConfigFactory.get_app_config()
    return replace_placeholders(
        app_config.generic_config.prompt_config.extract_requirements_prompt,
        dynamic_placeholders=((DynamicPlaceholder.JOB_TEXT, job_text),),
    )


def get_prompt_to_match_requirement(
    cv_text: str,
    requirement: Requirement,
    requirement_type: JobRequirementType,
) -> str:
    app_config = AppConfigFactory.get_app_config()
    return replace_placeholders(
        app_config.generic_config.prompt_config.match_requirement_prompt,
        dynamic_placeholders=(
            (DynamicPlaceholder.CV_TEXT, cv_text),
            *create_dynamic_placeholders_from_requirement(requirement),
            *create_dynamic_placeholders_from_requirement_type(requirement_type),
        ),
    )


def get_prompt_to_check_if_candidate_is_promising(
    requirement_matches: dict[JobRequirementType, list[RequirementMatch]]
) -> str:
    app_config = AppConfigFactory.get_app_config()
    return replace_placeholders(
        app_config.generic_config.prompt_config.check_if_candidate_is_promising_prompt,
        dynamic_placeholders=(
            *create_dynamic_placeholders_from_requirement_matches(requirement_matches),
        ),
    )
