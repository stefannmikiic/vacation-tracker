"""CSV tabular reader."""

import csv
import io


def read_csv_rows(content: bytes) -> list[list[str]]:
    """Decode CSV bytes into a list of string rows."""
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    return [[cell.strip() for cell in row] for row in reader]
