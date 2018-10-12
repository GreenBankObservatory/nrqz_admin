#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse
import csv
from pprint import pprint

import django

django.setup()
from django.db import transaction

from applicants.models import Applicant
from tools.accessfieldmap import applicant_field_map
from tools.import_excel_application import derive_field_from_validation_error


class ManualRollback(Exception):
    pass


def load_rows(path):
    with open(path, newline="", encoding="latin1") as file:
        return list(csv.reader(file))


@transaction.atomic
def create_applicant_from_row(field_importers, row):
    row_dict = {}
    for importer, value in zip(field_importers, row):
        if importer:
            row_dict[importer.to_field] = importer.converter(value)

    # pprint(row_dict)
    return Applicant(**row_dict)


@transaction.atomic
def main():
    args = parse_args()
    rows = load_rows(args.path)
    headers = rows[0]
    data = rows[1:]

    field_importers = []
    for header in headers:
        try:
            field_importers.append(applicant_field_map[header])
        except KeyError:
            field_importers.append(None)

    applicants = [create_applicant_from_row(field_importers, row) for row in data]

    try:
        Applicant.objects.bulk_create(applicants)
    except (django.core.exceptions.ValidationError, ValueError, TypeError) as error:
        field = derive_field_from_validation_error(error.__traceback__)
        raise ValueError(f"Field: {field}") from error



    # raise ManualRollback()


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path")
    return parser.parse_args()


if __name__ == "__main__":
    main()
