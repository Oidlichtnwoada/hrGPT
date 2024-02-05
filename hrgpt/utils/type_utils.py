import typing

import pydantic


def strip_string(string: str) -> str:
    return string.strip()


StrippedString = typing.Annotated[str, pydantic.AfterValidator(strip_string)]

PositiveInt = typing.Annotated[int, pydantic.Field(ge=1)]

NonNegativeIntWithDefault = typing.Annotated[int, pydantic.Field(ge=-1)]
