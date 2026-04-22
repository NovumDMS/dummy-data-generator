from pathlib import Path
import csv
import zipfile
from sqlalchemy.orm import Session

import logging
logger = logging.getLogger(__name__)

def generate_tsv_file(data: list[dict], file_prefix: str) -> None:
    """Generate a tab-delimited TSV file under `tsv_files`.

    The file name will be `<file_prefix>_<import_set_no>.tsv`, e.g.
    `SOH_123.tsv` for header rows or `SOL_123.tsv` for line rows.
    """

    if not data:
        logger.info(f"No data provided for {file_prefix} TSV generation. Skipping file creation.")
        return

    first_row = data[0]
    import_set_no = first_row.get("import_set_no", "unknown")

    # Preserve column order based on the first row
    columns = list(first_row.keys())

    # Resolve project root (two levels up: app/routes -> app -> project root)
    project_root = Path(__file__).resolve().parents[2]
    if not project_root.exists():
        logger.error(f"Project root directory not found at {project_root}. Cannot generate TSV file.")
        raise FileNotFoundError(f"Project root directory not found at {project_root}")

    tsv_dir = project_root / "tsv_files"
    if file_prefix == "SOHPLAY" or file_prefix == "SOLPLAY":
        tsv_dir = tsv_dir / "sales_orders"
    elif file_prefix == "POHPLAY" or file_prefix == "POLPLAY":
        tsv_dir = tsv_dir / "purchase_orders"
    tsv_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{file_prefix}_{import_set_no}.txt"
    file_path = tsv_dir / file_name

    # Write TSV with tab delimiter
    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        for row in data:
            writer.writerow([row.get(col, "") for col in columns])

def zip_orders(tsv_dir: Path, output_zip: Path) -> Path:
    files_to_delete = []

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in (tsv_dir / "sales_orders").glob("*.txt"):
            z.write(file, arcname=f"Sales Orders/{file.name}")
            files_to_delete.append(file)

        for file in (tsv_dir / "purchase_orders").glob("*.txt"):
            z.write(file, arcname=f"Purchase Orders/{file.name}")
            files_to_delete.append(file)

    logger.info(f"Created zip file at {output_zip} containing {len(files_to_delete)} TSV files. Deleting files from disk now.")
    for file in files_to_delete:
        file.unlink()

    return output_zip
    