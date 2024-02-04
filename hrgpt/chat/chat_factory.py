import concurrent.futures
import functools

from hrgpt.chat.chat import Chat, Provider, DEFAULT_MODEL_CONFIG, ModelConfig, ChatMessage
from hrgpt.chat.openai_chat import OpenaiChat
from hrgpt.chat.replicate_chat import ReplicateChat


def get_chat(config: ModelConfig = DEFAULT_MODEL_CONFIG) -> Chat:
    if config.model.provider == Provider.OPENAI:
        return OpenaiChat(config)
    elif config.model.provider == Provider.REPLICATE:
        return ReplicateChat(config)
    else:
        raise ValueError


def get_answer_message(prompt: str, config: ModelConfig = DEFAULT_MODEL_CONFIG) -> ChatMessage:
    chat = get_chat(config)
    return chat.send_prompt(prompt)


def get_answer_messages(prompts: tuple[str, ...], config: ModelConfig = DEFAULT_MODEL_CONFIG) -> tuple[ChatMessage, ...]:
    get_answer_message_with_config = functools.partial(get_answer_message, config=config)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return tuple(executor.map(get_answer_message_with_config, prompts))
