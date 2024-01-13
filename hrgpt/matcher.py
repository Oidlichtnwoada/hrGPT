import collections
import dataclasses
import json
import numbers
import statistics

from hrgpt.chat.chat_factory import get_chat
from hrgpt.extraction import Requirement, get_pdf_document_text, extract_json_object_from_string

DEFAULT_REQUIREMENT_TYPE_WEIGHTINGS: dict[str, float] = {
    'work_experience': 0.25,
    'education': 0.15,
    'other_qualifications': 0.1,
    'hard_skills': 0.15,
    'soft_skills': 0.1,
    'specific_knowledge': 0.05,
    'personal_traits': 0.05,
    'languages': 0.05,
    'travel': 0.02,
    'location': 0.02,
    'working_hours': 0.03,
    'physical_ability': 0.03}


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class Score:
    score: float
    explanation: str


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class RequirementMatch:
    score: Score
    requirement: Requirement


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class PromisingResult:
    promising: bool
    explanation: str


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class ApplicantMatch:
    score: float
    promising: bool
    explanation: str
    requirement_matches: dict[str, list[RequirementMatch]]


def get_empty_score() -> Score:
    return Score(score=0, explanation='')


def get_empty_promising_result() -> PromisingResult:
    return PromisingResult(promising=False, explanation='')


def get_prompt_to_match_requirement(requirement: Requirement,
                                    requirement_type: str,
                                    requirement_type_definitions: dict[str, str],
                                    cv_text: str) -> str:
    return f'Please match the following requirement "{requirement.specification}" with the provided application document and fill the score and the explanation of the score in the following JSON object {json.dumps(dataclasses.asdict(get_empty_score()))}. The score should be 0 if the requirement is completely unfulfilled and 1 if the requirement is fully covered. Assign a score between 0 and 1 if the requirement is only partially covered and a higher score means a higher degree of coverage. A description of the type of requirement called "{requirement_type}" is provided here: {json.dumps(requirement_type_definitions[requirement_type])}. Explain the chosen score with the explanation field in the JSON object. The response must contain the filled JSON object. Here is the CV for which the described requirement should be scored and explained: {cv_text}.'


def get_prompt_if_candidate_is_promising(requirement_matches: dict[str, list[RequirementMatch]]) -> PromisingResult:
    return f'Please report if the following candidate is promising and should proceed in the application process or if the candidate is not promising. The candidate was evaluated to the various job requirements and this was the result: {json.dumps(dataclasses.asdict(requirement_matches))}. A score of 0 means a complete mismatch of the requirement and a score of 1 means a perfect match of the requirement. The higher the score, the better is the requirement matched by the candidate. Furthermore, an explanation is given and if the requirement is mandatory or optional. Please provide the answer in from of a JSON object that looks like this {json.dumps(dataclasses.asdict(get_empty_promising_result()))}. Please fill in the promising field with "true" if you think the candidate is promising and with "false" otherwise. Please provide an explanation why this decision was made in the JSON return value in the respective field.'

def compute_total_score(requirement_matches: dict[str, list[RequirementMatch]], requirement_type_weightings: dict[str, float]) -> float:
    if sum(requirement_type_weightings.values()) != 1:
        return ValueError
    present_requirement_types_maximum = sum([value for key, value in requirement_type_weightings.items() if len(requirement_matches[key]) > 0])
    correction_factor = 1 / present_requirement_types_maximum
    total_score = 0
    for requirement_type, requirement_match_list in requirement_matches.items():
        total_score += statistics.mean([x.score.score for x in requirement_match_list]) * requirement_type_weightings[requirement_type] * correction_factor
    return total_score


def match_job_requirements_to_candidate_cv(
    job_requirements: dict[str, list[Requirement, ...]],
    requirement_type_definitions: dict[str, str],
    requirement_type_weightings: dict[str, float],
    candidate_cv_file_path: str,
) -> ApplicantMatch:
    cv_text = get_pdf_document_text(candidate_cv_file_path)
    requirement_matches = collections.defaultdict(list)
    for requirement_type in requirement_type_definitions.keys():
        for requirement in job_requirements[requirement_type]:
            prompt = get_prompt_to_match_requirement(requirement, requirement_type, requirement_type_definitions, cv_text)
            chat = get_chat()
            answer = chat.send_prompt(prompt)
            extracted_json_object = extract_json_object_from_string(answer.text)
            requirement_score = dataclasses.asdict(get_empty_score())
            if 'score' in extracted_json_object and isinstance(extracted_json_object['score'], numbers.Number):
                # extract the score
                requirement_score['score'] = min(max(extracted_json_object['score'], 0), 1)
            if 'explanation' in extracted_json_object and isinstance(extracted_json_object['explanation'], str):
                # extract the explanation
                requirement_score['explanation'] = extracted_json_object['explanation']
            requirement_match = RequirementMatch(score=Score(**requirement_score), requirement=requirement)
            requirement_matches[requirement_type].append(requirement_match)
    chat = get_chat()
    answer = chat.send_prompt(get_prompt_if_candidate_is_promising(requirement_matches))
    extracted_json_object = extract_json_object_from_string(answer.text)
    promising = False
    explanation = ''
    if 'promising' in extracted_json_object and isinstance(extracted_json_object['promising'], bool):
        # extract the promising flag
        promising = extracted_json_object['promising']
    if 'explanation' in extracted_json_object and isinstance(extracted_json_object['explanation'], str):
        # extract the explanation
        explanation = extracted_json_object['explanation']
    total_score = compute_total_score(requirement_matches, requirement_type_weightings)
    applicant_match = ApplicantMatch(score=total_score, promising=promising, explanation=explanation, requirement_matches=requirement_matches)
    return applicant_match
