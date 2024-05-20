import pathlib

from fastapi import UploadFile

from hrgpt.utils.type_utils import File, DocumentFileType


def convert_path_to_file(path: str) -> File:
    path_object = pathlib.Path(path)
    with open(path_object, "rb") as file:
        content = file.read()
    return File(
        name=path_object.stem,
        type=DocumentFileType(path_object.suffix),
        content=content,
    )


async def convert_upload_file_to_file(upload_file: UploadFile) -> File:
    path_object = pathlib.Path(str(upload_file.filename))
    content = await upload_file.read()
    return File(
        name=path_object.stem,
        type=DocumentFileType(path_object.suffix),
        content=content,
    )
