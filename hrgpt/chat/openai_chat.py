import datetime
import enum
import functools

import openai
import pydantic

from hrgpt.chat.chat import Chat
from hrgpt.config.config import AppConfig, Provider
from hrgpt.utils.config_utils import get_temperature, get_seed, get_top_probability, get_model_for_model_enum
from hrgpt.utils.message_utils import generate_user_chat_message, generate_model_chat_message
from hrgpt.utils.secret_utils import get_api_key_for_provider
from hrgpt.utils.type_utils import StrippedString, ChatMessage, Author


class OpenaiRole(enum.StrEnum):
    USER = enum.auto()
    ASSISTANT = enum.auto()
    SYSTEM = enum.auto()


class OpenaiChatMessage(pydantic.BaseModel):
    role: OpenaiRole
    content: StrippedString


def transform_chat_message_to_openai_chat_message(chat_message: ChatMessage) -> OpenaiChatMessage:
    if chat_message.author == Author.USER:
        role = OpenaiRole.USER
    elif chat_message.author == Author.SYSTEM:
        role = OpenaiRole.SYSTEM
    elif chat_message.author == Author.MODEL:
        role = OpenaiRole.ASSISTANT
    else:
        raise ValueError
    return OpenaiChatMessage(role=role, content=chat_message.text)


class OpenaiChat(Chat):
    def __init__(self, config: AppConfig) -> None:
        if get_model_for_model_enum(config.llm_config.model).provider != Provider.OPENAI:
            raise ValueError
        super().__init__(config.llm_config.system_context)
        self.config = config
        self.openai = openai.OpenAI(
            api_key=get_api_key_for_provider(self.config),
            max_retries=self.config.generic_config.network_config.retry_amount
        )

    def send_prompt(self, prompt: str) -> ChatMessage:
        before_datetime = datetime.datetime.now(datetime.timezone.utc)
        user_chat_message = generate_user_chat_message(prompt, before_datetime)
        self.chat_message_history += (user_chat_message,)
        model_response = self.openai.chat.completions.create(
            model=get_model_for_model_enum(self.config.llm_config.model).name,
            messages=list(map(functools.partial(pydantic.BaseModel.model_dump, mode='json'),
                              map(transform_chat_message_to_openai_chat_message, self.chat_message_history))),
            temperature=get_temperature(self.config.llm_config.deterministic, self.config.llm_config.temperature),
            stop=self.config.llm_config.stop_sequences,
            seed=get_seed(self.config.llm_config.deterministic),
            top_p=get_top_probability(self.config.llm_config.deterministic, self.config.llm_config.top_probability),
            max_tokens=self.config.llm_config.max_tokens,
            n=self.config.llm_config.choices,
            frequency_penalty=self.config.llm_config.frequency_penalty,
            logit_bias=self.config.llm_config.logit_bias,
            presence_penalty=self.config.llm_config.presence_penalty,
            response_format=self.config.llm_config.response_format,
        )
        after_datetime = datetime.datetime.now(datetime.timezone.utc)
        model_response_choice = model_response.choices[0]
        if model_response_choice.message.content is None or model_response_choice.finish_reason != 'stop':
            raise RuntimeError
        creation_datetime = datetime.datetime.fromtimestamp(model_response.created, datetime.timezone.utc)
        model_chat_message = generate_model_chat_message(model_response_choice.message.content,
                                                         before_datetime,
                                                         creation_datetime,
                                                         after_datetime)
        self.chat_message_history += (model_chat_message,)
        return model_chat_message
