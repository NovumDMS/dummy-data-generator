from pathlib import Path
import csv
import zipfile

import logging
logger = logging.getLogger(__name__)

def _append_files_to_master(source_files: list[Path], master_file: Path) -> int:
    """
    Append all rows from source files into a single master file.
    This requires all information to be written to files already.
    :param source_files: List of source file paths to append
    :param master_file: Path to the master file
    :return: Number of rows written to the master file
    """
    rows_written = 0
    with master_file.open("w", encoding="utf-8", newline="") as out_f:
        for file_path in source_files:
            with file_path.open("r", encoding="utf-8", newline="") as in_f:
                for line in in_f:
                    out_f.write(line)
                    rows_written += 1
    return rows_written

def generate_tsv_file(data: list[dict], file_prefix: str) -> None:
    """
    Adds rows for each individual order to a master file containing all information
    The file is labeled with the given as {prefix}_0.txt since we are not splitting into multiple files, but this allows for future expansion if needed.
    The master file is overwritten each time, but that's acceptable since it's only used for immediate zipping and download and not stored long-term.
    """

    if not data:
        logger.info(f"No data provided for {file_prefix} TSV generation. Skipping file creation.")
        return

    first_row = data[0]

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

    file_name = f"{file_prefix}_0.txt"
    file_path = tsv_dir / file_name

    # Write TSV with tab delimiter
    with file_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
             
        # Write data rows
        for row in data:
            writer.writerow([row.get(col, "") for col in columns])

def zip_orders(tsv_dir: Path, output_zip: Path) -> Path:
    """
    This function zips all generated order TSV files into a single zip file for download, then deletes the original TSV files.
    The zip file path must be returned so it can be sent via API response.
    This will be overwritten each generation, but that's acceptable since it's only used for immediate download and not stored long-term.

    :param tsv_dir: Path to the directory containing TSV files
    :param output_zip: Path to the output zip file
    :return: Path to the created zip file
    """
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
    