import concurrent.futures
import dataclasses

from hrgpt.chat.chat import Chat, Provider, DEFAULT_MODEL_CONFIG, ModelConfig, ChatMessage
from hrgpt.chat.openai_chat import OpenaiChat
from hrgpt.chat.replicate_chat import ReplicateChat


def get_chat(**kwargs: dict) -> Chat:
    config = DEFAULT_MODEL_CONFIG
    config_dict = dict((field.name, getattr(config, field.name)) for field in dataclasses.fields(config))
    for key, value in kwargs.items():
        config_dict[key] = value
    config = ModelConfig(**config_dict)
    if config.model.provider == Provider.OPENAI:
        return OpenaiChat(config)
    elif config.model.provider == Provider.REPLICATE:
        return ReplicateChat(config)
    else:
        raise ValueError


def get_answer_message(prompt: str, **kwargs: dict) -> ChatMessage:
    chat = get_chat(**kwargs)
    return chat.send_prompt(prompt)


def get_answer_messages(prompts: tuple[str, ...], **kwargs: dict) -> tuple[ChatMessage, ...]:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return tuple(executor.map(get_answer_message, prompts, **kwargs))
