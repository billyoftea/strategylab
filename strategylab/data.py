"""Qlib initialisation + thin data-access wrappers."""
from __future__ import annotations

import os
from typing import Iterable

import qlib
from qlib.data import D

_initialized = False


def init_qlib(provider_uri: str | None = None, region: str = "cn") -> None:
    """Idempotently initialise Qlib. Provider URI defaults to the cn_data already
    downloaded by RD-Agent at ~/.qlib/qlib_data/cn_data (overridable via env)."""
    global _initialized
    if _initialized:
        return
    provider_uri = provider_uri or os.environ.get(
        "QLIB_PROVIDER_URI", "~/.qlib/qlib_data/cn_data"
    )
    qlib.init(provider_uri=provider_uri, region=region)
    _initialized = True


def instruments(market: str = "csi300"):
    init_qlib()
    return D.instruments(market=market)


def load_features(
    fields: list[str],
    market: str = "csi300",
    start_time: str = "2015-01-01",
    end_time: str = "2024-12-31",
):
    """Load a MultiIndex (instrument, datetime) DataFrame of the given Qlib fields/
    expressions for all instruments in `market`."""
    init_qlib()
    inst = D.instruments(market=market)
    return D.features(inst, fields, start_time=start_time, end_time=end_time)
