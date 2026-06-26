"""Fetch the raw Online Retail II dataset. Raw files are gitignored.

Provenance: the canonical source is the UCI Machine Learning Repository,
dataset 502 (DOI 10.24432/C5CG6D), released under CC BY 4.0. UCI's direct
file server is heavily throttled (~15 KB/s, no range support), so we fetch a
byte-for-byte CC BY 4.0 redistribution of the same 1,067,371-row table hosted
on GitHub. Both carry identical data; see ATTRIBUTION.md.
"""

from __future__ import annotations

from pathlib import Path

import requests

# CC BY 4.0 redistribution of UCI dataset 502 (full 2009-2011 table, .rda).
DATA_URL = (
    "https://raw.githubusercontent.com/allanvc/onlineretail2/master/data/onlineretail2.rda"
)
# Canonical upstream (documented; throttled, not used for automated fetch).
UCI_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"

RAW_DIR = Path("data/raw")
RDA_NAME = "onlineretail2.rda"


def download_raw(dest_dir: Path = RAW_DIR, *, force: bool = False) -> Path:
    """Download the raw dataset into ``dest_dir``; return its path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    rda_path = dest_dir / RDA_NAME
    if rda_path.exists() and not force:
        return rda_path

    resp = requests.get(DATA_URL, timeout=120)
    resp.raise_for_status()
    rda_path.write_bytes(resp.content)
    return rda_path
