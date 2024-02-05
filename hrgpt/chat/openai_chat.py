import datetime
import typing

import openai
import openai.types.chat

from hrgpt.chat.chat import Chat
from hrgpt.config.config import Provider, AppConfigFactory
from hrgpt.utils.config_utils import (
    get_temperature,
    get_seed,
    get_top_probability,
    get_model_for_model_enum,
)
from hrgpt.utils.message_utils import (
    generate_user_chat_message,
    generate_model_chat_message,
)
from hrgpt.utils.secret_utils import get_api_key_for_provider
from hrgpt.utils.type_utils import ChatMessage, Author

OpenaiChatMessageDict = typing.Union[
    openai.types.chat.ChatCompletionSystemMessageParam,
    openai.types.chat.ChatCompletionUserMessageParam,
    openai.types.chat.ChatCompletionAssistantMessageParam,
    openai.types.chat.ChatCompletionToolMessageParam,
    openai.types.chat.ChatCompletionFunctionMessageParam,
]


def transform_chat_message_history_to_openai_chat_messages(
    chat_messages: tuple[ChatMessage, ...],
) -> list[OpenaiChatMessageDict]:
    dict_list: list[OpenaiChatMessageDict] = []
    for chat_message in chat_messages:
        dict_value: OpenaiChatMessageDict
        if chat_message.author == Author.USER:
            user_value: openai.types.chat.ChatCompletionUserMessageParam = {
                "role": "user",
                "content": chat_message.text,
            }
            dict_value = user_value
        elif chat_message.author == Author.SYSTEM:
            system_value: openai.types.chat.ChatCompletionSystemMessageParam = {
                "role": "system",
                "content": chat_message.text,
            }
            dict_value = system_value
        elif chat_message.author == Author.MODEL:
            model_value: openai.types.chat.ChatCompletionAssistantMessageParam = {
                "role": "assistant",
                "content": chat_message.text,
            }
            dict_value = model_value
        else:
            raise ValueError
        dict_list.append(dict_value)
    return dict_list


class OpenaiChat(Chat):
    def __init__(self) -> None:
        config = AppConfigFactory.get_app_config()
        if (
            get_model_for_model_enum(config.llm_config.model).provider
            != Provider.OPENAI
        ):
            raise ValueError
        super().__init__(config.llm_config.system_context)
        self.openai = openai.OpenAI(
            api_key=get_api_key_for_provider(),
            max_retries=config.generic_config.network_config.retry_amount,
        )

    def send_prompt(self, prompt: str) -> ChatMessage:
        config = AppConfigFactory.get_app_config()
        before_datetime = datetime.datetime.now(datetime.timezone.utc)
        user_chat_message = generate_user_chat_message(prompt, before_datetime)
        self.chat_message_history += (user_chat_message,)
        model_response = self.openai.chat.completions.create(
            model=get_model_for_model_enum(config.llm_config.model).name,
            messages=transform_chat_message_history_to_openai_chat_messages(
                self.chat_message_history
            ),
            temperature=get_temperature(
                config.llm_config.deterministic, config.llm_config.temperature
            ),
            stop=list(config.llm_config.stop_sequences),
            seed=get_seed(config.llm_config.deterministic),
            top_p=get_top_probability(
                config.llm_config.deterministic, config.llm_config.top_probability
            ),
            max_tokens=config.llm_config.max_tokens,
            n=config.llm_config.choices,
            frequency_penalty=config.llm_config.frequency_penalty,
            logit_bias=config.llm_config.logit_bias,
            presence_penalty=config.llm_config.presence_penalty,
            response_format=config.llm_config.response_format,
        )
        after_datetime = datetime.datetime.now(datetime.timezone.utc)
        model_response_choice = model_response.choices[0]
        if (
            model_response_choice.message.content is None
            or model_response_choice.finish_reason != "stop"
        ):
            raise RuntimeError
        creation_datetime = datetime.datetime.fromtimestamp(
            model_response.created, datetime.timezone.utc
        )
        model_chat_message = generate_model_chat_message(
            model_response_choice.message.content,
            before_datetime,
            creation_datetime,
            after_datetime,
        )
        self.chat_message_history += (model_chat_message,)
        return model_chat_message
