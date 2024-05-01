import typing

import scipy

from hrgpt.utils.type_utils import RankingPlace

T = typing.TypeVar("T")


def clamp_float(value: float, min_value: float, max_value: float) -> float:
    return min(max_value, max(min_value, value))


def clamp_int(value: int, min_value: int, max_value: int) -> int:
    return min(max_value, max(min_value, value))


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
