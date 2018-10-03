#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse
from glob import glob
import os

import pyexcel

def convert_excel_file_to_csv(excel_path, output="."):
    book = pyexcel.get_book(file_name=excel_path)

    try:
        sheet = book.sheet_by_name("From Applicant")
    except KeyError:
        print(
            "WARNING: Could not find sheet 'From Applicant'. Falling back to first sheet"
        )
        # TODO: More robust
        if len(book) != 1:
            print("ERROR: More than one sheet!")

    sheet = book.sheet_by_index(0)
    excel_file_name = os.path.basename(excel_path)
    file_name = f"{os.path.join(output, excel_file_name)}.{sheet.name}.csv".replace(" ", "_")
    sheet.save_as(file_name)
    print(f"Wrote {excel_file_name} to {file_name}")

def convert_excel_directory_to_csv(dir_path, output):
    for excel_path in sorted(glob(os.path.join(dir_path, "*.xls*"))):
        print(f"Processing {excel_path}")
        convert_excel_file_to_csv(excel_path, output)

def main():
    args = parse_args()
    if os.path.isdir(args.path):
        convert_excel_directory_to_csv(args.path, args.output)
    elif os.path.isfile(args.path):
        convert_excel_file_to_csv(args.path, args.output)
    else:
        raise ValueError("womp womp")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path")
    parser.add_argument("-o", "--output")
    return parser.parse_args()


if __name__ == '__main__':
    main()
