import abc
import datetime
import enum
import os
import random

import pydantic

DEFAULT_RETRY_LIMIT = 1_000_000


class Author(enum.StrEnum):
    USER = enum.auto()
    MODEL = enum.auto()
    SYSTEM = enum.auto()


class ChatMessage(pydantic.BaseModel):
    text: str
    author: Author
    creation_datetime: datetime.datetime
    generation_timedelta: datetime.timedelta


class Provider(enum.StrEnum):
    OPENAI = enum.auto()
    REPLICATE = enum.auto()


class Model(pydantic.BaseModel):
    provider: Provider
    name: str


class ModelOption(enum.Enum):
    GPT_4_TURBO = Model(provider=Provider.OPENAI, name='gpt-4-0125-preview')
    GPT_35_TURBO = Model(provider=Provider.OPENAI, name='gpt-3.5-turbo-0125')
    LLAMA_2_70B_CHAT = Model(provider=Provider.REPLICATE, name='meta/llama-2-70b-chat')
    LLAMA_2_13B_CHAT = Model(provider=Provider.REPLICATE, name='meta/llama-2-13b-chat')
    LLAMA_2_7B_CHAT = Model(provider=Provider.REPLICATE, name='meta/llama-2-7b-chat')


def get_api_key_for_provider(provider: Provider) -> str:
    if provider == Provider.OPENAI:
        return os.getenv('OPENAI_API_KEY')
    elif provider == Provider.REPLICATE:
        return os.getenv('REPLICATE_API_KEY')
    else:
        raise ValueError


def get_random_seed() -> int:
    return random.randint(0, 2 ** 32 - 1)


def get_deterministic_seed() -> int:
    return 42


def get_seed(deterministic: bool) -> int:
    if deterministic:
        return get_deterministic_seed()
    else:
        return get_random_seed()


def get_temperature(deterministic: bool, temperature: float) -> float:
    if deterministic:
        return 0
    else:
        return temperature


def get_top_tokens(deterministic: bool, top_tokens: int) -> int:
    if deterministic:
        return 1
    else:
        return top_tokens


def get_top_probability(deterministic: bool, top_probability: float) -> float:
    if deterministic:
        return 0
    else:
        return top_probability


class ModelConfig(pydantic.BaseModel):
    model: Model
    presence_penalty: int
    logit_bias: dict
    frequency_penalty: int
    choices: int
    system_context: str
    debug: bool
    min_tokens: int
    max_tokens: int
    top_tokens: int
    top_probability: float
    deterministic: bool
    stop_sequences: tuple[str, ...]
    temperature: float
    response_format: dict
    repetition_penalty: float


DEFAULT_MODEL_CONFIG = ModelConfig(
    model=ModelOption.GPT_35_TURBO.value,
    debug=False,
    choices=1,
    presence_penalty=0,
    frequency_penalty=0,
    repetition_penalty=1,
    logit_bias={},
    system_context='You are a helpful assistant.',
    min_tokens=-1,
    max_tokens=4096,
    stop_sequences=(),
    response_format={'type': 'text'},
    top_tokens=1,
    top_probability=0,
    deterministic=True,
    temperature=0,
)


def generate_user_chat_message(prompt: str, datetime_value: datetime.datetime) -> ChatMessage:
    return ChatMessage(
        text=prompt.strip(),
        author=Author.USER,
        creation_datetime=datetime_value,
        generation_timedelta=datetime_value - datetime_value)


def generate_model_chat_message(prompt: str,
                                before_datetime: datetime.datetime,
                                creation_datetime: datetime.datetime,
                                after_datetime: datetime.datetime) -> ChatMessage:
    return ChatMessage(
        text=prompt.strip(),
        author=Author.MODEL,
        creation_datetime=creation_datetime,
        generation_timedelta=after_datetime - before_datetime)


def generate_system_chat_message(prompt: str) -> ChatMessage:
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    return ChatMessage(
        text=prompt.strip(),
        author=Author.SYSTEM,
        creation_datetime=current_datetime,
        generation_timedelta=current_datetime - current_datetime
    )


class Chat(abc.ABC):
    def __init__(self, context: str) -> None:
        self.chat_message_history: tuple[ChatMessage] = ()
        self.set_context(context)

    @abc.abstractmethod
    def send_prompt(self, prompt: str) -> ChatMessage:
        pass

    def get_chat_message_history(self, include_context: bool = False) -> tuple[ChatMessage]:
        return tuple([x for x in self.chat_message_history if include_context or x.author != Author.SYSTEM])

    def set_context(self, context: str) -> None:
        if len(self.chat_message_history) > 0:
            return
        self.chat_message_history += (generate_system_chat_message(context),)

    def get_context(self) -> str:
        system_chat_messages = [x for x in self.chat_message_history if x.author == Author.SYSTEM]
        if len(system_chat_messages) == 0:
            raise RuntimeError
        system_chat_message = system_chat_messages[0]
        return system_chat_message.text
