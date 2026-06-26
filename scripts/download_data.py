"""CLI: download the raw Online Retail II dataset into data/raw/ (gitignored)."""

from __future__ import annotations

from real_retail.data.download import download_raw


def main() -> None:
    path = download_raw()
    print(f"Raw dataset ready at: {path}")


if __name__ == "__main__":
    main()
