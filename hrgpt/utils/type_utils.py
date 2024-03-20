import datetime
import enum
import typing

import pydantic

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


class HumanMatchingResult(pydantic.BaseModel):
    human_id: int
    job_name: str
    timestamp: datetime.datetime
    minutes_taken: int
    promising_candidates: set[str]
    candidate_places: dict[RankingPlace, str]

    @pydantic.model_validator(mode="after")
    def check_consistency(self) -> "HumanMatchingResult":
        unique_places_amount = len(typing.get_args(RankingPlace))
        unique_places = set(self.candidate_places.keys())
        unique_applicants = set(self.candidate_places.values())
        assert len(unique_places) == unique_places_amount
        assert len(unique_applicants) == unique_places_amount
        assert self.promising_candidates.issubset(unique_applicants)
        promising_candidates_amount = len(self.promising_candidates)
        promising_candidates_according_to_ranking = set(
            [
                self.candidate_places[place]
                for place in range(1, promising_candidates_amount + 1)
            ]
        )
        assert self.promising_candidates == promising_candidates_according_to_ranking
        return self
