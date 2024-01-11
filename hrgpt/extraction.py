import fitz


def get_pdf_document_text(pdf_document_path: str,
                          replacements: tuple[tuple[str, str]] = ((chr(160), ' '),)) -> str:
    with fitz.open(pdf_document_path) as pdf_document:
        page_texts = []
        for page in pdf_document:
            page_text = page.get_text().strip()
            for search_string, replacement_string in replacements:
                page_text = page_text.replace(search_string, replacement_string)
            page_texts.append(page_text)
        return '\n'.join(page_texts)
