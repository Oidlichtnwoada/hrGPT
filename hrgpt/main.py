import argparse

from hrgpt.anonymization import anonymize_applicant_documents


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=str, default='server')
    return parser.parse_args()


def main() -> None:
    args = get_args()
    if args.target == 'server':
        pass
    elif args.target == 'anonymization':
        anonymize_applicant_documents()
    else:
        raise RuntimeError


if __name__ == '__main__':
    main()
