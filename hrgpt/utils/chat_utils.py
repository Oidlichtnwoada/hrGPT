import concurrent.futures

from hrgpt.chat.chat import Chat, ChatMessage
from hrgpt.chat.openai_chat import OpenaiChat
from hrgpt.chat.replicate_chat import ReplicateChat
from hrgpt.config.config import Provider
from hrgpt.utils.config_utils import get_model_for_model_enum, AppConfigFactory


def get_chat() -> Chat:
    config = AppConfigFactory.get_app_config()
    provider = get_model_for_model_enum(config.llm_config.model).provider
    if provider == Provider.OPENAI:
        return OpenaiChat()
    elif provider == Provider.REPLICATE:
        return ReplicateChat()
    else:
        raise ValueError


def get_answer_message(prompt: str) -> ChatMessage:
    chat = get_chat()
    return chat.send_prompt(prompt)


def get_answer_messages(prompts: tuple[str, ...]) -> tuple[ChatMessage, ...]:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return tuple(executor.map(get_answer_message, prompts))
