from pydantic import BaseModel


class RowError(BaseModel):
    row: int  # spreadsheet row number (header = 1)
    error: str


class ImportResult(BaseModel):
    total_rows: int
    created: int
    updated: int
    failed: int
    errors: list[RowError]
