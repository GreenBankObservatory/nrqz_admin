from django.apps import apps
from django.contrib.gis.db.models.functions import Area, Azimuth, AsKML, Distance
from django.db.models import BooleanField, Case, F, Func, QuerySet, Value, When
from django.utils.functional import cached_property


class LocationQuerySet(QuerySet):
    @cached_property
    def GBT(self):
        return apps.get_model("cases", "Location").objects.get(name="GBT").location

    @cached_property
    def NRQZ(self):
        return apps.get_model("cases", "Boundaries").objects.get(name="NRQZ").bounds

    def annotate_distance_to_gbt(self):
        return self.annotate(distance_to_gbt=Distance(F("location"), self.GBT))

    def annotate_azimuth_to_gbt(self):
        """Add an "azimuth_to_gbt" annotation that indicates the azimuth bearing to the GBT (in degrees)"""
        return self.annotate(
            azimuth_radians_to_gbt=Azimuth(F("location"), self.GBT),
            azimuth_to_gbt=Func(F("azimuth_radians_to_gbt"), function="DEGREES"),
        )

    def annotate_in_nrqz(self):
        """Add an "in_nrqz" annotation that indicates whether each Facility is inside or outside the NRQZ"""
        return self.annotate(
            in_nrqz=Case(
                When(location__intersects=self.NRQZ, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def annotate_kml(self):
        return self.annotate(kml=AsKML("location"))


LocationManager = lambda: LocationQuerySet.as_manager()
