import datetime

import pydantic
import replicate

from hrgpt.chat.chat import Chat, Provider, generate_user_chat_message, Author, ChatMessage, \
    get_api_key_for_provider, generate_model_chat_message, get_seed, get_temperature, get_top_tokens, get_top_probability
from hrgpt.config.config import AppConfig, get_model_for_model_enum
from hrgpt.utils.type_utils import StrippedString


class ReplicateChatMessage(pydantic.BaseModel):
    prompt: StrippedString
    system_prompt: StrippedString


class ReplicateChat(Chat):
    def __init__(self, config: AppConfig) -> None:
        if get_model_for_model_enum(config.llm_config.model).provider != Provider.REPLICATE:
            raise ValueError
        super().__init__(config.llm_config.system_context)
        self.config = config
        self.replicate = replicate.Client(
            api_token=get_api_key_for_provider(self.config),
        )
        self.replicate._client._transport.max_attempts = self.config.generic_config.network_config.retry_amount

    def transform_chat_messages_to_replicate_chat_object(self) -> ReplicateChatMessage:
        prompts = []
        for chat_message in self.get_chat_message_history():
            if chat_message.author == Author.USER:
                prompts.append(f'[INST] {chat_message.text} [/INST]')
            elif chat_message.author == Author.MODEL:
                prompts.append(chat_message.text)
            else:
                raise ValueError
        return ReplicateChatMessage(system_prompt=self.get_context(), prompt='\n'.join(prompts))

    def send_prompt(self, prompt: str) -> ChatMessage:
        before_datetime = datetime.datetime.now(datetime.timezone.utc)
        user_chat_message = generate_user_chat_message(prompt, before_datetime)
        self.chat_message_history += (user_chat_message,)
        output_parts = self.replicate.run(
            get_model_for_model_enum(self.config.llm_config.model).name,
            {
                **self.transform_chat_messages_to_replicate_chat_object().model_dump(mode='json'),
                'debug': self.config.llm_config.debug,
                'top_k': get_top_tokens(self.config.llm_config.deterministic, self.config.llm_config.top_tokens),
                'top_p': get_top_probability(self.config.llm_config.deterministic, self.config.llm_config.top_probability),
                'temperature': max(0.01, get_temperature(self.config.llm_config.deterministic, self.config.llm_config.temperature)),
                'max_new_tokens': self.config.llm_config.max_tokens,
                'min_new_tokens': self.config.llm_config.min_tokens,
                'seed': get_seed(self.config.llm_config.deterministic),
                'stop_sequences': ','.join([f'<{x}>' for x in self.config.llm_config.stop_sequences]),
                'repetition_penalty': self.config.llm_config.repetition_penalty,
            }
        )
        after_datetime = datetime.datetime.now(datetime.timezone.utc)
        model_chat_message = generate_model_chat_message(''.join(output_parts),
                                                         before_datetime,
                                                         after_datetime,
                                                         after_datetime)
        self.chat_message_history += (model_chat_message,)
        return model_chat_message
