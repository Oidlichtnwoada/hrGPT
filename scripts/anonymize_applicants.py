from utils import get_repo_root
from pypdf import PdfReader, PdfWriter

import pathlib
import os

def get_applicant_document_paths() -> list[str]:
    return [os.path.abspath(x) for x in pathlib.Path(os.path.join(get_repo_root(), 'sample_screening_documents')).rglob('candidate_*.pdf') if x.is_file()]

def anonymize_applicant_document(path: str) -> None:
    pdf_reader = PdfReader(stream=path)
    pdf_writer = PdfWriter(clone_from=pdf_reader)
    for page in pdf_writer.pages:
        pass
    pdf_writer.write(path)
    pdf_writer.close()

def main() -> None:
    for applicant_document_path in get_applicant_document_paths():
        anonymize_applicant_document(applicant_document_path)

if __name__ == '__main__':
    main()
