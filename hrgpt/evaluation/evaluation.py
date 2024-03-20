from hrgpt.evaluation.csv_loader import load_result_from_responses_csv_file


def produce_evaluation_output() -> None:
    human_matching_result = load_result_from_responses_csv_file()
