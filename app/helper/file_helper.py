from pathlib import Path
import csv
import zipfile

import logging
logger = logging.getLogger(__name__)


def _append_files_to_master(source_files: list[Path], master_file: Path) -> int:
    """Append all rows from source files into a single master file."""
    rows_written = 0
    with master_file.open("w", encoding="utf-8", newline="") as out_f:
        for file_path in source_files:
            with file_path.open("r", encoding="utf-8", newline="") as in_f:
                for line in in_f:
                    out_f.write(line)
                    rows_written += 1
    return rows_written

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


def generate_master_order_files(tsv_dir: Path) -> None:
    """Create _0 master files by concatenating generated order txt files per prefix."""
    folder_and_prefixes = {
        tsv_dir / "sales_orders": ["SOHPLAY", "SOLPLAY"],
        tsv_dir / "purchase_orders": ["POHPLAY", "POLPLAY"],
    }

    for folder, prefixes in folder_and_prefixes.items():
        if not folder.exists():
            logger.info(f"Skipping master file generation for missing folder: {folder}")
            continue

        for prefix in prefixes:
            master_file = folder / f"{prefix}_0.txt"
            source_files = sorted(
                file_path
                for file_path in folder.glob(f"{prefix}_*.txt")
                if file_path.name != master_file.name
            )

            if not source_files:
                logger.info(f"No source files found for {prefix}. Skipping master file generation.")
                continue

            rows_written = _append_files_to_master(source_files, master_file)
            logger.info(
                f"Generated master file {master_file.name} with {rows_written} rows "
                f"from {len(source_files)} files."
            )

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
    