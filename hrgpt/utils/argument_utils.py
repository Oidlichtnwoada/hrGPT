import typing

import tap

from hrgpt.utils.path_utils import get_default_model_config_json_path, get_default_environment_secrets_file_path


class ArgumentParser(tap.Tap):
    target: typing.Literal['scoring', 'anonymization'] = 'scoring'
    job: tuple[int, ...] = (1,)
    candidate: tuple[int, ...] = (1,)
    config: str = get_default_model_config_json_path()
    secrets: str = get_default_environment_secrets_file_path()


def get_args() -> ArgumentParser:
    return ArgumentParser().parse_args()