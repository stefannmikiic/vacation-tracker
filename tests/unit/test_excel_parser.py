from io import BytesIO

from openpyxl import Workbook

from vacation_tracker.imports.parsers.excel_parser import read_excel_rows


def test_read_excel_rows() -> None:
    workbook = Workbook()
    sheet = workbook.active

    sheet.append(
        [
            "Employee Email",
            "Employee Password",
        ]
    )

    sheet.append(
        [
            "test@example.com",
            "Password123!",
        ]
    )

    buffer = BytesIO()
    workbook.save(buffer)

    rows = read_excel_rows(buffer.getvalue())

    assert rows == [
        [
            "Employee Email",
            "Employee Password",
        ],
        [
            "test@example.com",
            "Password123!",
        ],
    ]