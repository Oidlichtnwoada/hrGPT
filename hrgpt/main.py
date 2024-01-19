import argparse
import logging
import os

from dotenv import load_dotenv

from hrgpt.anonymization import anonymize_applicant_documents
from hrgpt.scoring import score_applicants
from hrgpt.utils import get_environment_file_path


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=str, default='scoring')
    parser.add_argument('--job', type=int, default=[1], nargs='+')
    parser.add_argument('--candidate', type=int, default=[1], nargs='+')
    return parser.parse_args()


def main() -> None:
    load_dotenv(dotenv_path=get_environment_file_path())
    logging.basicConfig(level=logging.getLevelName(os.getenv('LOGGING_LEVEL')))
    args = get_args()
    if args.target == 'scoring':
        score_applicants(tuple(args.job), tuple(args.candidate))
    elif args.target == 'anonymization':
        anonymize_applicant_documents()
    else:
        raise RuntimeError


if __name__ == '__main__':
    main()
