import enum
import typing

import pydantic
import typing_extensions

from hrgpt.utils.type_utils import StrippedString, PositiveInt, NonNegativeIntWithDefault

JobRequirementType = typing.Literal[
    'work_experience', 'education', 'other_qualifications', 'hard_skills',
    'soft_skills', 'specific_knowledge', 'personal_traits', 'languages',
    'travel', 'location', 'working_hours', 'physical_ability']

WeightingFloat = typing.Annotated[float, pydantic.Field(gt=0)]


class JobRequirementConfig(pydantic.BaseModel):
    definition: StrippedString
    weighting: WeightingFloat


JobRequirementDict = typing.Dict[JobRequirementType, JobRequirementConfig]
JobRequirementDefinitions = typing.Dict[JobRequirementType, StrippedString]
JobRequirementWeightings = typing.Dict[JobRequirementType, WeightingFloat]


class Provider(enum.StrEnum):
    OPENAI = enum.auto()
    REPLICATE = enum.auto()


class Model(pydantic.BaseModel):
    provider: Provider
    name: StrippedString


class ModelEnum(enum.StrEnum):
    GPT_4_TURBO = enum.auto()
    GPT_35_TURBO = enum.auto()
    LLAMA_2_70B_CHAT = enum.auto()
    LLAMA_2_13B_CHAT = enum.auto()
    LLAMA_2_7B_CHAT = enum.auto()


FrequencyPenaltyFloat = typing.Annotated[float, pydantic.Field(ge=-2.0, le=2.0)]
PresencePenaltyFloat = typing.Annotated[float, pydantic.Field(ge=-2.0, le=2.0)]
TopProbabilityFloat = typing.Annotated[float, pydantic.Field(ge=0.0, le=1.0)]
TemperatureFloat = typing.Annotated[float, pydantic.Field(ge=0.0, le=2.0)]
RepetitionPenaltyFloat = typing.Annotated[float, pydantic.Field(ge=0.0, le=2.0)]
TokenId: typing.TypeAlias = int
BiasValueFloat = typing.Annotated[float, pydantic.Field(ge=-100.0, le=100.0)]
MaxTokensInt = typing.Annotated[PositiveInt, pydantic.Field(le=4096)]


class ResponseFormatDict(typing_extensions.TypedDict):
    type: typing.Literal["text", "json_object"]


class ModelConfiguration(pydantic.BaseModel):
    model: ModelEnum
    presence_penalty: PresencePenaltyFloat
    logit_bias: dict[TokenId, BiasValueFloat]
    frequency_penalty: FrequencyPenaltyFloat
    choices: PositiveInt
    system_context: StrippedString
    debug: bool
    min_tokens: NonNegativeIntWithDefault
    max_tokens: MaxTokensInt
    top_tokens: PositiveInt
    top_probability: TopProbabilityFloat
    deterministic: bool
    stop_sequences: tuple[StrippedString, ...]
    temperature: TemperatureFloat
    response_format: ResponseFormatDict
    repetition_penalty: RepetitionPenaltyFloat


NonEmptyJobRequirementDict = typing.Annotated[JobRequirementDict, pydantic.Field(min_length=1)]


class ScoreConfiguration(pydantic.BaseModel):
    minimum_score_value: float
    maximum_score_value: float


class PolarsConfiguration(pydantic.BaseModel):
    max_print_string_length: PositiveInt
    disable_shape_print: bool


LogLevel = typing.Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]


class LoggingConfiguration(pydantic.BaseModel):
    root_logging_level: LogLevel
    application_logging_level: LogLevel


class NetworkConfiguration(pydantic.BaseModel):
    retry_amount: PositiveInt


class GenericConfiguration(pydantic.BaseModel):
    score_config: ScoreConfiguration
    polars_config: PolarsConfiguration
    logging_config: LoggingConfiguration
    network_config: NetworkConfiguration
    job_requirements_config: NonEmptyJobRequirementDict


class EnvironmentSecrets(pydantic.BaseModel):
    openai_api_key: str
    replicate_api_key: str
    aspose_app_key: str
    aspose_app_sid: str


class AppConfig(pydantic.BaseModel):
    llm_config: ModelConfiguration
    generic_config: GenericConfiguration
    secrets: EnvironmentSecrets
