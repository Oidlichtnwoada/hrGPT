from hrgpt.chat.chat import Chat, Provider, DEFAULT_MODEL_CONFIG
from hrgpt.chat.openai_chat import OpenaiChat
from hrgpt.chat.replicate_chat import ReplicateChat


def get_chat(**kwargs) -> Chat:
    config = DEFAULT_MODEL_CONFIG
    if config.model.provider == Provider.OPENAI:
        return OpenaiChat(config)
    elif config.model.provider == Provider.REPLICATE:
        return ReplicateChat(config)
    else:
        raise ValueError


if __name__ == '__main__':
    get_chat()
