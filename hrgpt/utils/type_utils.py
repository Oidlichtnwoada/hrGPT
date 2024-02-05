import datetime
import enum
import typing

import pydantic

JobRequirementType = typing.Literal[
    'work_experience', 'education', 'other_qualifications', 'hard_skills',
    'soft_skills', 'specific_knowledge', 'personal_traits', 'languages',
    'travel', 'location', 'working_hours', 'physical_ability']


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
