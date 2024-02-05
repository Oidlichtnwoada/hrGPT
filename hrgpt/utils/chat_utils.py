import concurrent.futures
import functools

from hrgpt.chat.chat import Chat, ChatMessage
from hrgpt.chat.openai_chat import OpenaiChat
from hrgpt.chat.replicate_chat import ReplicateChat
from hrgpt.config.config import AppConfig, Provider
from hrgpt.utils.config_utils import get_model_for_model_enum


def get_chat(config: AppConfig) -> Chat:
    provider = get_model_for_model_enum(config.llm_config.model).provider
    if provider == Provider.OPENAI:
        return OpenaiChat(config)
    elif provider == Provider.REPLICATE:
        return ReplicateChat(config)
    else:
        raise ValueError


def get_answer_message(prompt: str, config: AppConfig) -> ChatMessage:
    chat = get_chat(config)
    return chat.send_prompt(prompt)


def get_answer_messages(prompts: tuple[str, ...], config: AppConfig) -> tuple[ChatMessage, ...]:
    get_answer_message_with_config = functools.partial(get_answer_message, config=config)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return tuple(executor.map(get_answer_message_with_config, prompts))
