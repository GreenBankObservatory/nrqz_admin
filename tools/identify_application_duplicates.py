#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse
import os
from pprint import pprint
import re

application_name_regex_str = (
    r"^(?P<start>\d+)[\s\-_]+(?:(?:\w+[\s\-_]+)?(?P<end>\d+)[\s\-_]+)?"
)

application_name_regex = re.compile(application_name_regex_str)


def get_filenames_by_case_number(path):
    filenames_by_case_number = {}
    overlaps = {}
    for filename in os.listdir(path):
        match = application_name_regex.match(filename)
        if match:
            # print(filename)
            start, end = match.groups()
            start = int(start)
            if end:
                end = int(end)
                # print(f"  Found case numbers {start} - {end}")
                case_numbers = range(start, end)
            else:
                # print(f"  Found case number {start}")
                case_numbers = [start]

            for case_number in case_numbers:
                if case_number in filenames_by_case_number:
                    prev_filename = filenames_by_case_number[case_number]
                    # print(
                    #     f"{filename} overlaps previously-found case number {case_number} (from {prev_filename})"
                    # )
                    filenames_by_case_number[case_number].add(filename)
                else:
                    filenames_by_case_number[case_number] = set([filename])
        else:
            print(
                f"Failed to parse {filename!r} with regex {application_name_regex_str!r}"
            )
    return filenames_by_case_number


def identify_overlaps(filenames_by_case_number):
    return {
        case_number: filenames
        for case_number, filenames in filenames_by_case_number.items()
        if len(filenames) > 1
    }


def case_numbers_by_filenames(filenames_by_case_number):
    by_fn = {}
    for case_number, filenames in filenames_by_case_number.items():
        filenames_as_tuple = tuple(filenames)
        if filenames_as_tuple in by_fn:
            by_fn[filenames_as_tuple].append(case_number)
        else:
            by_fn[filenames_as_tuple] = [case_number]
    return by_fn


def is_contiguous(list_):
    last_element = None
    for element in list_:
        if last_element and element != last_element + 1:
            return False
        last_element = element

    return True


def clean_case_numbers(filename_overlaps_by_case_number):
    cleaned = {}
    for key, value in filename_overlaps_by_case_number.items():
        value = sorted(value)
        if is_contiguous(value):
            cleaned[key] = (value[0], value[-1])
    return cleaned


def main():
    args = parse_args()
    filenames_by_case_number = get_filenames_by_case_number(args.path)
    filename_overlaps_by_case_number = identify_overlaps(filenames_by_case_number)
    pprint(filename_overlaps_by_case_number)
    print("-" * 80)
    case_number_overlaps_by_filenames = case_numbers_by_filenames(
        filename_overlaps_by_case_number
    )
    cleaned = clean_case_numbers(case_number_overlaps_by_filenames)
    for filenames, case_number_range in cleaned.items():
        case_number_start, case_number_end = case_number_range
        print(
            f"Files {filenames!r} overlap on the following case numbers: {case_number_start} - {case_number_end}"
        )
    # pprint(cleaned)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path")
    return parser.parse_args()


if __name__ == "__main__":
    main()
