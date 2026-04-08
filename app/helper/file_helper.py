from pathlib import Path
import csv
import zipfile
from sqlalchemy.orm import Session

import logging
logger = logging.getLogger(__name__)

def generate_tsv_file(data: list[dict], db: Session, file_prefix: str) -> None:
    """Generate a tab-delimited TSV file under `tsv_files`.

    The file name will be `<file_prefix>_<import_set_no>.tsv`, e.g.
    `SOH_123.tsv` for header rows or `SOL_123.tsv` for line rows.
    """

    if not data:
        return

    first_row = data[0]
    import_set_no = first_row.get("import_set_no", "unknown")

    # Preserve column order based on the first row
    columns = list(first_row.keys())

    # Resolve project root (two levels up: app/routes -> app -> project root)
    project_root = Path(__file__).resolve().parents[2]
    tsv_dir = project_root / "tsv_files"
    if file_prefix == "SOH" or file_prefix == "SOL":
        tsv_dir = tsv_dir / "sales_orders"
    elif file_prefix == "POH" or file_prefix == "POL":
        tsv_dir = tsv_dir / "purchase_orders"
    tsv_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{file_prefix}_{import_set_no}.tsv"
    file_path = tsv_dir / file_name

    # Write TSV with tab delimiter
    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        for row in data:
            writer.writerow([row.get(col, "") for col in columns])

    logger.info(f"Generated TSV file at {file_path}")

def zip_orders(tsv_dir: Path, output_zip: Path) -> Path:
    files_to_delete = []

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in (tsv_dir / "sales_orders").glob("*.tsv"):
            z.write(file, arcname=f"Sales Orders/{file.name}")
            files_to_delete.append(file)

        for file in (tsv_dir / "purchase_orders").glob("*.tsv"):
            z.write(file, arcname=f"Purchase Orders/{file.name}")
            files_to_delete.append(file)

    for file in files_to_delete:
        file.unlink()

    return output_zip
    