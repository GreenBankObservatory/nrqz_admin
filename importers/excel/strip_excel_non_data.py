#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Strip non-data lines from an Excel or CSV file

This is done removing any rows that do not meet a threshold of populated cells.
That is, if C / L < T -- where C is the number of non-empty cells, L is the length
of the row, and T is the threshold (0 - 1) -- then the row is discarded.

The intent here is to leave only header and data rows, removing random
comments, etc.
"""


import argparse
import os
import re

import pyexcel
from tqdm import tqdm
from xlrd.xldate import XLDateAmbiguous

DEFAULT_PATTERN = r".*\.(xls.?|csv)$"
DEFAULT_THRESHOLD = 0.7
DEFAULT_OVERWRITE = False

MBFACTOR = float(1 << 20)


def get_total_bytes(files):
    return sum(os.path.getsize(file) for file in files)


def strip_excel_directory(
    input_path,
    output_path,
    threshold=DEFAULT_THRESHOLD,
    pattern=DEFAULT_PATTERN,
    overwrite=DEFAULT_OVERWRITE,
):
    files = [
        os.path.join(input_path, f)
        for f in os.listdir(input_path)
        if re.search(pattern, f)
    ]
    total_megabytes = get_total_bytes(files) / MBFACTOR
    progress = tqdm(total=total_megabytes, unit="MB")
    errors = []
    for input_file_path in files:
        tqdm.write(f"Processing {input_file_path}")
        try:
            strip_excel_file(
                input_file_path, output_path, threshold, overwrite=overwrite
            )
        except ValueError as error:
            errors.append(error)
        file_megabytes = os.path.getsize(input_file_path) / MBFACTOR
        progress.update(file_megabytes)
    print(f"Errors: {errors}")


def row_is_invalid(row, threshold=DEFAULT_THRESHOLD):
    invalid_cells = 0
    for cell in row:
        value = cell.value
        if value is None:
            invalid_cells += 1

    if not invalid_cells or invalid_cells / len(row) > threshold:
        # tqdm.write(
        #     f"Found invalid row ({invalid_cells} / {len(row)} {invalid_cells / len(row) * 100}%>"
        #     f"{threshold * 100}% cells invalid): {row}"
        # )
        return True
    return False


def identify_invalid_rows(rows, threshold=DEFAULT_THRESHOLD):
    invalid_row_indices = []
    for ri, row in enumerate(rows):
        if row_is_invalid(row):
            invalid_row_indices.append(ri)

    return invalid_row_indices


def strip_excel_sheet(sheet, threshold=DEFAULT_THRESHOLD):
    """Strip non-data rows from a Sheet -- done in-place!"""

    # Annotate each row with its original index (1-indexed). This
    # is so that we can reference them by this later
    tqdm.write(f"Processing {sheet.name}")

    if not sheet:
        tqdm.write(f"Empty sheet; skipping")
        return

    # For some reason we add a column this way... strange API, but it works.
    # We create a Sheet with a single Column. Sheet expects a 2d list,
    # so we create one here. The range starts at two because the original
    # row numbers are 1-indexed, and the first row (row 1) doesn't get numbered
    # because it contains the header ("Original Row")
    # This will be used later to reference the original row from which the data
    # was imported
    sheet.column += pyexcel.Sheet(
        [["Original Row"], *[[num] for num in range(2, len(sheet) + 1)]]
    )

    orig_num_rows = len(sheet.array)
    # Get the indexes of all invalid rows...
    invalid_row_indices = identify_invalid_rows(sheet.array, threshold)
    for index in sorted(invalid_row_indices, reverse=True):
        # tqdm.write(f"Deleted invalid row {index}")
        # ...then delete them
        # TODO: See http://docs.pyexcel.org/en/latest/sheet.html#how-to-filter-out-empty-rows-in-my-sheet
        # for a potentially cleaner way to do this
        del sheet.row[index]

    num_rows_deleted = orig_num_rows - len(sheet)

    tqdm.write(
        f"Deleted {num_rows_deleted}/{orig_num_rows} rows "
        f"({num_rows_deleted / orig_num_rows * 100:.2f}%)"
    )


def strip_excel_book(book, threshold=DEFAULT_THRESHOLD):
    """Strip non-data rows from a Book -- done in-place!"""

    for sheet in book:
        strip_excel_sheet(sheet, threshold=threshold)


def open_excel_book(input_path):
    try:
        book = pyexcel.get_book(file_name=input_path)
    except ValueError as error:
        raise ValueError(f"Error reading {input_path}") from error

    return book


def save_excel_book(book, output_path):
    return book.save_as(output_path)


def strip_excel_file(
    input_path, output_path, threshold=DEFAULT_THRESHOLD, overwrite=DEFAULT_OVERWRITE
):
    """Save a new Excel file containing only headers and data rows"""

    output_filename = f"{os.path.basename(input_path)}"
    full_output_path = os.path.join(output_path, output_filename)

    if os.path.isfile(full_output_path) and not overwrite:
        tqdm.write(f"{full_output_path} already exists; skipping")
        return None

    tqdm.write("Opening workbook")
    book = open_excel_book(input_path)
    tqdm.write("...done")

    strip_excel_book(book, threshold=threshold)

    save_excel_book(book, full_output_path)
    tqdm.write(f"Wrote {full_output_path}")
    return full_output_path


def main():
    args = parse_args()
    if os.path.isdir(args.input_path):
        strip_excel_directory(
            args.input_path,
            args.output_path,
            threshold=args.threshold,
            pattern=args.pattern,
            overwrite=args.force,
        )
    elif os.path.isfile(args.input_path):
        strip_excel_file(
            args.input_path,
            args.output_path,
            threshold=args.threshold,
            overwrite=args.force,
        )
    else:
        raise ValueError(f"Given path {args.input_path!r} is not a directory or file!")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input_path")
    parser.add_argument("output_path", default=".")
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Threshold of invalid cells which constitute an invalid row.",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default=DEFAULT_PATTERN,
        help=(
            "Regular expression used to identify Excel application files. "
            "Used only when a directory is given in path"
        ),
    )
    parser.add_argument(
        "-f",
        "--force",
        default=DEFAULT_OVERWRITE,
        action="store_true",
        help=("Force overwriting of output files"),
    )

    parsed_args = parser.parse_args()
    if not 0 <= parsed_args.threshold <= 1:
        parser.error("--threshold must be between 0 and 1")
    return parsed_args


if __name__ == "__main__":
    main()
