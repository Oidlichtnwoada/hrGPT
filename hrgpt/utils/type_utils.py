import enum
import typing

import pydantic


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


ScoreValue: typing.TypeAlias = float


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
    total_score: ScoreValue
    promising_result: PromisingResult
    requirement_matches: dict[str, list[RequirementMatch]]
