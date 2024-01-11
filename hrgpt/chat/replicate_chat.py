import dataclasses

import pendulum
import replicate

from hrgpt.chat.chat import ModelConfig, Chat, Provider, generate_user_chat_message, Author, ChatMessage, \
    get_api_key_for_provider, generate_model_chat_message


@dataclasses.dataclass(order=True, frozen=True, kw_only=True)
class ReplicateChatMessage:
    prompt: str
    system_prompt: str


class ReplicateChat(Chat):
    def __init__(self, config: ModelConfig) -> None:
        if config.model.provider != Provider.REPLICATE:
            raise ValueError
        super().__init__(config.system_context)
        self.config = config
        self.replicate = replicate.Client(get_api_key_for_provider(self.config.model.provider))

    def transform_chat_message_to_replicate_chat_object(self) -> ReplicateChatMessage:
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
        before_datetime = pendulum.DateTime.utcnow()
        user_chat_message = generate_user_chat_message(prompt, before_datetime)
        self.chat_message_history += (user_chat_message,)
        output_parts = self.replicate.run(
            self.config.model.model_name,
            {
                **dataclasses.asdict(self.transform_chat_message_to_replicate_chat_object()),
                'debug': self.config.debug,
                'top_k': self.config.top_tokens,
                'top_p': self.config.top_probability,
                'temperature': self.config.temperature,
                'max_new_tokens': self.config.max_tokens,
                'min_new_tokens': self.config.min_tokens,
                'seed': self.config.deterministic,
                'stop_sequences': ','.join([x for x in self.config.stop_sequences]),
            }
        )
        after_datetime = pendulum.DateTime.utcnow()
        model_chat_message = generate_model_chat_message(''.join(output_parts),
                                                         before_datetime,
                                                         after_datetime,
                                                         after_datetime)
        self.chat_message_history += (model_chat_message,)
        return model_chat_message
