from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException

from cases.models import Facility
from tools.fieldmap import cooerce_long, cooerce_lat


def run():
    for facility in Facility.objects.filter(
        longitude__isnull=False, latitude__isnull=False
    ):
        try:
            longitude = cooerce_long(facility.longitude)
            latitude = cooerce_lat(facility.latitude)
        except ValueError:
            print(f"Error parsing {facility}")
        else:
            point_str = f"Point({longitude} {latitude})"

            try:
                facility.location = GEOSGeometry(point_str)
                facility.save()
            except GEOSException as error:
                print(f"Error saving {point_str}: {error}")
