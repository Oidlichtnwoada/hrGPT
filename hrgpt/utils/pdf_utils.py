import os
import shutil

import fitz

from hrgpt.utils.path_utils import get_random_file_name


def clean_pdf_document(
    pdf_document_path: str,
    clean: bool = True,
    compress: bool = True,
    linearize: bool = True,
    prettify: bool = True,
) -> None:
    kwargs = {}
    if clean:
        kwargs.update({"garbage": 4, "clean": True})
    if compress:
        kwargs.update({"deflate": True})
    else:
        kwargs.update({"expand": 255})
    if linearize:
        kwargs.update({"linear": True})
    if prettify:
        kwargs.update({"pretty": True})
    random_file_name = get_random_file_name()
    with fitz.open(pdf_document_path) as pdf_document:
        pdf_document.save(random_file_name, **kwargs, encryption=fitz.PDF_ENCRYPT_NONE)
    shutil.copyfile(random_file_name, pdf_document_path)
    os.remove(random_file_name)


def remove_links(pdf_document_path: str) -> None:
    with fitz.open(pdf_document_path) as pdf_document:
        for page in pdf_document:
            links = page.get_links()
            for link in links:
                page.delete_link(link)
        pdf_document.save(
            pdf_document_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP
        )
