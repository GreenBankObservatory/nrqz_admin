#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import django

from pykml.factory import KML_ElementMaker as KML
from lxml import etree


def facility_as_kml(facility):
    """Generate a Placemark from a single facility"""
    return KML.Placemark(
        KML.name(facility.nrqz_id),
        KML.Point(KML.coordinates(f"{facility.location.x},{facility.location.y}")),
    )


def facilities_as_kml(facilities):
    """Generate a Folder of Placemarks from an iterable of facilities"""
    return KML.Folder(*[facility_as_kml(facility) for facility in facilities])


def case_as_kml(case):
    return KML.Folder(
        KML.name(case.case_num),
        *[facility_as_kml(facility) for facility in case.facilities.all()],
    )


def cases_as_kml(cases):
    return KML.Folder(KML.name("cases"), *[case_as_kml(case) for case in cases])


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
    facility_placemarks_by_case = cases_as_kml(Case.objects.all())
    write_kml(facility_placemarks_by_case)


# def parse_args():
#     parser = argparse.ArgumentParser(
#         formatter_class=argparse.ArgumentDefaultsHelpFormatter
#     )
#     # parser.add_argument()
#     return parser.parse_args()


if __name__ == "__main__":
    django.setup()
    from cases.models import Case, Facility

    main()
