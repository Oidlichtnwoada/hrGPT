import datetime
import enum
import typing

import pydantic
import typing_extensions

JobRequirementType = typing.Literal[
    "work_experience",
    "education",
    "other_qualifications",
    "hard_skills",
    "soft_skills",
    "specific_knowledge",
    "personal_traits",
    "languages",
    "travel",
    "location",
    "working_hours",
    "physical_ability",
]

VALID_JOB_REQUIREMENT_TYPES: tuple[JobRequirementType, ...] = typing.get_args(
    JobRequirementType
)


def strip_string(string: str) -> str:
    return string.strip()


StrippedString = typing.Annotated[str, pydantic.AfterValidator(strip_string)]

PositiveInt = typing.Annotated[int, pydantic.Field(ge=1)]

NonNegativeIntWithDefault = typing.Annotated[int, pydantic.Field(ge=-1)]


class RequirementType(enum.StrEnum):
    MANDATORY = enum.auto()
    OPTIONAL = enum.auto()


class Requirement(pydantic.BaseModel):
    type: RequirementType
    specification: StrippedString


ScoreValue: typing.TypeAlias = int
TotalScoreValue: typing.TypeAlias = float


class Score(pydantic.BaseModel):
    value: ScoreValue
    explanation: StrippedString


class RequirementMatch(pydantic.BaseModel):
    score: Score
    requirement: Requirement


class PromisingResult(pydantic.BaseModel):
    promising: bool
    explanation: StrippedString


class ApplicantMatch(pydantic.BaseModel):
    total_score: TotalScoreValue
    promising_result: PromisingResult
    requirement_matches: dict[JobRequirementType, list[RequirementMatch]]


class Author(enum.StrEnum):
    USER = enum.auto()
    MODEL = enum.auto()
    SYSTEM = enum.auto()


class ChatMessage(pydantic.BaseModel):
    text: StrippedString
    author: Author
    creation_datetime: datetime.datetime
    generation_timedelta: datetime.timedelta


class DocumentFileType(enum.StrEnum):
    PDF = ".pdf"
    DOCX = ".docx"
    TEXT = ".txt"


def get_supported_file_types() -> tuple[str, ...]:
    return tuple([x.value for x in DocumentFileType])


RankingPlace = typing.Literal[1, 2, 3, 4, 5, 6, 7, 8]


def check_applicant_name(name: str) -> str:
    name_parts = name.split(" ")
    assert len(name_parts) == 2
    first_name, last_name = name_parts
    assert first_name == first_name.strip()
    assert last_name == last_name.strip()
    return name


ApplicantName = typing_extensions.Annotated[
    str, pydantic.functional_validators.AfterValidator(check_applicant_name)
]

JobName: typing.TypeAlias = str


class HumanMatchingErrorResult(pydantic.BaseModel):
    human_id: int
    job_name: JobName
    promising_candidates_hamming_distance: int
    candidate_places_kendall_tau_correlation: float


class MeanHumanMatchingErrorResult(pydantic.BaseModel):
    job_name: JobName
    promising_candidates_hamming_distance: float
    candidate_places_kendall_tau_correlation: float


CompleteHumanMatchingErrorResult = dict[JobName, tuple[HumanMatchingErrorResult, ...]]


class ModelMatchingErrorResult(pydantic.BaseModel):
    job_name: JobName
    promising_candidates_hamming_distance: int
    candidate_places_kendall_tau_correlation: float


CompleteModelMatchingErrorResult = dict[JobName, ModelMatchingErrorResult]


class ModelMatchingResult(pydantic.BaseModel):
    job_name: JobName
    seconds_taken: int
    promising_candidates: set[ApplicantName]
    candidate_places: dict[RankingPlace, ApplicantName]


CompleteModelMatchingResult = dict[JobName, ModelMatchingResult]


class MeanHumanMatchingResult(pydantic.BaseModel):
    job_name: JobName
    minutes_taken: float
    promising_candidates: set[ApplicantName]
    candidate_places: dict[RankingPlace, ApplicantName]


CompleteMeanHumanMatchingResult = dict[JobName, MeanHumanMatchingResult]


def get_unique_places_amount() -> int:
    return len(typing.get_args(RankingPlace))


class HumanMatchingResult(pydantic.BaseModel):
    human_id: int
    job_name: JobName
    timestamp: datetime.datetime
    minutes_taken: int
    promising_candidates: set[ApplicantName]
    candidate_places: dict[RankingPlace, ApplicantName]

    @pydantic.model_validator(mode="after")
    def check_consistency(self) -> "HumanMatchingResult":
        unique_places_amount = get_unique_places_amount()
        unique_places = set(self.candidate_places.keys())
        unique_applicants = set(self.candidate_places.values())
        assert len(unique_places) == unique_places_amount
        assert len(unique_applicants) == unique_places_amount
        assert self.promising_candidates.issubset(unique_applicants)
        promising_candidates_amount = len(self.promising_candidates)
        promising_candidates_according_to_ranking = set(
            [
                self.candidate_places[typing.cast(RankingPlace, place)]
                for place in range(1, promising_candidates_amount + 1)
            ]
        )
        assert self.promising_candidates == promising_candidates_according_to_ranking
        return self


CompleteHumanMatchingResult = dict[JobName, tuple[HumanMatchingResult, ...]]


class HumanMatchingEvaluation(pydantic.BaseModel):
    human_results: tuple[HumanMatchingResult, ...]
    human_error_results: tuple[HumanMatchingErrorResult, ...]


class ModelMatchingEvaluation(pydantic.BaseModel):
    ai_model_result: ModelMatchingResult
    ai_model_error_result: ModelMatchingErrorResult


class MeanHumanMatchingEvaluation(pydantic.BaseModel):
    mean_human_result: MeanHumanMatchingResult
    mean_human_error_result: MeanHumanMatchingErrorResult


class ModelMetrics(pydantic.BaseModel):
    ai_model_ranking_better_or_equal_than_human_percentage: float
    ai_model_categorization_better_or_equal_than_human_percentage: float
    time_savings_percentage: float
    candidates_filtered_by_model: int | float
    filter_accuracy: float


class JobMatchingResult(pydantic.BaseModel):
    job_name: JobName
    mean_human_evaluation: MeanHumanMatchingEvaluation
    human_matching_evaluation: HumanMatchingEvaluation
    ai_model_matching_evaluation: ModelMatchingEvaluation
    ai_model_metrics: ModelMetrics


class MergedMetrics(pydantic.BaseModel):
    human_promising_candidates_hamming_distance: float
    human_candidate_places_kendall_tau_correlation: float
    ai_model_promising_candidates_hamming_distance: float
    ai_model_candidate_places_kendall_tau_correlation: float
    ai_model_metrics: ModelMetrics


class MatchingResult(pydantic.BaseModel):
    matching_result: dict[JobName, JobMatchingResult]
    merged_metrics: MergedMetrics
