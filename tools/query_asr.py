#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from collections import OrderedDict
from pprint import pprint

import requests

DEFAULTS = {"SRID": 4326, "UNIT": "meter"}

UNIT_MAP = {
    "meter": "esriSRUnit_Meter",
    "mile": "esriSRUnit_StatuteMile",
    "foot": "esriSRUnit_Foot",
    "kilometer": "esriSRUnit_Kilometer",
}

UNIT_PLURAL_MAP = {
    "meter": "meters",
    "mile": "miles",
    "foot": "feet",
    "kilometer": "kilometers",
}


def query_asr(query):
    api_key = "Hp6G80Pky0om7QvQ"
    base_url = "https://services1.arcgis.com/{api_key}/arcgis/rest/services/Antenna_Structure_Registrate/FeatureServer/0/query?".format(
        api_key=api_key
    )
    url = "{base_url}{query}".format(base_url=base_url, query=urlencode(query))
    # print("Fetching {}".format(url))

    response = requests.get(url)
    response_json = response.json()

    if "error" in response_json:
        raise ValueError(
            "Error <{code}>: {message} ({details})".format(**response_json["error"])
        )

    # if not response_json["features"]:
    #     print("No results found!")

    return response_json


def query_asr_by_reg_num(regnum, output_coord_sys):
    query = OrderedDict(
        where="REGNUM like '%{}%'".format(regnum),
        outFields="*",
        outSR=output_coord_sys,
        f="json",
    )
    return query_asr(query)


def query_asr_by_location(
    coords,
    radius=10,
    input_coord_sys=DEFAULTS["SRID"],
    output_coord_sys=DEFAULTS["SRID"],
    units=DEFAULTS["UNIT"],
):
    geometry = "{},{}".format(*coords)
    units = UNIT_MAP[units]
    query = OrderedDict(
        where="1=1",
        outFields="*",
        geometry=geometry,
        geometryType="esriGeometryPoint",
        inSR=str(input_coord_sys),
        spatialRel="esriSpatialRelIntersects",
        distance=str(radius),
        units=units,
        outSR=str(output_coord_sys),
        f="json",
    )

    return query_asr(query)


def main():
    args = parse_args()

    if args.coords:
        print(
            "Searching ASR for all structures within {radius} {plural_unit} of "
            "{coords} [{input_coord_sys}]:".format(
                radius=args.radius,
                coords="({}, {})".format(*args.coords),
                input_coord_sys=args.input_coord_sys,
                plural_unit=UNIT_PLURAL_MAP[args.units],
            )
        )
        json = query_asr_by_location(
            # Note that we reverse these here!
            coords=(args.coords[1], args.coords[0]),
            radius=args.radius,
            input_coord_sys=args.input_coord_sys,
            output_coord_sys=args.output_coord_sys,
            units=args.units,
        )
    elif args.regnum:
        print(
            "Searching ASR database for Reg Number {regnum}:".format(regnum=args.regnum)
        )
        json = query_asr_by_reg_num(args.regnum, args.output_coord_sys)
    else:
        raise ValueError(":(")
    if args.json:
        pprint(json["features"])
    else:
        for feature in json["features"]:
            fstring = (
                "{ENTITY} ({DD_TEMP}, {DD_TEMP0}) [{STRUCHT}m]: "
                "{STRUCADD}, {STRUCCITY}, {STRUCSTATE}"
            )
            print(fstring.format(**feature["attributes"]))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--coords", help="Coordinates in decimal degrees", nargs=2
    )
    parser.add_argument(
        "-I",
        "--input-coord-sys",
        default=DEFAULTS["SRID"],
        help=(
            "ArcGIS ID of input coordinate system. Defaults to WGS84_SRID. See "
            "https://developers.arcgis.com/javascript/3/jshelp/gcs.html"
        ),
    )
    parser.add_argument(
        "-O",
        "--output-coord-sys",
        default=DEFAULTS["SRID"],
        help=(
            "ArcGIS ID of output coordinate system. Defaults to WGS84_SRID. See "
            "https://developers.arcgis.com/javascript/3/jshelp/gcs.html"
        ),
    )
    parser.add_argument(
        "-n",
        "--regnum",
        help=(
            "Query by Reg Number. Note that this will search for all "
            "Reg Numbers that contain the given string -- i.e. a substring search"
        ),
    )
    parser.add_argument(
        "-r", "--radius", help="Radius in given units (see --unit)", default=10
    )
    parser.add_argument(
        "-u",
        "--units",
        help="Units for --radius",
        choices=UNIT_MAP.keys(),
        default="kilometer",
    )
    parser.add_argument(
        "-j",
        "--json",
        help="Print out full JSON response from query",
        action="store_true",
    )
    args = parser.parse_args()

    if not args.coords or args.regnum:
        parser.error("One of --coords or --regnum is required")
    return args


if __name__ == "__main__":
    main()
