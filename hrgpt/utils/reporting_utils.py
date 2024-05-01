import os
import pathlib
import statistics

import polars as pl

from hrgpt.logger.logger import LoggerFactory
from hrgpt.utils.path_utils import (
    get_screening_documents_path,
    get_generated_tables_path,
    get_result_directory_path,
)
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import ApplicantMatch, MatchingResult


def create_category_scores_for_applicant_match(
    match: ApplicantMatch,
) -> dict[str, float]:
    category_scores: dict[str, float] = {}
    for category, requirement_match_list in match.requirement_matches.items():
        if len(requirement_match_list) == 0:
            continue
        category_scores[f"score ({category})"] = float(
            statistics.mean([x.score.value for x in requirement_match_list])
        )
    return category_scores


def create_output_files(
    score_result: dict[str, dict[str, ApplicantMatch]], log_result: bool = True
) -> None:
    for job_path, match_results in score_result.items():
        # create the result directory
        result_directory = get_result_directory_path(os.path.dirname(job_path))
        # make the resulting dataframe per job
        job_df_parts = []
        for candidate_path, applicant_match in match_results.items():
            # append the result part of the applicant
            job_df_parts.append(
                pl.DataFrame(
                    {
                        "candidate": [pathlib.Path(candidate_path).stem],
                        "promising": [applicant_match.promising_result.promising],
                        "total_score": [applicant_match.total_score],
                        **create_category_scores_for_applicant_match(applicant_match),
                    }
                )
            )
            # save the applicants data as json in the result directory
            match_result_json = dumps(applicant_match)
            candidate_result_path = os.path.join(
                result_directory,
                f"match_result_{pathlib.Path(candidate_path).stem}.json",
            )
            with open(candidate_result_path, "w") as file:
                file.write(match_result_json)
        job_df = pl.concat(job_df_parts).sort(
            "promising", "total_score", descending=(True, True)
        )
        # save the result table in the result directory
        job_df.write_csv(
            os.path.join(result_directory, "job_match_result.csv"), float_precision=1
        )
        if log_result:
            LoggerFactory.get_logger().info(
                f"\n\nMatching results for the job '{job_path}':\n{job_df}\n"
            )


def create_taken_time_table(matching_result: MatchingResult) -> None:
    dataframe = pl.DataFrame()
    for job_name, job_matching_result in matching_result.matching_result.items():
        minutes_taken_dict = {}
        for human_result in job_matching_result.human_matching_evaluation.human_results:
            minutes_taken_dict[f"human_id: {human_result.human_id}"] = float(
                human_result.minutes_taken
            )
        dataframe = pl.concat(
            (
                dataframe,
                pl.DataFrame(
                    {
                        "job_name": job_name,
                        **minutes_taken_dict,
                        "mean": job_matching_result.mean_human_evaluation.mean_human_result.minutes_taken,
                    }
                ),
            ),
        )
    mean_row = pl.DataFrame(
        {**dataframe.mean(axis=0).to_dicts()[0], "job_name": "mean"}
    )
    dataframe = pl.concat((dataframe, mean_row))
    dataframe.write_csv(
        os.path.join(get_generated_tables_path(), "taken_time.csv"), float_precision=2
    )


def create_taken_time_model_table(matching_result: MatchingResult) -> None:
    dataframe = pl.DataFrame()
    for job_name, job_matching_result in matching_result.matching_result.items():
        minutes_taken_dict = {}
        ai_result = job_matching_result.ai_model_matching_evaluation.ai_model_result
        minutes_taken = ai_result.seconds_taken / 60
        minutes_taken_dict["model"] = float(minutes_taken)
        dataframe = pl.concat(
            (
                dataframe,
                pl.DataFrame(
                    {
                        "job_name": job_name,
                        **minutes_taken_dict,
                    }
                ),
            ),
        )
    mean_row = pl.DataFrame(
        {**dataframe.mean(axis=0).to_dicts()[0], "job_name": "mean"}
    )
    dataframe = pl.concat((dataframe, mean_row))
    dataframe.write_csv(
        os.path.join(get_generated_tables_path(), "taken_time_model.csv"),
        float_precision=2,
    )


def create_matching_result_output(matching_result: MatchingResult) -> None:
    create_taken_time_table(matching_result)
    create_taken_time_model_table(matching_result)
    matching_result_json_string = dumps(matching_result)
    result_directory = get_result_directory_path(get_screening_documents_path())
    with open(os.path.join(result_directory, "matching_result.json"), "w") as file:
        file.write(matching_result_json_string)
