import typing

import uvicorn
from fastapi import FastAPI, UploadFile, HTTPException

from hrgpt.scoring.scoring import score_applicants
from hrgpt.utils.file_utils import convert_upload_file_to_file
from hrgpt.utils.init_utils import initialize_app
from hrgpt.utils.type_utils import ScoreWorkload, File, ApplicantMatch

app = FastAPI()


@app.post("/match")
async def match_files(
    files: list[UploadFile],
) -> dict[str, tuple[list[dict[str, typing.Any]], dict[str, ApplicantMatch]]]:
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
