"""
PyArrow Columnar Memory Converter - In-memory schema and Arrow table conversion.
"""

from typing import Dict, Optional
import pyarrow as pa
import pyarrow.parquet as pq

def create_arrow_table_from_schema(data_dict: Dict[str, list], schema_map: Optional[Dict[str, str]] = None) -> pa.Table:
    """
    Convert dictionary of lists into a PyArrow columnar Table.
    """
    table = pa.Table.from_pydict(data_dict)
    return table

def write_parquet_file(table: pa.Table, output_path: str, compression: str = "SNAPPY") -> str:
    """
    Write PyArrow Table to compressed Parquet storage.
    """
    pq.write_table(table, output_path, compression=compression)
    return output_path
