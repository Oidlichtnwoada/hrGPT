import json
import typing


def extract_json_object_from_string(text: str) -> dict[str, typing.Any]:
    json_start_string = text.find("{")
    json_end_string = text.rfind("}")
    if json_start_string != -1 and json_end_string != -1:
        json_string = text[json_start_string : json_end_string + 1]
        return json.loads(json_string, strict=False)
    else:
        raise ValueError
