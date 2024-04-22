import os
import pathlib

import polars as pl

from hrgpt.logger.logger import LoggerFactory
from hrgpt.utils.path_utils import (
    get_screening_documents_path,
    get_generated_tables_path,
)
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import ApplicantMatch, MatchingResult


def create_output_files(
    score_result: dict[str, dict[str, ApplicantMatch]], log_result: bool = True
) -> None:
    for job_path, match_results in score_result.items():
        # create the result directory
        result_directory = os.path.join(os.path.dirname(job_path), "result")
        os.makedirs(result_directory, exist_ok=True)
        # make the resulting dataframe per job
        job_df_parts = []
        for candidate_path, applicant_match in match_results.items():
            # append the result part of the applicant
            job_df_parts.append(
                pl.DataFrame(
                    {
                        "candidate": [candidate_path],
                        "score": [applicant_match.total_score],
                        "promising": [applicant_match.promising_result.promising],
                        "explanation": [applicant_match.promising_result.explanation],
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
            "promising", "score", descending=(True, True)
        )
        # save the result table in the result directory
        job_df.write_csv(os.path.join(result_directory, "job_match_result.csv"))
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
        os.path.join(get_generated_tables_path(), "taken_time.csv"), float_precision=1
    )


def create_matching_result_output(matching_result: MatchingResult) -> None:
    create_taken_time_table(matching_result)
    matching_result_json_string = dumps(matching_result)
    result_directory = os.path.join(get_screening_documents_path(), "result")
    os.makedirs(result_directory, exist_ok=True)
    with open(os.path.join(result_directory, "matching_result.json"), "w") as file:
        file.write(matching_result_json_string)
