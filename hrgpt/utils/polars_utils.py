import polars as pl

from hrgpt.config.config import PolarsConfiguration


def configure_polars(config: PolarsConfiguration) -> None:
    pl.Config.set_fmt_str_lengths(config.max_print_string_length)
    pl.Config.set_tbl_hide_dataframe_shape(config.disable_shape_print)
