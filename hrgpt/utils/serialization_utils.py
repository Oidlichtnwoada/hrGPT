import json

import pydantic


def dumps(x: object, separators: tuple[str, str] = (', ', ': '), indent: int = 4) -> str:
    class ExtendedEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, pydantic.BaseModel):
                return obj.model_dump(mode='json')
            return json.JSONEncoder.default(self, obj)

    return json.dumps(x, ensure_ascii=False, indent=indent, separators=separators, cls=ExtendedEncoder)
