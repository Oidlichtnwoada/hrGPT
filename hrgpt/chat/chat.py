import abc
import datetime
import enum
import random
import typing

import pydantic

from hrgpt.config.config import Provider, TemperatureFloat, TopProbabilityFloat, AppConfig, get_model_for_model_enum
from hrgpt.utils.type_utils import StrippedString, PositiveInt


class Author(enum.StrEnum):
    USER = enum.auto()
    MODEL = enum.auto()
    SYSTEM = enum.auto()


class ChatMessage(pydantic.BaseModel):
    text: StrippedString
    author: Author
    creation_datetime: datetime.datetime
    generation_timedelta: datetime.timedelta


def get_api_key_for_provider(app_config: AppConfig) -> str:
    api_key: typing.Optional[str] = None
    provider = get_model_for_model_enum(app_config.llm_config.model).provider
    if provider == Provider.OPENAI:
        api_key = app_config.secrets.openai_api_key
    elif provider == Provider.REPLICATE:
        api_key = app_config.secrets.replicate_api_key
    if api_key is None:
        raise RuntimeError
    return api_key


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

    def get_context(self) -> StrippedString:
        system_chat_messages = [x for x in self.chat_message_history if x.author == Author.SYSTEM]
        if len(system_chat_messages) == 0:
            raise RuntimeError
        system_chat_message = system_chat_messages[0]
        return system_chat_message.text
