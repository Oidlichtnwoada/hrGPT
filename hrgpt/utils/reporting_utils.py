import collections
import os
import pathlib
import statistics
import typing

import polars as pl

from hrgpt.logger.logger import LoggerFactory
from hrgpt.utils.iterable_utils import all_elements_equal
from hrgpt.utils.math_utils import (
    compute_kendall_tau_correlation,
    compute_hamming_distance,
)
from hrgpt.utils.path_utils import (
    get_screening_documents_path,
    get_generated_tables_path,
    get_result_directory_path,
)
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import (
    ApplicantMatch,
    MatchingResult,
    RankingPlace,
    ApplicantName,
    JobName,
)

T = typing.TypeVar("T")


def get_float_precision(adjustment: int = 0) -> int:
    return 2 + adjustment


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
            os.path.join(result_directory, "job_match_result.csv"),
            float_precision=get_float_precision(),
        )
        if log_result:
            LoggerFactory.get_logger().info(
                f"\n\nMatching results for the job '{job_path}':\n{job_df}\n"
            )


def get_human_id_name(human_id: int) -> str:
    return f"human_id: {human_id}"


def get_model_name() -> str:
    return "model"


def get_mean_name() -> str:
    return "mean"


def get_entity_name() -> str:
    return "entity"


def create_taken_time_table(matching_result: MatchingResult) -> None:
    dataframe = pl.DataFrame()
    for job_name, job_matching_result in matching_result.matching_result.items():
        minutes_taken_dict = {}
        for human_result in job_matching_result.human_matching_evaluation.human_results:
            minutes_taken_dict[get_human_id_name(human_result.human_id)] = float(
                human_result.minutes_taken
            )
        dataframe = pl.concat(
            (
                dataframe,
                pl.DataFrame(
                    {
                        "job_name": job_name,
                        **minutes_taken_dict,
                        get_mean_name(): job_matching_result.mean_human_evaluation.mean_human_result.minutes_taken,
                    }
                ),
            ),
        )
    mean_row = pl.DataFrame(
        {**dataframe.mean(axis=0).to_dicts()[0], "job_name": get_mean_name()}
    )
    dataframe = pl.concat((dataframe, mean_row))
    dataframe.write_csv(
        os.path.join(get_generated_tables_path(), "taken_time.csv"),
        float_precision=get_float_precision(),
    )


def add_mean_row_to_dataframe(
    df: pl.DataFrame, non_numeric_column_values: dict[str, str]
) -> pl.DataFrame:
    mean_row = pl.DataFrame(
        {**df.mean(axis=0).to_dicts()[0], **non_numeric_column_values}
    )
    new_dataframe = pl.concat((df, mean_row))
    return new_dataframe


def create_taken_time_model_table(matching_result: MatchingResult) -> None:
    dataframe = pl.DataFrame()
    for job_name, job_matching_result in matching_result.matching_result.items():
        minutes_taken_dict = {}
        ai_result = job_matching_result.ai_model_matching_evaluation.ai_model_result
        minutes_taken = ai_result.seconds_taken / 60
        minutes_taken_dict[get_model_name()] = float(minutes_taken)
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
    dataframe = add_mean_row_to_dataframe(dataframe, {"job_name": get_mean_name()})
    dataframe.write_csv(
        os.path.join(get_generated_tables_path(), "taken_time_model.csv"),
        float_precision=get_float_precision(),
    )


def create_matrix(
    data: dict[str, T],
    metric_function: typing.Callable[[T, T], typing.Union[float, int]],
) -> pl.DataFrame:
    column_names = list(data.keys())
    dataframe = pl.DataFrame()
    for column_name in column_names:
        metric_data: dict[str, float] = {}
        for other_column_name in column_names:
            metric_data[other_column_name] = float(
                metric_function(data[column_name], data[other_column_name])
            )
        dataframe = pl.concat(
            (
                dataframe,
                pl.DataFrame(
                    {
                        get_entity_name(): column_name,
                        **metric_data,
                        get_mean_name(): float(statistics.mean(metric_data.values())),
                    }
                ),
            ),
        )
    dataframe = add_mean_row_to_dataframe(
        dataframe, {get_entity_name(): get_mean_name()}
    )
    return dataframe


def compute_mean_dataframe(data: dict[JobName, pl.DataFrame]) -> pl.DataFrame:
    columns = [tuple(x.columns) for x in data.values()]
    shapes = [x.shape for x in data.values()]
    if (
        not all_elements_equal(columns)
        or not all_elements_equal(shapes)
        or len(data) == 0
    ):
        raise ValueError
    numeric_values: dict[tuple[int, int], list[float]] = collections.defaultdict(
        lambda: []
    )
    text_values: dict[tuple[int, int], list[float]] = collections.defaultdict(
        lambda: []
    )
    for df in data.values():
        for column, series in enumerate(df.iter_columns()):
            for row, value in enumerate(series):
                if series.dtype == pl.String:
                    text_values[(row, column)].append(value)
                else:
                    numeric_values[(row, column)].append(value)
    for text_value_list in text_values.values():
        if not all_elements_equal(text_value_list):
            raise ValueError
    mean_values_df = list(data.values())[0].clone()
    for (row, column), numeric_value_list in numeric_values.items():
        mean_values_df[row, column] = float(statistics.mean(numeric_value_list))
    return mean_values_df


def store_dictionary_data(data: dict[JobName, pl.DataFrame], key: str) -> None:
    for job_name, df in data.items():
        if job_name == get_mean_name():
            float_precision = get_float_precision(1)
        else:
            float_precision = get_float_precision()
        df.write_csv(
            os.path.join(get_generated_tables_path(), f"{job_name}_{key}.csv"),
            float_precision=float_precision,
        )


def create_kendall_tau_correlation_matrices(
    matching_result: MatchingResult, include_model: bool = True
) -> None:
    kendall_tau_correlation_matrices: dict[JobName, pl.DataFrame] = {}
    for job_name, job_matching_result in matching_result.matching_result.items():
        rankings: dict[str, dict[RankingPlace, ApplicantName]] = {}
        for human_result in job_matching_result.human_matching_evaluation.human_results:
            rankings[get_human_id_name(human_result.human_id)] = (
                human_result.candidate_places
            )
        if include_model:
            rankings[get_model_name()] = (
                job_matching_result.ai_model_matching_evaluation.ai_model_result.candidate_places
            )
        matrix = create_matrix(rankings, compute_kendall_tau_correlation)
        kendall_tau_correlation_matrices[job_name] = matrix
    mean_dataframe = compute_mean_dataframe(kendall_tau_correlation_matrices)
    kendall_tau_correlation_matrices[get_mean_name()] = mean_dataframe
    store_dictionary_data(
        kendall_tau_correlation_matrices, "kendall_tau_correlation_matrix"
    )


def create_hamming_distance_distance_matrices(
    matching_result: MatchingResult, include_model: bool = True
) -> None:
    hamming_distance_distance_matrices: dict[JobName, pl.DataFrame] = {}
    for job_name, job_matching_result in matching_result.matching_result.items():
        promising_candidates: dict[str, set[ApplicantName]] = {}
        for human_result in job_matching_result.human_matching_evaluation.human_results:
            promising_candidates[get_human_id_name(human_result.human_id)] = (
                human_result.promising_candidates
            )
        if include_model:
            promising_candidates[get_model_name()] = (
                job_matching_result.ai_model_matching_evaluation.ai_model_result.promising_candidates
            )
        matrix = create_matrix(promising_candidates, compute_hamming_distance)
        hamming_distance_distance_matrices[job_name] = matrix
    mean_dataframe = compute_mean_dataframe(hamming_distance_distance_matrices)
    hamming_distance_distance_matrices[get_mean_name()] = mean_dataframe
    store_dictionary_data(
        hamming_distance_distance_matrices, "hamming_distance_distance_matrix"
    )


def create_matching_result_output(matching_result: MatchingResult) -> None:
    create_taken_time_table(matching_result)
    create_taken_time_model_table(matching_result)
    create_kendall_tau_correlation_matrices(matching_result)
    create_hamming_distance_distance_matrices(matching_result)
    matching_result_json_string = dumps(matching_result)
    result_directory = get_result_directory_path(get_screening_documents_path())
    with open(os.path.join(result_directory, "matching_result.json"), "w") as file:
        file.write(matching_result_json_string)
