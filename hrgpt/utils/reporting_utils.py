import collections
import math
import os
import pathlib
import statistics
import typing

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import polars as pl
import scipy
import sklearn.manifold

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
    get_generated_pdfs_path,
)
from hrgpt.utils.serialization_utils import dumps
from hrgpt.utils.type_utils import (
    ApplicantMatch,
    MatchingResult,
    RankingPlace,
    ApplicantName,
    JobName,
    get_unique_places_amount,
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


def default_transform(df: pl.DataFrame) -> pl.DataFrame:
    return df


def kendall_tau_correlation_to_distance(value: float) -> int:
    return int(
        (value - 1) * (-1) / 2 * scipy.special.binom(get_unique_places_amount(), 2)
    )


def kendall_tau_distance_transform(df: pl.DataFrame) -> pl.DataFrame:
    column_names: list[str] = df.columns
    df = df.map_rows(lambda row: tuple(map(kendall_tau_correlation_to_distance, row)))
    df = df.rename(
        {
            column_name: new_column_name
            for column_name, new_column_name in zip(df.columns, column_names)
        }
    )
    return df


def create_plot_from_mean_dataframe(
    mean_df: pl.DataFrame,
    title: str,
    transform_function: typing.Callable[
        [pl.DataFrame, float], float
    ] = default_transform,
) -> None:
    mds = sklearn.manifold.MDS(
        n_components=2,
        metric=True,
        n_init=256,
        max_iter=1024,
        verbose=0,
        eps=1e-6,
        n_jobs=-1,
        random_state=42,
        dissimilarity="precomputed",
        normalized_stress="auto",
    )
    distance_matrix = transform_function(mean_df[mean_df.columns[1:-1]].slice(0, -1))
    fit_result = mds.fit(distance_matrix)
    position_for_label_dict: dict[str, tuple[float, float]] = {
        key: (x, y)
        for key, (x, y) in zip(fit_result.feature_names_in_, fit_result.embedding_)
    }
    x_limit = max([abs(x) for (x, _) in position_for_label_dict.values()])
    y_limit = max([abs(y) for (_, y) in position_for_label_dict.values()])
    limit = math.ceil(max(x_limit, y_limit)) + 1
    figure, axis = plt.subplots()
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_xlim([-limit, limit])
    axis.set_ylim([-limit, limit])
    axis.set_aspect("equal", adjustable="box")
    axis.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    axis.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    axis.set_title(f"{title} (Multidimensional Scaling)", pad=12)
    axis.set_axisbelow(True)
    for key, (x, y) in position_for_label_dict.items():
        axis.scatter(x, y, label=key, s=128)
    plt.grid(color="lightgrey", linestyle=(0, (1, 1)), linewidth=1)
    plt.tight_layout()
    plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left", borderaxespad=0.0)
    file_name = f'{title.lower().replace(" ", "_")}.pdf'
    plt.savefig(os.path.join(get_generated_pdfs_path(), file_name), bbox_inches="tight")
    plt.close()


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
    create_plot_from_mean_dataframe(
        mean_dataframe, "Kendall's Tau Distance", kendall_tau_distance_transform
    )
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
    create_plot_from_mean_dataframe(mean_dataframe, "Hamming Distance")
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
