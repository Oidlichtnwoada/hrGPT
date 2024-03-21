import collections
import json
import os
import pathlib
import statistics
import typing

import pandas
import scipy

from hrgpt.evaluation.csv_loader import load_result_from_responses_csv_file
from hrgpt.utils.path_utils import (
    get_job_folder_path_by_job_index,
    get_responses_csv_path,
    get_screening_documents_path,
)
from hrgpt.utils.reporting_utils import create_matching_result_output
from hrgpt.utils.type_utils import (
    CompleteHumanMatchingResult,
    CompleteMeanHumanMatchingResult,
    MeanHumanMatchingResult,
    RankingPlace,
    CompleteHumanMatchingErrorResult,
    HumanMatchingErrorResult,
    CompleteModelMatchingErrorResult,
    ModelMatchingErrorResult,
    ModelMatchingResult,
    JobName,
    ApplicantName,
    MatchingResult,
    JobMatchingResult,
    CompleteModelMatchingResult,
    HumanMatchingEvaluation,
    ModelMatchingEvaluation,
    ModelMetrics,
    MeanHumanMatchingEvaluation,
    MeanHumanMatchingErrorResult,
)

T = typing.TypeVar("T")


def compute_mean_set(sets: tuple[set[T], ...]) -> set[T]:
    result_set: set[T] = set()
    set_amount = len(sets)
    half_set_amount = set_amount / 2
    presence_count_dict: dict[T, int] = collections.defaultdict(int)
    for set_arg in sets:
        for element in set_arg:
            presence_count_dict[element] += 1
    for element, count in presence_count_dict.items():
        if count > half_set_amount:
            result_set.add(element)
    return result_set


def compute_mean_ranking(
    rankings: tuple[dict[RankingPlace, T], ...]
) -> dict[RankingPlace, T]:
    result: dict[RankingPlace, T] = {}
    places_per_element: dict[T, list[RankingPlace]] = collections.defaultdict(list)
    for ranking in rankings:
        for place, element in ranking.items():
            places_per_element[element].append(place)
    order_information = [
        {
            "name": name,
            "mean": statistics.mean(places),
            "mode": statistics.mode(places),
            "min": min(places),
            "max": max(places),
        }
        for name, places in places_per_element.items()
    ]
    order_information_df = pandas.DataFrame(order_information)
    ordered_order_information_df = order_information_df.sort_values(
        ["mean", "mode", "min", "max"],
        ascending=[True, True, True, True],
        ignore_index=True,
    )
    for index, name in ordered_order_information_df["name"].items():
        result[typing.cast(RankingPlace, typing.cast(int, index) + 1)] = name
    return result


def compute_mean_human_matching_result(
    human_matching_result: CompleteHumanMatchingResult,
) -> CompleteMeanHumanMatchingResult:
    result: CompleteMeanHumanMatchingResult = {}
    for job_name, human_matching_results in human_matching_result.items():
        mean_minutes_taken = statistics.mean(
            [x.minutes_taken for x in human_matching_results]
        )
        result[job_name] = MeanHumanMatchingResult(
            job_name=job_name,
            minutes_taken=mean_minutes_taken,
            promising_candidates=compute_mean_set(
                tuple([x.promising_candidates for x in human_matching_results])
            ),
            candidate_places=compute_mean_ranking(
                tuple([x.candidate_places for x in human_matching_results])
            ),
        )
    return result


def compute_hamming_distance(first_set: set[T], second_set: set[T]) -> int:
    return len(first_set.symmetric_difference(second_set))


def compute_kendall_tau_correlation(
    first_ranking: dict[RankingPlace, T],
    second_ranking: dict[RankingPlace, T],
) -> float:
    first_ranking_values_in_order = [
        first_ranking[key] for key in sorted(first_ranking.keys())
    ]
    second_ranking_values_in_order = [
        second_ranking[key] for key in sorted(second_ranking.keys())
    ]
    kendall_tau = scipy.stats.kendalltau(
        first_ranking_values_in_order,
        second_ranking_values_in_order,
        nan_policy="raise",
        method="exact",
    )
    return float(kendall_tau.correlation)


def compute_human_matching_error_result(
    mean_human_matching_result: CompleteMeanHumanMatchingResult,
    human_matching_result: CompleteHumanMatchingResult,
) -> CompleteHumanMatchingErrorResult:
    result: CompleteHumanMatchingErrorResult = collections.defaultdict(tuple)
    for job_name, human_matching_results in human_matching_result.items():
        mean_human_job_matching = mean_human_matching_result[job_name]
        for human_job_matching_result in human_matching_results:
            error = HumanMatchingErrorResult(
                human_id=human_job_matching_result.human_id,
                job_name=job_name,
                promising_candidates_hamming_distance=compute_hamming_distance(
                    mean_human_job_matching.promising_candidates,
                    human_job_matching_result.promising_candidates,
                ),
                candidate_places_kendall_tau_correlation=compute_kendall_tau_correlation(
                    mean_human_job_matching.candidate_places,
                    human_job_matching_result.candidate_places,
                ),
            )
            result[job_name] += (error,)
    return result


def get_job_index_by_job_name(job_name: str) -> int:
    screening_documents_folder = pathlib.Path(get_screening_documents_path())
    result_indices = [
        int(x.parts[-2].split("_")[1])
        for x in screening_documents_folder.rglob(f"{job_name}.txt")
        if x.is_file()
    ]
    if len(result_indices) != 1:
        raise RuntimeError
    return result_indices[0]


def map_candidate_path_to_candidate_name(candidate_path: str) -> ApplicantName:
    path_object = pathlib.Path(candidate_path)
    job_id = int(path_object.parts[-3].split("_")[1])
    candidate_id = int(path_object.stem.split("_")[1])
    responses_df = pandas.read_csv(get_responses_csv_path())
    candidate_place_label = responses_df.T.index[
        3 + (10 * (job_id - 1)) + (candidate_id - 1)
    ]
    candidate_name = " ".join(candidate_place_label.split(" ")[2:])
    return candidate_name


def get_model_matching_result_by_job_name(job_name: JobName) -> ModelMatchingResult:
    job_index = get_job_index_by_job_name(job_name)
    job_folder_path = get_job_folder_path_by_job_index(job_index)
    with open(os.path.join(job_folder_path, "result", "additional_info.json")) as file:
        seconds_taken = json.load(file)["seconds_taken"]
    match_result_df = pandas.read_csv(
        os.path.join(job_folder_path, "result", "job_match_result.csv")
    )
    promising_candidate_paths = set(
        match_result_df[match_result_df["promising"] == True]["candidate"]
    )
    promising_candidates = set(
        [map_candidate_path_to_candidate_name(x) for x in promising_candidate_paths]
    )
    ordered_candidate_paths = list(match_result_df["candidate"])
    candidate_places = {
        typing.cast(RankingPlace, index + 1): map_candidate_path_to_candidate_name(path)
        for index, path in enumerate(ordered_candidate_paths)
    }
    return ModelMatchingResult(
        job_name=job_name,
        seconds_taken=seconds_taken,
        promising_candidates=promising_candidates,
        candidate_places=candidate_places,
    )


def get_model_matching_result(
    mean_human_matching_result: CompleteMeanHumanMatchingResult,
) -> CompleteModelMatchingResult:
    result: CompleteModelMatchingResult = {}
    for job_name, mean_human_job_matching in mean_human_matching_result.items():
        model_matching_result = get_model_matching_result_by_job_name(job_name)
        result[job_name] = model_matching_result
    return result


def compute_model_matching_error_result(
    mean_human_matching_result: CompleteMeanHumanMatchingResult,
    model_matching_result: CompleteModelMatchingResult,
) -> CompleteModelMatchingErrorResult:
    result: CompleteModelMatchingErrorResult = {}
    for job_name, mean_human_job_matching in mean_human_matching_result.items():
        job_model_matching_result = model_matching_result[job_name]
        error = ModelMatchingErrorResult(
            job_name=job_name,
            promising_candidates_hamming_distance=compute_hamming_distance(
                mean_human_job_matching.promising_candidates,
                job_model_matching_result.promising_candidates,
            ),
            candidate_places_kendall_tau_correlation=compute_kendall_tau_correlation(
                mean_human_job_matching.candidate_places,
                job_model_matching_result.candidate_places,
            ),
        )
        result[job_name] = error
    return result


def get_hamming_distance(
    result: ModelMatchingErrorResult | HumanMatchingErrorResult,
) -> int:
    return result.promising_candidates_hamming_distance


def get_kendall_tau_correlation(
    result: ModelMatchingErrorResult | HumanMatchingErrorResult,
) -> float:
    return result.candidate_places_kendall_tau_correlation


def get_better_or_equal_percentage(
    job_model_matching_error_result: ModelMatchingErrorResult,
    job_human_matching_error_results: tuple[HumanMatchingErrorResult, ...],
    getter_callback: typing.Callable[
        [typing.Union[ModelMatchingErrorResult, HumanMatchingErrorResult]], int | float
    ],
    higher_is_better: bool,
) -> float:
    model_value = getter_callback(job_model_matching_error_result)
    human_values = map(getter_callback, job_human_matching_error_results)
    if higher_is_better:
        return statistics.mean([1 if model_value >= x else 0 for x in human_values])
    else:
        return statistics.mean([1 if model_value <= x else 0 for x in human_values])


def compute_mean_human_matching_error_result(
    human_job_matching_error_result: tuple[HumanMatchingErrorResult, ...]
) -> MeanHumanMatchingErrorResult:
    assert len(human_job_matching_error_result) > 0
    mean_promising_candidates_hamming_distance = statistics.mean(
        [
            x.promising_candidates_hamming_distance
            for x in human_job_matching_error_result
        ]
    )
    mean_candidate_places_kendall_tau_correlation = statistics.mean(
        [
            x.candidate_places_kendall_tau_correlation
            for x in human_job_matching_error_result
        ]
    )
    return MeanHumanMatchingErrorResult(
        job_name=human_job_matching_error_result[0].job_name,
        promising_candidates_hamming_distance=mean_promising_candidates_hamming_distance,
        candidate_places_kendall_tau_correlation=mean_candidate_places_kendall_tau_correlation,
    )


def produce_evaluation_output() -> MatchingResult:
    human_matching_result = load_result_from_responses_csv_file()
    mean_human_matching_result = compute_mean_human_matching_result(
        human_matching_result
    )
    human_matching_error_result = compute_human_matching_error_result(
        mean_human_matching_result, human_matching_result
    )
    model_matching_result = get_model_matching_result(mean_human_matching_result)
    model_matching_error_result = compute_model_matching_error_result(
        mean_human_matching_result, model_matching_result
    )
    matching_result: MatchingResult = {}
    for job_name, mean_human_matching_value in mean_human_matching_result.items():
        job_model_matching_result = model_matching_result[job_name]
        job_model_matching_error_result = model_matching_error_result[job_name]
        job_human_matching_error_results = human_matching_error_result[job_name]
        mean_human_seconds_taken = mean_human_matching_value.minutes_taken * 60
        time_savings_percentage = (
            mean_human_seconds_taken - job_model_matching_result.seconds_taken
        ) / mean_human_seconds_taken
        filtered_model_candidates = set(
            job_model_matching_result.candidate_places.values()
        ) - set(job_model_matching_result.promising_candidates)
        filtered_model_candidate_amount = len(filtered_model_candidates)
        if filtered_model_candidate_amount == 0:
            filter_accuracy = 0.0
        else:
            filter_accuracy = (
                filtered_model_candidate_amount
                - len(
                    filtered_model_candidates.intersection(
                        mean_human_matching_value.promising_candidates
                    )
                )
            ) / filtered_model_candidate_amount
        model_ranking_better_or_equal_than_human_percentage = (
            get_better_or_equal_percentage(
                job_model_matching_error_result,
                job_human_matching_error_results,
                get_kendall_tau_correlation,
                True,
            )
        )
        model_categorization_better_or_equal_than_human_percentage = (
            get_better_or_equal_percentage(
                job_model_matching_error_result,
                job_human_matching_error_results,
                get_hamming_distance,
                False,
            )
        )
        job_matching_result = JobMatchingResult(
            job_name=job_name,
            mean_human_evaluation=MeanHumanMatchingEvaluation(
                mean_human_result=mean_human_matching_value,
                mean_human_error_result=compute_mean_human_matching_error_result(
                    human_matching_error_result[job_name]
                ),
            ),
            human_matching_evaluation=HumanMatchingEvaluation(
                human_results=human_matching_result[job_name],
                human_error_results=human_matching_error_result[job_name],
            ),
            ai_model_matching_evaluation=ModelMatchingEvaluation(
                ai_model_result=model_matching_result[job_name],
                ai_model_error_result=model_matching_error_result[job_name],
            ),
            ai_model_metrics=ModelMetrics(
                ai_model_ranking_better_or_equal_than_human_percentage=model_ranking_better_or_equal_than_human_percentage,
                ai_model_categorization_better_or_equal_than_human_percentage=model_categorization_better_or_equal_than_human_percentage,
                time_savings_percentage=time_savings_percentage,
                candidates_filtered_by_model=filtered_model_candidate_amount,
                filter_accuracy=filter_accuracy,
            ),
        )
        matching_result[job_name] = job_matching_result
    create_matching_result_output(matching_result)
    return matching_result
