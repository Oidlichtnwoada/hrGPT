import abc
import dataclasses
import enum
import os
import random

import pendulum


class Author(enum.Enum):
    USER = 'user'
    MODEL = 'model'
    SYSTEM = 'system'


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class ChatMessage:
    text: str
    author: Author
    creation_datetime: pendulum.DateTime
    generation_interval: pendulum.Interval


class Provider(enum.Enum):
    OPENAI = 'OPENAI'
    REPLICATE = 'REPLICATE'


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class Model:
    provider: Provider
    model_name: str


class ModelOption(enum.Enum):
    GPT_4_TURBO = Model(provider=Provider.OPENAI, model_name='gpt-4-1106-preview')
    GPT_35_TURBO = Model(provider=Provider.OPENAI, model_name='gpt-3.5-turbo-1106')
    LLAMA_2_70B_CHAT = Model(provider=Provider.REPLICATE, model_name='meta/llama-2-70b-chat')
    LLAMA_2_13B_CHAT = Model(provider=Provider.REPLICATE, model_name='meta/llama-2-13b-chat')
    LLAMA_2_7B_CHAT = Model(provider=Provider.REPLICATE, model_name='meta/llama-2-7b-chat')


def get_api_key_for_provider(provider: Provider) -> str:
    if provider == Provider.OPENAI:
        return os.getenv('OPENAI_API_KEY')
    elif provider == Provider.REPLICATE:
        return os.getenv('REPLICATE_API_KEY')
    else:
        raise ValueError


def get_model_seed() -> int:
    return random.randint(0, 2 ** 32 - 1)


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class ModelConfig:
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


DEFAULT_MODEL_CONFIG = ModelConfig(
    model=ModelOption.GPT_35_TURBO,
    presence_penalty=0,
    frequency_penalty=0,
    logit_bias={},
    choices=1,
    system_context='You are a helpful assistant.',
    debug=False,
    min_tokens=0,
    max_tokens=4096,
    top_tokens=50,
    top_probability=1,
    deterministic=True,
    stop_sequences=(),
    temperature=0,
    response_format={'type': 'json_object'}
)


def generate_user_chat_message(prompt: str, datetime: pendulum.DateTime) -> ChatMessage:
    return ChatMessage(
        text=prompt.strip(),
        author=Author.USER,
        creation_datetime=datetime,
        generation_interval=pendulum.Interval(
            datetime,
            datetime
        ))


def generate_model_chat_message(prompt: str,
                                before_datetime: pendulum.DateTime,
                                creation_datetime: pendulum.DateTime,
                                after_datetime: pendulum.DateTime) -> ChatMessage:
    return ChatMessage(
        text=prompt.strip(),
        author=Author.MODEL,
        creation_datetime=creation_datetime,
        generation_interval=pendulum.Interval(
            before_datetime,
            after_datetime
        ))


def generate_system_chat_message(prompt: str) -> ChatMessage:
    current_datetime = pendulum.DateTime.utcnow()
    return ChatMessage(
        text=prompt.strip(),
        author=Author.SYSTEM,
        creation_datetime=current_datetime,
        generation_interval=pendulum.Interval(current_datetime, current_datetime)
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
