#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse

import django

from pykml.factory import KML_ElementMaker as KML
from lxml import etree


def facility_as_kml(facility):
    return KML.Placemark(
        KML.name(facility.nrqz_id),
        KML.Point(KML.coordinates(f"{facility.longitude},{facility.latitude}")),
    )


def facilities_as_kml(facilities):
    return KML.Folder(*[facility_as_kml(facility) for facility in facilities])


def submission_as_kml(submission):
    return KML.Folder(
        KML.name(submission.name), *facilities_as_kml(submission.facilities.all())
    )


def submissions_as_kml(submissions):
    return KML.Folder(
        KML.name("submissions"),
        *[submission_as_kml(submission) for submission in submissions],
    )


def kml_to_string(kml):
    return etree.tostring(kml, pretty_print=True, encoding="unicode")


def write_kml(kml, output=None):
    if output is None:
        output = "./nrqz_applications.kml"
    with open(output, "w") as file:
        file.write(kml_to_string(kml))


def main():
    # args = parse_args()
    # kml = create_facility_placemarks(Facility.objects.all())
    facility_placemarks_by_submission = submissions_as_kml()
    write_kml(facility_placemarks_by_submission)


# def parse_args():
#     parser = argparse.ArgumentParser(
#         formatter_class=argparse.ArgumentDefaultsHelpFormatter
#     )
#     # parser.add_argument()
#     return parser.parse_args()


if __name__ == "__main__":
    django.setup()
    from submission.models import Submission, Facility

    main()
