import math
import os

import django

django.setup()
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.gis.geos import Point, Polygon

from utils.constants import NAD83_SRID, WGS84_SRID

User = get_user_model()

from cases.models import LetterTemplate, Boundaries, Location
from utils.coord_utils import parse_coord, point_to_string


def create_users():
    users = ["tchamber", "pwoody"]

    for user in users:
        try:
            User.objects.create_user(
                username=user, password=user, email=f"{user}@nrao.edu", is_staff=True, is_superuser=True
            )
        except django.db.utils.IntegrityError:
            print(f"{user} already exists!")
        else:
            print(f"{user} created")


def create_templates():
    for path in os.listdir(settings.NRQZ_LETTER_TEMPLATE_DIR):
        full_path = os.path.join(settings.NRQZ_LETTER_TEMPLATE_DIR, path)
        if os.path.isfile(full_path):
            lt, created = LetterTemplate.objects.get_or_create(
                name=os.path.basename(full_path), path=full_path
            )
            if created:
                print(f"Created {lt}")
            else:
                print(f"{lt} already exists!")


def create_boundaries():
    # From: https://science.nrao.edu/facilities/gbt/interference-protection/nrqz
    # The NRQZ is bounded by NAD-83 meridians of longitude at 78d 29m 59.0s W and
    # 80d 29m 59.2s W and latitudes of 37d 30m 0.4s N and 39d 15m 0.4s N,
    # and encloses a land area of approximately 13,000 square miles
    west = parse_coord("80d 29m 59.2s W")
    south = parse_coord("37d 30m 0.4s N")
    east = parse_coord("78d 29m 59.0s W")
    north = parse_coord("39d 15m 0.4s N")
    # Wholly west of PM
    assert west < east < 0
    # Wholly north of equator
    assert 0 < south < north
    points = (
        Point((west, south), srid=NAD83_SRID),
        Point((west, north), srid=NAD83_SRID),
        Point((east, north), srid=NAD83_SRID),
        Point((east, south), srid=NAD83_SRID),
        Point((west, south), srid=NAD83_SRID),
    )
    # Convert all to WGS84
    [point.transform(WGS84_SRID) for point in points]
    nrqz_polygon = Polygon(points)

    nrqz_boundaries = Boundaries.objects.create(name="NRQZ", bounds=nrqz_polygon)

    nrqz_area_str = f"{nrqz_boundaries.area.sq_mi:.2f} square miles"
    expected_nrqz_area = 13107.604_462_396_526
    if not math.isclose(
        nrqz_boundaries.area.sq_mi, expected_nrqz_area, rel_tol=0.001
    ):
        raise AssertionError(
            f"Expected NRQZ area ({nrqz_boundaries.area.sq_mi}) to be close to {expected_nrqz_area} square miles"
        )
    print(f"The NRQZ is {nrqz_area_str}")


def create_locations():
    # From Antenna FITS file, given in NAD83
    gbt = Point((-79.839_833, 38.433_119), srid=NAD83_SRID)
    # We store it in WGS84_SRID, though
    gbt.transform(WGS84_SRID)
    gbt_location = Location.objects.create(name="GBT", location=gbt)
    print(f"The GBT is located at: {point_to_string(gbt_location.location)}")


def sanity_checks():
    gbt = Location.objects.first().location
    nrqz = Boundaries.objects.first().bounds
    assert nrqz.covers(gbt)


def main():
    create_users()
    create_templates()
    create_boundaries()
    create_locations()
    sanity_checks()


if __name__ == "__main__":
    main()
