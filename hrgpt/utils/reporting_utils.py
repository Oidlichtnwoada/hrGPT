import os
import pathlib

import polars as pl

from hrgpt.logger.logger import LoggerFactory
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import ApplicantMatch


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
            # append the result part of the applicant
            job_df_parts.append(
                pl.DataFrame(
                    {
                        "candidate": [candidate_path],
                        "score": [match_result.total_score],
                        "promising": [match_result.promising_result.promising],
                        "explanation": [match_result.promising_result.explanation],
                    }
                )
            )
            # save the applicants data as json in the result directory
            match_result_json = dumps(match_result)
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
