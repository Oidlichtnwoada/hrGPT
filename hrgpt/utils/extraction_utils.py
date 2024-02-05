def extract_json_object_string_from_string(text: str) -> str:
    json_start_string = text.find("{")
    json_end_string = text.rfind("}")
    if json_start_string != -1 and json_end_string != -1:
        return text[json_start_string : json_end_string + 1]
    else:
        raise ValueError
