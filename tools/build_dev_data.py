import math
import os

import django

django.setup()
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.gis.geos import Point, Polygon


User = get_user_model()

from cases.models import LetterTemplate, Boundaries, Location
from utils.coord_utils import parse_coord, point_to_string


def create_users():
    users = ["tchamber", "pwoody", "mholstin", "mwhitehe", "koneil"]

    for user in users:
        try:
            User.objects.create_user(
                username=user, password=user, is_staff=True, is_superuser=True
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
    north = parse_coord("37d 30m 0.4s N")
    east = parse_coord("78d 29m 59.0s W")
    south = parse_coord("39d 15m 0.4s N")

    assert west < east
    assert south < north
    points = (
        Point((west, south), srid=4269),
        Point((west, north), srid=4269),
        Point((east, north), srid=4269),
        Point((east, south), srid=4269),
        Point((west, south), srid=4269),
    )
    nrqz_polygon = Polygon(points)
    # TODO: Is this equivalent?
    # nrqz_polygon = Polygon.from_bbox((west, south, east, north))

    nrqz_boundaries = Boundaries.objects.create(name="NRQZ", bounds=nrqz_polygon)

    assert math.isclose(
        nrqz_boundaries.area.sq_mi, 13107.260_187_534_166, rel_tol=0.000_000_000_001
    )
    print(f"The NRQZ is {nrqz_boundaries.area.sq_mi:.2f} square miles")


def create_locations():
    # From Antenna FITS file
    gbt = Point((-79.839_833, 38.433_119), srid=4326)
    gbt_location = Location.objects.create(name="GBT", location=gbt)
    print(f"The GBT is located at: {point_to_string(gbt_location.location)}")


def main():
    create_users()
    create_templates()
    create_boundaries()
    create_locations()


if __name__ == "__main__":
    main()
