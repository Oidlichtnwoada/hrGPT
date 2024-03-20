import itertools
import typing


T = typing.TypeVar("T")


def chunked(
    iterable: typing.Iterable[T], chunk_size: int
) -> typing.Generator[tuple[T, ...], None, None]:
    iterator = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(iterator, chunk_size))
        if not chunk:
            break
        yield chunk
