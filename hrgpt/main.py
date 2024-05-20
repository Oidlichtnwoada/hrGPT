from hrgpt.anonymization.anonymization import anonymize_applicant_documents
from hrgpt.evaluation.evaluation import produce_evaluation_output
from hrgpt.scoring.scoring import score_applicants
from hrgpt.utils.argument_utils import get_args
from hrgpt.utils.init_utils import initialize_app
from hrgpt.utils.path_utils import get_score_workloads


def main() -> None:
    # init the app
    initialize_app()
    # get the arguments
    args = get_args()
    # start the correct execution path
    if args.target == "scoring":
        score_applicants(get_score_workloads(args.job, args.candidate))
    elif args.target == "anonymization":
        anonymize_applicant_documents()
    elif args.target == "evaluation":
        produce_evaluation_output()
    else:
        raise RuntimeError


if __name__ == "__main__":
    main()
