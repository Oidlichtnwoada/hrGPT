import collections
import concurrent.futures
import functools
import logging
import os
import pathlib

import polars as pl

from hrgpt.extraction import get_requirements_from_job_description, DEFAULT_REQUIREMENT_TYPE_DEFINITIONS
from hrgpt.matcher import match_job_requirements_to_candidate_cv, DEFAULT_REQUIREMENT_TYPE_WEIGHTINGS, ApplicantMatch
from hrgpt.utils import get_applicant_document_paths, dumps


def score_applicants_for_job_path(job_path: str, candidate_paths: list[str]) -> tuple[ApplicantMatch]:
    job_requirements = get_requirements_from_job_description(job_path, DEFAULT_REQUIREMENT_TYPE_DEFINITIONS)
    matching_function = functools.partial(match_job_requirements_to_candidate_cv,
                                          job_requirements,
                                          DEFAULT_REQUIREMENT_TYPE_DEFINITIONS,
                                          DEFAULT_REQUIREMENT_TYPE_WEIGHTINGS, )
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return tuple(executor.map(matching_function, candidate_paths))


def score_applicants(job_ids: tuple[int, ...], candidate_ids: tuple[int, ...]) -> dict[str, dict[str, ApplicantMatch]]:
    arguments = list(get_applicant_document_paths(job_ids, candidate_ids).items())
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mapped_arguments = tuple(executor.map(lambda x: score_applicants_for_job_path(*x), arguments))
    result_dict = collections.defaultdict(dict)
    for arguments, match_results in zip(arguments, mapped_arguments):
        job_path = arguments[0]
        for candidate_path, match_result in zip(arguments[1], match_results):
            result_dict[job_path][candidate_path] = match_result
    create_output_files(result_dict)
    return result_dict


def create_output_files(score_result: dict[str, dict[str, ApplicantMatch]], log_result: bool = True) -> None:
    for job_path, match_results in score_result.items():
        # create the result directory
        result_directory = os.path.join(os.path.dirname(job_path), 'result')
        os.makedirs(result_directory, exist_ok=True)
        # make the resulting dataframe per job
        job_df_parts = []
        for candidate_path, match_result in match_results.items():
            # append the result part of the applicant
            job_df_parts.append(pl.DataFrame({
                'candidate': [candidate_path],
                'score': [match_result.total_score],
                'promising': [match_result.promising_result.promising],
                'explanation': [match_result.promising_result.explanation],
            }))
            # save the applicants data as json in the result directory
            match_result_json = dumps(match_result)
            candidate_result_path = os.path.join(result_directory, f'match_result_{pathlib.Path(candidate_path).stem}.json')
            with open(candidate_result_path, 'w') as file:
                file.write(match_result_json)
        job_df = pl.concat(job_df_parts).sort('promising', 'score', descending=(True, True))
        # save the result table in the result directory
        job_df.write_csv(os.path.join(result_directory, 'job_match_result.csv'))
        if log_result:
            logging.info(f'\n\nMatching results for the job \'{job_path}\':\n{job_df}\n')
