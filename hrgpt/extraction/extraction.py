import typing

from hrgpt.prompting.prompting import get_prompt_to_extract_requirements
from hrgpt.utils.chat_utils import get_answer_message
from hrgpt.utils.extraction_utils import (
    extract_json_object_from_string,
    get_document_text,
)
from hrgpt.utils.sample_utils import get_empty_requirements
from hrgpt.utils.timing_utils import TimingClock, TaskType
from hrgpt.utils.type_utils import (
    Requirement,
    VALID_JOB_REQUIREMENT_TYPES,
    JobRequirementType,
)


def get_requirements_from_job_description(
    job_description_pdf_file_path: str,
) -> dict[JobRequirementType, list[Requirement]]:
    TimingClock.start_timer(
        TaskType.REQUIREMENT_EXTRACTION, job_description_pdf_file_path
    )
    # generate the extraction prompt
    job_description_text = get_document_text(job_description_pdf_file_path)
    prompt = get_prompt_to_extract_requirements(job_description_text)
    # send the prompt to the model
    answer = get_answer_message(prompt)
    # extract the JSON object from the answer
    extracted_json_object = extract_json_object_from_string(answer.text)
    # validate the structure and transform the JSON object from the answer
    job_requirements = get_empty_requirements()
    for requirement_type, requirements in extracted_json_object.items():
        if requirement_type not in VALID_JOB_REQUIREMENT_TYPES:
            continue
        job_requirement_type = typing.cast(JobRequirementType, requirement_type)
        if job_requirement_type not in job_requirements:
            # do not add unspecified requirement types
            continue
        if not isinstance(requirements, list):
            # the requirements should be given as a list
            continue
        for requirement in requirements:
            if not isinstance(requirement, dict):
                # each requirement should be an object
                continue
            # validate the requirement
            requirement_object = Requirement.model_validate(requirement)
            # add the requirement
            job_requirements[job_requirement_type].append(requirement_object)
    TimingClock.stop_timer(
        TaskType.REQUIREMENT_EXTRACTION, job_description_pdf_file_path
    )
    return job_requirements
