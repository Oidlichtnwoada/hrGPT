import typing

import google.auth.credentials
import google.cloud.translate
import lingua

from hrgpt.utils.config_utils import AppConfigFactory


def get_native_language_of_model() -> str:
    return "en"


def get_translation_client() -> google.cloud.translate.TranslationServiceClient:
    app_config = AppConfigFactory.get_app_config()
    info = app_config.secrets.google_translate_service_account.model_dump(mode="json")
    return google.cloud.translate.TranslationServiceClient.from_service_account_info(
        info
    )


def get_project_id() -> str:
    app_config = AppConfigFactory.get_app_config()
    return app_config.secrets.google_translate_service_account.project_id


def translate_text(
    text: str, target_language: str, source_language: typing.Optional[str] = None
) -> str:
    translation: google.cloud.translate.Translation = (
        get_translation_client()
        .translate_text(
            google.cloud.translate.TranslateTextRequest(
                contents=[text],
                mime_type="text/plain",
                source_language_code=source_language,
                target_language_code=target_language,
                parent=f"projects/{get_project_id()}",
            )
        )
        .translations[0]
    )
    return str(translation.translated_text)


def detect_language(text: str) -> str:
    detector = lingua.LanguageDetectorBuilder.from_all_languages().build()
    detected_language = detector.detect_language_of(text)
    if detected_language is None:
        raise RuntimeError
    return detected_language.iso_code_639_1.name.lower()
