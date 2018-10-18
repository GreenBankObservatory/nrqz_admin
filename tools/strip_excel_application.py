#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse
import os
import re

import pyexcel


def load_rows(path):
    book = pyexcel.get_book(file_name=path)
    book_dict = book.to_dict()

    try:
        sheet = book_dict["From Applicant"]
    except KeyError:
        print(
            "WARNING: Could not find sheet 'From Applicant'. Falling back to first sheet"
        )
        # TODO: More robust
        if len(book) != 1:
            print("ERROR: More than one sheet!")

        sheet = book.sheet_by_index(0).array

    return sheet


def strip_excel_directory(
    input_path, output_path, threshold=None, pattern=r".*\.(xls.?|csv)$"
):
    files = [
        os.path.join(input_path, f)
        for f in os.listdir(input_path)
        if re.search(pattern, f)
    ]
    for input_file_path in sorted(files):
        print(f"Processing {input_file_path}")
        strip_excel_file(input_file_path, output_path, threshold)


def indentify_invalid_rows(rows, threshold=None):
    if threshold is None:
        threshold = 0.7

    invalid_row_indices = []
    for ri, row in enumerate(rows):
        invalid_cells = 0
        for cell in row:
            if not str(cell):
                # print(f"Found invalid cell: {cell!r}")
                invalid_cells += 1

        if invalid_cells / len(row) > threshold:
            print(f"Found invalid row {ri} (>{threshold * 100}% cells invalid): {row}")
            invalid_row_indices.append(ri)

    return invalid_row_indices


def strip_excel_file(input_path, output_path, threshold=None, overwrite=False):
    """Save a new Excel file containing only headers and data rows"""
    output_filename = f"stripped_{os.path.basename(input_path)}"
    full_output_path = os.path.join(output_path, output_filename)
    if os.path.isfile(full_output_path) and not overwrite:
        print(f"{full_output_path} already exists; skipping")
        return False

    print("Opening workbook")
    rows = load_rows(input_path)
    print("...done")
    # Annotate each row with its original index (1-indexed). This
    # is so that we can reference them by this later
    rows = [row + [row_num] for row_num, row in enumerate(rows, 1)]

    orig_num_rows = len(rows)
    # Get the indexes of all invalid rows...
    invalid_row_indices = indentify_invalid_rows(rows, threshold)
    for index in sorted(invalid_row_indices, reverse=True):
        # print(f"Deleted invalid row {index}")
        # ...then delete them
        del rows[index]

    num_rows_deleted = orig_num_rows - len(rows)
    print(
        f"Deleted {num_rows_deleted}/{orig_num_rows} rows "
        f"({num_rows_deleted / orig_num_rows:.2f}%)"
    )
    # Change the header for our new column to something sensible
    rows[0][-1] = "Original Row"

    pyexcel.save_as(array=rows, dest_file_name=full_output_path)
    print(f"Wrote {full_output_path}")
    return True


def main():
    args = parse_args()
    if os.path.isdir(args.input_path):
        strip_excel_directory(
            args.input_path,
            args.output_path,
            threshold=args.threshold,
            pattern=args.pattern,
        )
    elif os.path.isfile(args.input_path):
        strip_excel_file(args.input_path, args.output_path, threshold=args.threshold)
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
        default=0.7,
        help="Threshold of invalid cells which constitute an invalid row.",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default=r".*\.(xls.?|csv)$",
        help=(
            "Regular expression used to identify Excel application files. "
            "Used only when a directory is given in path"
        ),
    )
    parser.add_argument(
        "-f",
        "--force",
        default=False,
        action="store_true",
        help=("Force overwriting of output files"),
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
