import collections
import pathlib

import pandas
import pendulum

from hrgpt.utils.iterable_utils import chunked
from hrgpt.utils.path_utils import (
    get_responses_csv_path,
    get_job_folder_path_by_job_index,
)
from hrgpt.utils.type_utils import (
    HumanMatchingResult,
    RankingPlace,
    CompleteHumanMatchingResult,
)


def get_job_name_by_job_index(job_index: int) -> str:
    job_folder_path = get_job_folder_path_by_job_index(job_index)
    text_file_stems = [x.stem for x in pathlib.Path(job_folder_path).glob("*.txt")]
    if len(text_file_stems) != 1:
        raise RuntimeError
    return text_file_stems[0].strip()


def load_result_from_responses_csv_file() -> CompleteHumanMatchingResult:
    human_matching_result_list: list[HumanMatchingResult] = []
    responses_df = pandas.read_csv(get_responses_csv_path())
    for human_id, human_result_row in responses_df.iterrows():
        timestamp = pendulum.from_format(
            human_result_row.iloc[0].replace("GMT+1", "+01:00"),
            "YYYY/MM/DD hh:mm:ss A Z",
        )
        human_result_row_without_timestamp = human_result_row[1:]
        for index, human_job_result in enumerate(
            chunked(
                zip(
                    human_result_row_without_timestamp.index,
                    human_result_row_without_timestamp,
                ),
                10,
            )
        ):
            job_index = index + 1
            minutes_taken = int(human_job_result[0][1])
            promising_candidates = set(human_job_result[1][1].split(";"))
            candidate_places: dict[RankingPlace, str] = {}
            for applicant_place in human_job_result[2:]:
                candidate_places[applicant_place[1]] = " ".join(
                    applicant_place[0].split(" ")[2:]
                )
            human_matching_result_list.append(
                HumanMatchingResult(
                    human_id=human_id,
                    job_name=get_job_name_by_job_index(job_index),
                    timestamp=timestamp,
                    minutes_taken=minutes_taken,
                    promising_candidates=promising_candidates,
                    candidate_places=candidate_places,
                )
            )
    result: CompleteHumanMatchingResult = collections.defaultdict(tuple)
    for human_matching_result in human_matching_result_list:
        result[human_matching_result.job_name] += (human_matching_result,)
    return result
