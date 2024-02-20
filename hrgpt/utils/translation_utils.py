import typing

import google.auth.credentials
import google.cloud.translate

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


def get_confidence(language: google.cloud.translate.DetectedLanguage) -> float:
    return float(language.confidence)


def detect_language(text: str, detection_character_limit: int = 1_000) -> str:
    detected_languages: tuple[google.cloud.translate.DetectedLanguage, ...] = tuple(
        get_translation_client()
        .detect_language(
            google.cloud.translate.DetectLanguageRequest(
                content=text[:detection_character_limit],
                mime_type="text/plain",
                parent=f"projects/{get_project_id()}",
            )
        )
        .languages
    )
    if len(detected_languages) == 0:
        raise RuntimeError
    sorted_detected_languages: list[google.cloud.translate.DetectedLanguage] = sorted(
        detected_languages, key=get_confidence, reverse=True
    )
    return str(sorted_detected_languages[0].language_code)
