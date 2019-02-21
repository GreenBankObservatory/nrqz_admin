import json
from pprint import pprint

from tqdm import tqdm

from django.contrib.gis.geos import GEOSGeometry
from cases.models import Facility, Structure
from cases.forms import StructureForm
from tools.query_asr import query_asr_by_location

from utils.constants import FCC_ASR

m = {
    "DD_TEMP": "latitude",
    "DD_TEMP0": "longitude",
    "ISSUEDATE": "issue_date",
    "REGNUM": "asr",
    "STRUCHT": "height",
    "FILENUM": "file_num",
    "FAACIRC": "faa_circ_num",
    "FAASTUDY": "faa_study_num",
}


def create_point_from_feature(feature):
    latitude = feature["attributes"]["DD_TEMP"]
    longitude = feature["attributes"]["DD_TEMP0"]
    return GEOSGeometry(f"Point({longitude} {latitude})", srid=4326)


def find_closest_feature(facility, features):
    return max(
        features,
        key=lambda feature: facility.location.distance(
            create_point_from_feature(feature)
        ),
    )


def create_structure_from_feature(feature, facility):
    attributes = feature["attributes"]
    structure_dict = {m[key]: value for key, value in attributes.items() if key in m}
    latitude = structure_dict.pop("latitude")
    longitude = structure_dict.pop("longitude")
    structure_dict["location"] = GEOSGeometry(
        f"Point({longitude} {latitude})", srid=4326
    )

    structure_dict["data_source"] = FCC_ASR

    structure_dict["facility"] = facility.id
    try:
        structure = Structure.objects.get(asr=structure_dict["asr"])
    except Structure.DoesNotExist:
        structure_form = StructureForm(structure_dict)
        if structure_form.is_valid():
            structure = Structure.objects.create(**structure_form.cleaned_data)
            tqdm.write(f"Created Structure {structure}")
        else:
            pprint(structure_form.errors)
            return (None, structure_form.errors)
    else:
        tqdm.write(f"Found Structure {structure}")

    structure.facilities.add(facility)
    tqdm.write(f"Added {facility} to Structure {structure}")
    facility.asr_from_applicant = False
    facility.save()

    return (structure, None)


def query_asr_for_facilities(facilities):
    report = {
        "skipped": [],
        "found": {"errors": {}, "no_errors": {}},
        "multiple_found": {},
        "not_found": [],
    }
    height_errors = []
    for facility in tqdm(facilities, unit="facilities"):
        if facility.structure:
            report["skipped"].append(facility)
            continue
        result = query_asr_by_location(
            coords=facility.location.coords, units="meter", radius=10
        )
        features = result["features"]
        num_features = len(features)
        if num_features == 1:
            feature = features[0]
            structure, errors = create_structure_from_feature(feature, facility)
            if not errors:
                report["found"]["no_errors"][facility] = structure
            else:
                report["found"]["errors"][facility] = errors
        elif num_features > 1:
            tqdm.write("Multiple ASR records found!")
            report["multiple_found"][facility] = features
        else:
            tqdm.write("No ASR records found!")
            # If over 60 meters (~200 feet), something is probably wrong
            if facility.agl and facility.agl > 60:
                height_errors.append(facility)
            report["not_found"].append(facility)
        tqdm.write("-" * 80)
    return report


def run():
    facilities = Facility.objects.filter(location__isnull=False)
    # facilities = Facility.objects.filter(location__isnull=False, agl__gte=60)
    try:
        with open("no_asr.json") as fp:
            no_asr = json.load(fp)
    except FileNotFoundError:
        no_asr = []

    print(f"Excluding {len(no_asr)} Facilities from operation")
    facilities = facilities.exclude(id__in=no_asr)

    facilities = facilities

    report = query_asr_for_facilities(facilities)

    print("DONE")
    print("report:")
    pprint(report)
    print("-" * 80)
    print("summary:")
    print(f"Total: {len(facilities)}")
    print(f"Skipped (Structure already exists for Facility): {len(report['skipped'])}")
    print(f"Found: {len(report['found']['no_errors'])}")
    print(f"Found, but with validation errors: {len(report['found']['errors'])}")
    print(f"Multiple found: {len(report['multiple_found'])}")
    print(f"Not found: {len(report['not_found'])}")
    print("-" * 80)

    with open("no_asr.json", "w") as fp:
        new_not_found = [f.id for f in report["not_found"]]
        not_found = list(set(no_asr + new_not_found))
        json.dump(not_found, fp)

    for facility, features in report["multiple_found"].items():
        closest = find_closest_feature(facility, features)
        print("Found closest feature; attempting to create structure")
        structure, errors = create_structure_from_feature(closest, facility)
        print(f"  {structure} | {errors}")
    # for facility in height_errors:
    #     print(f"Facility {facility}: no ASR entry, but height >60m ({facility.agl}m)")
