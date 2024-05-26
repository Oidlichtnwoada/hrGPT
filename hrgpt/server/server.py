import base64
import typing

import uvicorn
from fastapi import FastAPI, UploadFile, HTTPException, Header

from hrgpt.scoring.scoring import score_applicants
from hrgpt.utils.config_utils import AppConfigFactory
from hrgpt.utils.file_utils import convert_upload_file_to_file
from hrgpt.utils.init_utils import initialize_app
from hrgpt.utils.type_utils import ScoreWorkload, File, ApplicantMatch, ApiMatchResult


def get_server() -> FastAPI:
    app = FastAPI()

    @app.post("/match")
    async def match_cvs_to_job(
        job_files: list[UploadFile],
        cv_files: list[UploadFile],
        openai_api_key_base64: typing.Annotated[
            str | None, Header(convert_underscores=False)
        ] = None,
        google_translate_service_account_base64: typing.Annotated[
            str | None, Header(convert_underscores=False)
        ] = None,
        output_language_base64: typing.Annotated[
            str | None, Header(convert_underscores=False)
        ] = None,
    ) -> dict[str, tuple[list[dict[str, typing.Any]], dict[str, ApplicantMatch]]]:
        # check if all required headers are there
        if (
            openai_api_key_base64 is None
            or google_translate_service_account_base64 is None
            or output_language_base64 is None
        ):
            raise HTTPException(
                status_code=400,
                detail="All required headers must be provided",
            )
        # check if exactly one job is provided
        if len(job_files) != 1:
            raise HTTPException(
                status_code=400,
                detail="Exactly one job file must be provided",
            )
        # check if at least one CV is provided
        if len(cv_files) < 1:
            raise HTTPException(
                status_code=400,
                detail="At least one CV file must be provided",
            )
        # set configuration parameters
        AppConfigFactory.set_openai_api_key(
            base64.b64decode(openai_api_key_base64).decode("utf-8")
        )
        AppConfigFactory.set_google_translate_service_account(
            base64.b64decode(google_translate_service_account_base64).decode("utf-8")
        )
        AppConfigFactory.set_output_language(
            base64.b64decode(output_language_base64).decode("utf-8")
        )
        # extract files from form data
        job_file = await convert_upload_file_to_file(job_files[0])
        cv_files_tuple: tuple[File, ...] = ()
        for file in cv_files:
            cv_files_tuple += (await convert_upload_file_to_file(file),)
        # create the score workload and get the result
        score_workload = ScoreWorkload(job_file=job_file, cv_files=cv_files_tuple)
        score_result = score_applicants((score_workload,))
        # build the response
        result_dict: dict[str, ApiMatchResult] = {}
        for job_name, job_result in score_result.items():
            result_dict[job_name] = ApiMatchResult(
                overview_result=job_result[0].to_dicts(), exact_result=job_result[1]
            )
        # send the response
        return result_dict

    return app


def main() -> None:
    # init the app
    initialize_app()
    # get the app
    app = get_server()
    # start the server
    uvicorn.run(app, host="0.0.0.0", port=80)


if __name__ == "__main__":
    main()
