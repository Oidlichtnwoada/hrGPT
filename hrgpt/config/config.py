import enum
import typing

import pydantic
import typing_extensions

from hrgpt.utils.type_utils import (
    StrippedString,
    PositiveInt,
    NonNegativeIntWithDefault,
    JobRequirementType,
    ScoreValue,
)

WeightingInt = typing.Annotated[int, pydantic.Field(gt=0)]


class JobRequirementConfig(pydantic.BaseModel):
    definition: StrippedString
    weighting: WeightingInt


JobRequirementDict = typing.Dict[JobRequirementType, JobRequirementConfig]
JobRequirementDefinitions = typing.Dict[JobRequirementType, StrippedString]
JobRequirementWeightings = typing.Dict[JobRequirementType, WeightingInt]


class Provider(enum.StrEnum):
    OPENAI = enum.auto()
    REPLICATE = enum.auto()
    GOOGLE = enum.auto()


class Model(pydantic.BaseModel):
    provider: Provider
    name: StrippedString


class ModelEnum(enum.StrEnum):
    GPT_4_TURBO = enum.auto()
    GPT_4O = enum.auto()
    GPT_35_TURBO = enum.auto()
    LLAMA_3_70B_INSTRUCT = enum.auto()
    LLAMA_3_8B_INSTRUCT = enum.auto()
    GEMINI_15_PRO = enum.auto()
    GEMINI_15_FLASH = enum.auto()


FrequencyPenaltyFloat = typing.Annotated[float, pydantic.Field(ge=-2.0, le=2.0)]
PresencePenaltyFloat = typing.Annotated[float, pydantic.Field(ge=-2.0, le=2.0)]
TopProbabilityFloat = typing.Annotated[float, pydantic.Field(ge=0.0, le=1.0)]
TemperatureFloat = typing.Annotated[float, pydantic.Field(ge=0.0, le=5.0)]
RepetitionPenaltyFloat = typing.Annotated[float, pydantic.Field(ge=0.0, le=2.0)]
TokenId: typing.TypeAlias = str
BiasValueInt = typing.Annotated[int, pydantic.Field(ge=-100, le=100)]
MaxTokensInt = typing.Annotated[PositiveInt, pydantic.Field(le=4096)]


class ResponseFormatDict(typing_extensions.TypedDict, total=False):
    type: typing.Literal["text", "json_object"]


class ModelConfiguration(pydantic.BaseModel):
    model: ModelEnum
    presence_penalty: PresencePenaltyFloat
    logit_bias: dict[TokenId, BiasValueInt]
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


NonEmptyJobRequirementDict = typing.Annotated[
    JobRequirementDict, pydantic.Field(min_length=1)
]


class PrettifyConfiguration(pydantic.BaseModel):
    enable_llm_prettification: bool


class ScoreConfiguration(pydantic.BaseModel):
    minimum_score_value: ScoreValue
    maximum_score_value: ScoreValue


class PolarsConfiguration(pydantic.BaseModel):
    max_print_string_length: PositiveInt
    max_print_table_width: PositiveInt
    max_print_columns_amount: PositiveInt
    disable_shape_print: bool


LogLevel = typing.Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]


class LoggingConfiguration(pydantic.BaseModel):
    root_logging_level: LogLevel
    application_logging_level: LogLevel
    loggers_to_disable_propagation: tuple[str, ...]


class NetworkConfiguration(pydantic.BaseModel):
    retry_amount: PositiveInt


class PromptConfiguration(pydantic.BaseModel):
    prettify_text_prompt: StrippedString
    extract_requirements_prompt: StrippedString
    match_requirement_prompt: StrippedString
    check_if_candidate_is_promising_prompt: StrippedString


class LanguageConfiguration(pydantic.BaseModel):
    output_language: StrippedString


class GenericConfiguration(pydantic.BaseModel):
    prettify_config: PrettifyConfiguration
    score_config: ScoreConfiguration
    polars_config: PolarsConfiguration
    logging_config: LoggingConfiguration
    network_config: NetworkConfiguration
    job_requirements_config: NonEmptyJobRequirementDict
    prompt_config: PromptConfiguration
    language_config: LanguageConfiguration


class GoogleServiceAccount(pydantic.BaseModel):
    type: StrippedString
    project_id: StrippedString
    private_key_id: StrippedString
    private_key: StrippedString
    client_email: StrippedString
    client_id: StrippedString
    auth_uri: StrippedString
    token_uri: StrippedString
    auth_provider_x509_cert_url: StrippedString
    client_x509_cert_url: StrippedString
    universe_domain: StrippedString


class EnvironmentSecrets(pydantic.BaseModel):
    openai_api_key: str
    replicate_api_key: str
    google_api_key: str
    aspose_app_key: str
    aspose_app_sid: str
    google_translate_service_account: GoogleServiceAccount


class AppConfig(pydantic.BaseModel):
    llm_config: ModelConfiguration
    generic_config: GenericConfiguration
    secrets: EnvironmentSecrets
