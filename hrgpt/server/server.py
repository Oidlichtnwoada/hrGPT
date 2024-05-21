import base64
import typing

import uvicorn
from fastapi import FastAPI, UploadFile, HTTPException, Header

from hrgpt.scoring.scoring import score_applicants
from hrgpt.utils.config_utils import AppConfigFactory
from hrgpt.utils.file_utils import convert_upload_file_to_file
from hrgpt.utils.init_utils import initialize_app
from hrgpt.utils.type_utils import ScoreWorkload, File, ApplicantMatch

app = FastAPI()


@app.post("/match")
async def match_files(
    files: list[UploadFile],
    openai_api_key_base64: typing.Annotated[
        str | None, Header(convert_underscores=False)
    ] = None,
    google_translate_service_account_base64: typing.Annotated[
        str | None, Header(convert_underscores=False)
    ] = None,
) -> dict[str, tuple[list[dict[str, typing.Any]], dict[str, ApplicantMatch]]]:
    if openai_api_key_base64 is None or google_translate_service_account_base64 is None:
        raise HTTPException(
            status_code=400,
            detail="Both required keys must be provided",
        )
    AppConfigFactory.set_openai_api_key(
        base64.b64decode(openai_api_key_base64).decode("utf-8")
    )
    AppConfigFactory.set_google_translate_service_account(
        base64.b64decode(google_translate_service_account_base64).decode("utf-8")
    )
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two files must be supplied",
        )
    job_file = await convert_upload_file_to_file(files[0])
    cv_files: tuple[File, ...] = ()
    for file in files[1:]:
        cv_files += (await convert_upload_file_to_file(file),)
    score_workload = ScoreWorkload(job_file=job_file, cv_files=cv_files)
    score_result = score_applicants((score_workload,))
    result_dict: dict[
        str, tuple[list[dict[str, typing.Any]], dict[str, ApplicantMatch]]
    ] = {}
    for job_name, job_result in score_result.items():
        result_dict[job_name] = (job_result[0].to_dicts(), job_result[1])
    return result_dict


if __name__ == "__main__":
    # init the app
    initialize_app()
    # start the server
    uvicorn.run(app, host="0.0.0.0", port=4444)
