import json
import random

from hrgpt.config.config import TopProbabilityFloat, TemperatureFloat, JobRequirementDict, JobRequirementDefinitions, ModelEnum, Model, Provider, AppConfig
from hrgpt.utils.type_utils import PositiveInt


def get_random_seed() -> int:
    return random.randint(0, 2 ** 32 - 1)


def get_deterministic_seed() -> int:
    return 42


def get_seed(deterministic: bool) -> int:
    if deterministic:
        return get_deterministic_seed()
    else:
        return get_random_seed()


def get_temperature(deterministic: bool, temperature: TemperatureFloat) -> TemperatureFloat:
    if deterministic:
        return 0
    else:
        return temperature


def get_top_tokens(deterministic: bool, top_tokens: PositiveInt) -> PositiveInt:
    if deterministic:
        return 1
    else:
        return top_tokens


def get_top_probability(deterministic: bool, top_probability: TopProbabilityFloat) -> TopProbabilityFloat:
    if deterministic:
        return 0
    else:
        return top_probability


def get_job_requirement_definitions(job_requirement_dict: JobRequirementDict) -> JobRequirementDefinitions:
    job_requirement_definitions = {}
    for key, value in job_requirement_dict.items():
        job_requirement_definitions[key] = value.definition
    return job_requirement_definitions


def get_job_requirement_weightings(job_requirement_dict: JobRequirementDict) -> JobRequirementDefinitions:
    job_requirement_weightings = {}
    for key, value in job_requirement_dict.items():
        job_requirement_weightings[key] = value.weighting
    return job_requirement_weightings


def get_model_for_model_enum(value: ModelEnum) -> Model:
    match value:
        case ModelEnum.GPT_4_TURBO:
            return Model(provider=Provider.OPENAI, name='gpt-4-0125-preview')
        case ModelEnum.GPT_35_TURBO:
            return Model(provider=Provider.OPENAI, name='gpt-3.5-turbo-0125')
        case ModelEnum.LLAMA_2_70B_CHAT:
            return Model(provider=Provider.REPLICATE, name='meta/llama-2-70b-chat')
        case ModelEnum.LLAMA_2_13B_CHAT:
            return Model(provider=Provider.REPLICATE, name='meta/llama-2-13b-chat')
        case ModelEnum.LLAMA_2_7B_CHAT:
            return Model(provider=Provider.REPLICATE, name='meta/llama-2-7b-chat')


def get_app_config_from_json_file(config_json_file_path: str, secrets_json_file_path: str) -> AppConfig:
    with open(secrets_json_file_path) as file:
        secrets_dict = {'secrets': json.loads(file.read())}
    with open(config_json_file_path) as file:
        config_dict = json.loads(file.read())
    app_config = config_dict | secrets_dict
    return AppConfig.model_validate(app_config)
