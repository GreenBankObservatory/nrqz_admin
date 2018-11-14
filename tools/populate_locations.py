from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException

from cases.models import Facility

def run():
    for facility in Facility.objects.filter(longitude__isnull=False, latitude__isnull=False):
        point_str = f"Point({facility.longitude} {facility.latitude})"
        try:
            facility.location = GEOSGeometry(point_str)
            facility.save()
        except GEOSException as error:
            print(f"Error saving {point_str}: {error}")
