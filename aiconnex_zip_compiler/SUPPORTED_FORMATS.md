# AIConnex Compiler — Supported File Formats Registry

The `aiconnex_zip_compiler` plugin architecture operates on a static, deterministic plugin registry.
Format support is defined by registered parsers in `aiconnex_zip_compiler/plugins/parsers/`.

## 📦 Supported Formats

| Category | Format / Extension | Parser Plugin | Notes |
|---|---|---|---|
| **Tabular** | `.csv`, `.tsv` | `csv_parser` | Standard delimiter separated values |
| **Text** | `.txt`, `.dat` | `text_delimited_autodetect_parser` | Auto-detects whitespace, tab, pipe, or comma delimiters |
| **Excel** | `.xlsx`, `.xls` | `scada_excel_parser` | Multi-row merged headers, SCADA DPR reports, multi-sheet workbook parsing |
| **Semi-structured** | `.json`, `.jsonl` | `json_parser` | Nested or flat JSON structures, newline-delimited JSON |
| **Columnar Storage** | `.parquet` | `parquet_parser` | Apache Parquet datasets |
| **Scientific Binary** | `.mat` | `mat_parser` | MATLAB v5/v7 struct arrays and matrix dumps |
| **HDF5 Binary** | `.hdf5`, `.h5` | `hdf5_parser` | Hierarchical Data Format containers |
| **Industrial / LabView** | `.tdms` | `tdms_parser` | National Instruments LabVIEW TDMS telemetry streams |
| **Embedded Database** | `.db`, `.sqlite` | `sqlite_parser` | SQLite database table extraction |
| **Structured Markup** | `.xml` | `xml_parser` | XML tag extraction and flattening |

---

## 🚫 Unsupported Formats Policy

If a dataset archive contains an unrecognized file format outside of the scope listed above:
1. The compiler will **fail-closed** and raise an `UnsupportedFormatError`.
2. Dynamic code generation or sandbox plugin generation has been **permanently disabled**.
3. Users must manually convert unsupported formats to a supported format (e.g. `.csv`, `.xlsx`, `.parquet`) prior to ingestion.
