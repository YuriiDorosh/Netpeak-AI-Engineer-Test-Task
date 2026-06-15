from io import BytesIO

import pandas as pd

REQUIRED_COLUMNS = {"id", "channel", "timestamp", "raw_text"}


def read_csv(content: bytes) -> list[dict]:
    try:
        df = pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    if df.empty:
        raise ValueError("CSV contains no data rows")

    before = len(df)
    df = df.dropna(subset=["raw_text"])
    dropped = before - len(df)
    if dropped:
        import logging
        logging.getLogger(__name__).warning("Dropped %d rows with empty raw_text", dropped)

    return df.to_dict(orient="records")
