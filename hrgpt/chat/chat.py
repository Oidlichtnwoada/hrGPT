import abc

from hrgpt.utils.message_utils import generate_system_chat_message
from hrgpt.utils.type_utils import StrippedString, ChatMessage, Author


class Chat(abc.ABC):
    def __init__(self, context: str) -> None:
        self.chat_message_history: tuple[ChatMessage, ...] = ()
        self.set_context(context)

    @abc.abstractmethod
    def send_prompt(self, prompt: str) -> ChatMessage:
        pass

    def get_chat_message_history(
        self, include_context: bool = False
    ) -> tuple[ChatMessage, ...]:
        return tuple(
            [
                x
                for x in self.chat_message_history
                if include_context or x.author != Author.SYSTEM
            ]
        )

    def set_context(self, context: str) -> None:
        if len(self.chat_message_history) > 0:
            return
        self.chat_message_history += (generate_system_chat_message(context),)

    def get_context(self) -> StrippedString:
        system_chat_messages = [
            x for x in self.chat_message_history if x.author == Author.SYSTEM
        ]
        if len(system_chat_messages) == 0:
            raise RuntimeError
        system_chat_message = system_chat_messages[0]
        return system_chat_message.text
