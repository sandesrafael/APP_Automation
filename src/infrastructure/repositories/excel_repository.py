from typing import List
from src.utils.helpers import ExcelHelper
from .interfaces import IExcelRepository

class ExcelRepository(IExcelRepository):
    def read_sheets(self, path_name_excel: str, sheet_names: List[str], nrows: int = 4, engine: str = 'calamine'):
        return ExcelHelper.read_sheets(path_name_excel, sheet_names, nrows=nrows, engine=engine)

    def read_columns(self, path_name_excel: str, sheet_name: str, col_indexes: List[int], skiprows: int = 3, engine: str = 'calamine'):
        return ExcelHelper.read_columns(path_name_excel, sheet_name, col_indexes, skiprows=skiprows, engine=engine)
