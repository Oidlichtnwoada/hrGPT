import collections
import statistics
import typing

import pandas
import rbo

from hrgpt.evaluation.csv_loader import load_result_from_responses_csv_file
from hrgpt.utils.type_utils import (
    CompleteHumanMatchingResult,
    CompleteMeanHumanMatchingResult,
    MeanHumanMatchingResult,
    RankingPlace,
    CompleteHumanMatchingErrorResult,
    HumanMatchingErrorResult,
)

T = typing.TypeVar("T")


def compute_mean_set(sets: tuple[set[T]]) -> set[T]:
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
    rankings: tuple[dict[RankingPlace, T]]
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
        result[index + 1] = name
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


def compute_rank_biased_overlap(
    first_ranking: dict[RankingPlace, T],
    second_ranking: dict[RankingPlace, T],
    p: float,
) -> float:
    first_ranking_values_in_order = [
        first_ranking[key] for key in sorted(first_ranking.keys())
    ]
    second_ranking_values_in_order = [
        second_ranking[key] for key in sorted(second_ranking.keys())
    ]
    similarity_measure = rbo.RankingSimilarity(
        first_ranking_values_in_order, second_ranking_values_in_order
    ).rbo(p=p)
    return similarity_measure


def compute_human_matching_error_result(
    mean_human_matching_result: CompleteMeanHumanMatchingResult,
    human_matching_result: CompleteHumanMatchingResult,
    p: float = 0.5,
) -> CompleteHumanMatchingErrorResult:
    result: CompleteHumanMatchingErrorResult = collections.defaultdict(tuple)
    for job_name, human_matching_results in human_matching_result.items():
        mean_human_job_matching = mean_human_matching_result[job_name]
        for human_matching_result in human_matching_results:
            error = HumanMatchingErrorResult(
                human_id=human_matching_result.human_id,
                job_name=job_name,
                promising_candidates_hamming_distance=compute_hamming_distance(
                    mean_human_job_matching.promising_candidates,
                    human_matching_result.promising_candidates,
                ),
                candidate_places_rank_biased_overlap_similarity=compute_rank_biased_overlap(
                    mean_human_job_matching.candidate_places,
                    human_matching_result.candidate_places,
                    p,
                ),
            )
            result[job_name] += (error,)
    return result


def produce_evaluation_output() -> None:
    human_matching_result = load_result_from_responses_csv_file()
    mean_human_matching_result = compute_mean_human_matching_result(
        human_matching_result
    )
    human_matching_error_result = compute_human_matching_error_result(
        mean_human_matching_result, human_matching_result
    )
