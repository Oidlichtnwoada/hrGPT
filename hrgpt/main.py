from hrgpt.anonymization.anonymization import anonymize_applicant_documents
from hrgpt.config.config import AppConfigFactory
from hrgpt.logger.logger import LoggerFactory
from hrgpt.scoring.scoring import score_applicants
from hrgpt.utils.argument_utils import get_args
from hrgpt.utils.config_utils import get_app_config_from_json_file
from hrgpt.utils.polars_utils import configure_polars


def main() -> None:
    # get the arguments
    args = get_args()
    # load the configuration and the secrets
    app_config = get_app_config_from_json_file(args.config, args.secrets)
    # configure polars
    configure_polars(app_config.generic_config.polars_config)
    # configure loggers
    LoggerFactory.initialize_loggers(app_config.generic_config.logging_config)
    # initialize the app config factory
    AppConfigFactory.initialize_app_config(app_config)
    # start the correct execution path
    if args.target == 'scoring':
        score_applicants(args.job, args.candidate)
    elif args.target == 'anonymization':
        anonymize_applicant_documents()
    else:
        raise RuntimeError


if __name__ == '__main__':
    main()
