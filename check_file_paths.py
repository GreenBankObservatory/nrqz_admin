#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Check paths in given CSV file and determine whether they exist on the filesystem"""


import argparse
import csv
import os
from pprint import pprint, pformat
import urllib2
import httplib


def check_file_paths(csv_path):
    report = {"found": [], "not_found": []}
    with open(csv_path) as file:
        for line in file.readlines():
            path = line.strip()
            if os.path.isfile(path) or os.path.isdir(path):
                report["found"].append(path)
            elif path.startswith("http"):
                print(path)
                try:
                    # escaped = quote(str(path))
                    urllib2.urlopen(path)
                except (urllib2.HTTPError, urllib2.URLError, httplib.InvalidURL):
                    report["not_found"].append(path)
                else:
                    report["found"].append(path)
            else:
                report["not_found"].append(path)

    print("Summary:")
    for key, value in report.items():
        print("  {}: {}".format(key, len(value)))

    return report


def main():
    args = parse_args()
    report = check_file_paths(args.path)
    with open("./output.txt", "w") as file:
        file.write(pformat(report))

    if args.verbose:
        if args.keys:
            report = {key: value for key, value in report.items() if key in args.keys}
        pprint(report)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-k", "--keys", nargs="+", choices=["found", "not_found"])

    return parser.parse_args()


if __name__ == "__main__":
    main()
