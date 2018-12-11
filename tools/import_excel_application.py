#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Import Excel NRQZ application forms into the DB

Each Excel file creates a Batch. Each case number represents a Case.
Each data row in the Excel file creates a Facility.

Any files matching *.xls* or *.csv will be considered applications and
an attempt will be made to import them
"""

import argparse
import os
import re
import django

django.setup()

from django.db import transaction
from tqdm import tqdm

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException

from cases.models import Facility
from tools.fieldmap import coerce_long, coerce_lat


from tools.excel_importer import (
    ExcelCollectionImporter,
    DEFAULT_THRESHOLD,
    DEFAULT_PREPROCESS,
)


class ManualRollback(Exception):
    pass


def determine_files_to_process(paths, pattern=r".*\.(xls.?|csv)$"):
    files = []
    for path in paths:
        if os.path.isfile(path):
            files.append(path)
        elif os.path.isdir(path):
            files.extend(
                [
                    os.path.join(path, file)
                    for file in os.listdir(path)
                    if re.search(pattern, file)
                ]
            )
        else:
            raise ValueError(f"Given path {path!r} is not a directory or file!")

    return sorted(files)


def populate_locations(durable=False):
    for facility in tqdm(
        Facility.objects.filter(longitude__isnull=False, latitude__isnull=False),
        unit="facilities",
    ):
        try:
            longitude = coerce_long(facility.longitude)
            latitude = coerce_lat(facility.latitude)
        except ValueError as error:
            if not durable:
                raise
            print(
                f"Error parsing {facility} ({facility.latitude}, {facility.longitude}): {error}"
            )
        else:
            point_str = f"Point({longitude} {latitude})"

            try:
                facility.location = GEOSGeometry(point_str)
                facility.save()
            except GEOSException as error:
                print(f"Error saving {point_str}: {error}")


@transaction.atomic
def main():
    # sys.excepthook = excepthook
    args = parse_args()
    files_to_process = determine_files_to_process(args.paths, pattern=args.pattern)
    eci = ExcelCollectionImporter(
        paths=files_to_process,
        durable=args.durable,
        threshold=args.threshold,
        preprocess=not bool(args.no_preprocess),
    )

    eci.process()

    print("-" * 80)
    eci.report.process()
    # TODO: Include in report somehow
    populate_locations(durable=args.durable)

    if args.dry_run:
        raise ManualRollback("DRY RUN; ROLLING BACK CHANGES")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help=(
            "The paths to Excel applications to process "
            "(or .csv representation), or a directories thereof"
        ),
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help=(
            "Roll back all database changes after execution. Note that "
            "this will leave gaps in the PKs where created objects were rolled back"
        ),
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="If given, drop into an interactive shell upon unhandled exception",
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
        "-D",
        "--durable",
        default=False,
        action="store_true",
        help=(
            "If set, processing on a given batch will continue past all possible errors"
        ),
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Threshold of invalid headers which constitute an invalid sheet.",
    )
    parser.add_argument(
        "--no-preprocess",
        default=not DEFAULT_PREPROCESS,
        action="store_true",
        help="Indicate that no pre-processing needs to be done on the given input file(s)",
    )

    parsed_args = parser.parse_args()
    if not 0 <= parsed_args.threshold <= 1:
        parser.error("--threshold must be between 0 and 1")
    return parsed_args


if __name__ == "__main__":
    try:
        main()
    except ManualRollback as error:
        print(error)
