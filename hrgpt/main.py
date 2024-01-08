import argparse

from dotenv import load_dotenv

from hrgpt.anonymization import anonymize_applicant_documents
from hrgpt.utils import get_environment_file_path


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=str, default='server')
    return parser.parse_args()


def main() -> None:
    load_dotenv(dotenv_path=get_environment_file_path())
    args = get_args()
    if args.target == 'server':
        pass
    elif args.target == 'anonymization':
        anonymize_applicant_documents()
    else:
        raise RuntimeError


if __name__ == '__main__':
    main()
