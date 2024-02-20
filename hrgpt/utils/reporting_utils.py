import os
import pathlib

import polars as pl

from hrgpt.logger.logger import LoggerFactory
from hrgpt.utils.config_utils import AppConfigFactory
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.translation_utils import get_native_language_of_model, translate_text
from hrgpt.utils.type_utils import ApplicantMatch


def translate_applicant_match(applicant_match: ApplicantMatch) -> ApplicantMatch:
    app_config = AppConfigFactory.get_app_config()
    target_language = app_config.generic_config.language_config.output_language
    if target_language == get_native_language_of_model():
        return applicant_match
    else:
        applicant_match.promising_result.explanation = translate_text(
            applicant_match.promising_result.explanation,
            target_language=target_language,
        )
        for requirement_match_list in applicant_match.requirement_matches.values():
            for requirement_match in requirement_match_list:
                requirement_match.requirement.specification = translate_text(
                    requirement_match.requirement.specification,
                    target_language=target_language,
                )
                requirement_match.score.explanation = translate_text(
                    requirement_match.score.explanation,
                    target_language=target_language,
                )
    return applicant_match


def create_output_files(
    score_result: dict[str, dict[str, ApplicantMatch]], log_result: bool = True
) -> None:
    for job_path, match_results in score_result.items():
        # create the result directory
        result_directory = os.path.join(os.path.dirname(job_path), "result")
        os.makedirs(result_directory, exist_ok=True)
        # make the resulting dataframe per job
        job_df_parts = []
        for candidate_path, match_result in match_results.items():
            # output translation
            translated_applicant_match = translate_applicant_match(match_result)
            # append the result part of the applicant
            job_df_parts.append(
                pl.DataFrame(
                    {
                        "candidate": [candidate_path],
                        "score": [translated_applicant_match.total_score],
                        "promising": [
                            translated_applicant_match.promising_result.promising
                        ],
                        "explanation": [
                            translated_applicant_match.promising_result.explanation
                        ],
                    }
                )
            )
            # save the applicants data as json in the result directory
            match_result_json = dumps(translated_applicant_match)
            candidate_result_path = os.path.join(
                result_directory,
                f"match_result_{pathlib.Path(candidate_path).stem}.json",
            )
            with open(candidate_result_path, "w") as file:
                file.write(match_result_json)
        job_df = pl.concat(job_df_parts).sort(
            "promising", "score", descending=(True, True)
        )
        # save the result table in the result directory
        job_df.write_csv(os.path.join(result_directory, "job_match_result.csv"))
        if log_result:
            LoggerFactory.get_logger().info(
                f"\n\nMatching results for the job '{job_path}':\n{job_df}\n"
            )
