import datetime
import enum
import functools

import openai
import pydantic

from hrgpt.chat.chat import Chat, ChatMessage, ModelConfig, get_api_key_for_provider, \
    Author, Provider, generate_user_chat_message, generate_model_chat_message, get_seed, get_temperature, get_top_probability, DEFAULT_RETRY_LIMIT


class OpenaiRole(enum.StrEnum):
    USER = enum.auto()
    ASSISTANT = enum.auto()
    SYSTEM = enum.auto()


class OpenaiChatMessage(pydantic.BaseModel):
    role: OpenaiRole
    content: str


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
    def __init__(self, config: ModelConfig) -> None:
        if config.model.provider != Provider.OPENAI:
            raise ValueError
        super().__init__(config.system_context)
        self.config = config
        self.openai = openai.OpenAI(
            api_key=get_api_key_for_provider(self.config.model.provider),
            max_retries=DEFAULT_RETRY_LIMIT,
        )

    def send_prompt(self, prompt: str) -> ChatMessage:
        before_datetime = datetime.datetime.now(datetime.timezone.utc)
        user_chat_message = generate_user_chat_message(prompt, before_datetime)
        self.chat_message_history += (user_chat_message,)
        model_response = self.openai.chat.completions.create(
            model=self.config.model.name,
            messages=list(map(functools.partial(pydantic.BaseModel.model_dump, mode='json'),
                              map(transform_chat_message_to_openai_chat_message, self.chat_message_history))),
            temperature=get_temperature(self.config.deterministic, self.config.temperature),
            stop=self.config.stop_sequences,
            seed=get_seed(self.config.deterministic),
            top_p=get_top_probability(self.config.deterministic, self.config.top_probability),
            max_tokens=self.config.max_tokens,
            n=self.config.choices,
            frequency_penalty=self.config.frequency_penalty,
            logit_bias=self.config.logit_bias,
            presence_penalty=self.config.presence_penalty,
            response_format=self.config.response_format,
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
