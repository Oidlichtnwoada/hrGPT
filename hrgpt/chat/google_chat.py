import datetime
import enum

import google.generativeai

from hrgpt.chat.chat import Chat
from hrgpt.config.config import Provider
from hrgpt.utils.config_utils import (
    get_temperature,
    get_top_probability,
    get_model_for_model_enum,
    AppConfigFactory,
    get_top_tokens,
)
from hrgpt.utils.message_utils import (
    generate_user_chat_message,
    generate_model_chat_message,
)
from hrgpt.utils.secret_utils import get_api_key_for_provider
from hrgpt.utils.type_utils import ChatMessage, Author


class FinishReason(enum.Enum):
    FINISH_REASON_UNSPECIFIED = 0
    STOP = 1
    MAX_TOKENS = 2
    SAFETY = 3
    RECITATION = 4
    OTHER = 5


def transform_chat_message_history_to_google_chat_messages(
    chat_messages: tuple[ChatMessage, ...],
) -> list[google.generativeai.types.ContentDict]:
    dict_list: list[google.generativeai.types.ContentDict] = []
    for chat_message in chat_messages:
        dict_value: google.generativeai.types.ContentDict
        if chat_message.author == Author.USER:
            user_value: google.generativeai.types.ContentDict = {
                "role": "user",
                "parts": [chat_message.text],
            }
            dict_value = user_value
        elif chat_message.author == Author.MODEL:
            model_value: google.generativeai.types.ContentDict = {
                "role": "model",
                "parts": [chat_message.text],
            }
            dict_value = model_value
        else:
            raise ValueError
        dict_list.append(dict_value)
    return dict_list


class GoogleChat(Chat):
    def __init__(self) -> None:
        config = AppConfigFactory.get_app_config()
        if (
            get_model_for_model_enum(config.llm_config.model).provider
            != Provider.GOOGLE
        ):
            raise ValueError
        super().__init__(config.llm_config.system_context)
        google.generativeai.configure(api_key=get_api_key_for_provider())

    def send_prompt(self, prompt: str) -> ChatMessage:
        config = AppConfigFactory.get_app_config()
        before_datetime = datetime.datetime.now(datetime.timezone.utc)
        user_chat_message = generate_user_chat_message(prompt, before_datetime)
        self.chat_message_history += (user_chat_message,)
        model = google.generativeai.GenerativeModel(
            get_model_for_model_enum(config.llm_config.model).name,
            generation_config=google.generativeai.GenerationConfig(
                candidate_count=config.llm_config.choices,
                stop_sequences=config.llm_config.stop_sequences,
                max_output_tokens=config.llm_config.max_tokens,
                temperature=min(
                    1.0,
                    get_temperature(
                        config.llm_config.deterministic, config.llm_config.temperature
                    ),
                ),
                top_p=get_top_probability(
                    config.llm_config.deterministic, config.llm_config.top_probability
                ),
                top_k=get_top_tokens(
                    config.llm_config.deterministic, config.llm_config.top_tokens
                ),
            ),
        )
        google_chat_messages = transform_chat_message_history_to_google_chat_messages(
            self.get_chat_message_history()
        )
        chat = model.start_chat(history=google_chat_messages[:-1])
        model_response = chat.send_message(google_chat_messages[-1])
        after_datetime = datetime.datetime.now(datetime.timezone.utc)
        model_response_choice = model_response.candidates[0]
        if (
            len(model_response_choice.content.parts) != 1
            or model_response_choice.finish_reason.value != FinishReason.STOP.value
        ):
            raise RuntimeError
        creation_datetime = after_datetime
        model_chat_message = generate_model_chat_message(
            model_response_choice.content.parts[0].text,
            before_datetime,
            creation_datetime,
            after_datetime,
        )
        self.chat_message_history += (model_chat_message,)
        return model_chat_message
