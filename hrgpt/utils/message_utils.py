import datetime

from hrgpt.logger.logger import LoggerFactory
from hrgpt.utils.type_utils import ChatMessage, Author


def generate_user_chat_message(prompt: str, datetime_value: datetime.datetime) -> ChatMessage:
    LoggerFactory.get_logger().debug(f'The following user prompt was used to generate a user chat message:\n{prompt}')
    return ChatMessage(
        text=prompt.strip(),
        author=Author.USER,
        creation_datetime=datetime_value,
        generation_timedelta=datetime_value - datetime_value)


def generate_model_chat_message(prompt: str,
                                before_datetime: datetime.datetime,
                                creation_datetime: datetime.datetime,
                                after_datetime: datetime.datetime) -> ChatMessage:
    return ChatMessage(
        text=prompt.strip(),
        author=Author.MODEL,
        creation_datetime=creation_datetime,
        generation_timedelta=after_datetime - before_datetime)


def generate_system_chat_message(prompt: str) -> ChatMessage:
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    return ChatMessage(
        text=prompt.strip(),
        author=Author.SYSTEM,
        creation_datetime=current_datetime,
        generation_timedelta=current_datetime - current_datetime)
