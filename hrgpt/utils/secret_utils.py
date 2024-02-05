import typing

from hrgpt.config.config import Provider, AppConfigFactory
from hrgpt.utils.config_utils import get_model_for_model_enum


def get_api_key_for_provider() -> str:
    app_config = AppConfigFactory.get_app_config()
    api_key: typing.Optional[str] = None
    provider = get_model_for_model_enum(app_config.llm_config.model).provider
    if provider == Provider.OPENAI:
        api_key = app_config.secrets.openai_api_key
    elif provider == Provider.REPLICATE:
        api_key = app_config.secrets.replicate_api_key
    if api_key is None:
        raise RuntimeError
    return api_key


def get_aspose_pdf_cloud_credentials() -> tuple[str, str]:
    app_config = AppConfigFactory.get_app_config()
    return app_config.secrets.aspose_app_key, app_config.secrets.aspose_app_sid
