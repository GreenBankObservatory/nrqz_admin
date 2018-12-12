"""Strip formatting, formulas, etc. from Excel file(s)

This is done by simply opening the file in pyexcel and re-saving it. This has
the effect of stripping all formatting, formulas, etc., and leaving only raw data.

This is typically useful if your original Excel files are huge due to
formatting quirks
"""

import argparse
import os
import re

import pyexcel
from tqdm import tqdm

DEFAULT_PATTERN = r".*\.xls.?$"


def strip_excel_directory(input_path, output_path, pattern=DEFAULT_PATTERN):
    files = [
        os.path.join(input_path, file)
        for file in os.listdir(input_path)
        if re.search(pattern, file)
    ]
    for input_file_path in tqdm(sorted(files), unit="files"):
        strip_excel_file(input_file_path, output_path)


def strip_excel_file(input_path, output_path, overwrite=False):
    tqdm.write(f"Processing {input_path}")

    output_filename = f"data_only_{os.path.basename(input_path)}".replace(" ", "_")
    full_output_path = os.path.join(output_path, output_filename)
    if os.path.isfile(full_output_path) and not overwrite:
        tqdm.write(f"{full_output_path} already exists; skipping")
        return False

    book = pyexcel.get_book(file_name=input_path)
    book.save_as(full_output_path)
    tqdm.write(f"Wrote {full_output_path}")
    return True


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input_path")
    parser.add_argument("output_path", default=".")
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
        default=False,
        action="store_true",
        help=("Force overwriting of output files"),
    )

    return parser.parse_args()


def main():
    args = parse_args()
    if os.path.isdir(args.input_path):
        strip_excel_directory(args.input_path, args.output_path, pattern=args.pattern)
    elif os.path.isfile(args.input_path):
        strip_excel_file(args.input_path, args.output_path)
    else:
        raise ValueError(f"Given path {args.input_path!r} is not a directory or file!")


if __name__ == "__main__":
    main()
