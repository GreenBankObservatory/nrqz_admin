import tempfile

import pyexcel

import django

django.setup()

from django.db import transaction

from tools.strip_excel_non_data import strip_excel_file
from tools.excel_importer import ExcelCollectionImporter


@transaction.atomic
def import_excel_file(input_path):
    print(f"Processing {input_path}")
    with tempfile.TemporaryDirectory() as tmpdirname:
        path_to_stripped_file = strip_excel_file(
            input_path=input_path, output_path=tmpdirname
        )
        print("Successfully stripped non-data rows")
        eci = ExcelCollectionImporter([path_to_stripped_file], durable=True)

        batch_audits = eci.process()
        eci.report.process()
        print("Successfully processed all Batch data")

    print(f"Created {len(batch_audits)} BatchAudits:")
    for batch_audit in batch_audits:
        print(f"  {batch_audit.id} {batch_audit}")

    # transaction.set_rollback(True)
    # print("Rolling back...")


def main():
    import_excel_file(
        # "/data/sandboxes/tchamber/nrqz/excel/allexcel/2018.02.09 Autopath DATA SUMMARY.xlsm"
        "/home/sandboxes/tchamber/projects/nrqz_admin/excel/all_fully_stripped/stripped_data_only_10023_Autopath_DATA_SUMMARY.xlsm"
    )


if __name__ == "__main__":
    main()
