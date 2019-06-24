import re

from tqdm import tqdm

from django.apps import apps
from django.contrib.gis.db.models.functions import Area, Azimuth, AsKML, Distance
from django.db.models import (
    BooleanField,
    Case as CASE,
    F,
    Func,
    Q,
    QuerySet,
    Value,
    When,
    Manager,
)
from django.utils.functional import cached_property

# https://regex101.com/r/g6NM6e/1
CASE_REGEX = re.compile(
    r"(?:(?:NRQZ ID )|(?:NRQZ#)|(?:Case\s*))(?P<case_num>\d+)", re.IGNORECASE
)
PCASE_REGEX = re.compile(r"NRQZ#P(\d+)", re.IGNORECASE)


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
            in_nrqz=CASE(
                When(location__intersects=self.NRQZ, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def annotate_kml(self):
        return self.annotate(kml=AsKML("location"))


LocationManager = lambda: LocationQuerySet.as_manager()


class CaseManager(Manager):
    def _handle_existing(self, pcase_nums, case_nums):
        Case = apps.get_model("cases", "Case")
        CaseGroup = apps.get_model("cases", "CaseGroup")
        PreliminaryCase = apps.get_model("cases", "PreliminaryCase")

        CaseGroup = apps.get_model("cases", "CaseGroup")
        tqdm.write(f"case_nums: {case_nums}")
        related_cases = Case.objects.filter(Q(case_num__in=case_nums))

        related_pcases = PreliminaryCase.objects.filter(Q(case_num__in=pcase_nums))
        tqdm.write(f"related_cases: {related_cases}; related_pcases: {related_pcases}")
        if not (related_cases or related_pcases):
            return None, None
        # Now, grab the unique set of all existing, PCaseGroups that these related
        # PCases are already associated with
        existing_case_groups = CaseGroup.objects.filter(
            Q(cases__in=related_cases) | Q(pcases__in=related_pcases)
        )
        tqdm.write(f"existing_case_groups: {existing_case_groups}")
        # If there aren't any, then we'll need to create one
        if existing_case_groups.count() == 0:
            case_group = CaseGroup.objects.create()
            tqdm.write(f"Created {case_group}")
        # If there is exactly one already in existence, we can just use it
        elif existing_case_groups.count() == 1:
            case_group = existing_case_groups.first()
            tqdm.write(f"Found {case_group}")
        # If there is more than one, then we need to merge them together
        else:
            # Pick the first one as the one to keep (doesn't actually matter which one)
            case_group_to_keep = existing_case_groups.first()
            # We need to generate a list in memory from the QuerySet so that
            # this will be accurate after the deletions
            existing_case_groups_ids = list(
                existing_case_groups.values_list("id", flat=True)
            )
            # Update all of the related PCase's PCGs to the one we want to keep
            # Delete the others, since they serve no purpose now
            deletions = existing_case_groups.exclude(id=case_group_to_keep.id).delete()
            tqdm.write(
                f"Found multiple existing PCGs {existing_case_groups_ids}. "
                f"Set all PCGs to {case_group_to_keep}, kept "
                f"{case_group_to_keep.id}, and deleted the others: {deletions}"
            )
            case_group = case_group_to_keep

        return case_group, related_cases, related_pcases

    def _handle_case_group(self, case_nums, pcase_nums):
        Case = apps.get_model("cases", "Case")
        CaseGroup = apps.get_model("cases", "CaseGroup")
        PreliminaryCase = apps.get_model("cases", "PreliminaryCase")
        case_group = None

        case_group, related_cases, related_pcases = self._handle_existing(
            pcase_nums, case_nums
        )
        if case_group:
            if related_cases:
                case_group.cases.add(*related_cases)
            if related_pcases:
                case_group.pcases.add(*related_pcases)

        return case_group

    @staticmethod
    def _derive_related_case_nums(comments, regex):
        """Given a pcase, attempt to derive all related pcase numbers"""

        match = regex.findall(comments)
        if match:
            case_nums = [int(case_num) for case_num in match]
        else:
            case_nums = []

        return case_nums

    def build_case_groups(self):
        Case = apps.get_model("cases", "Case")
        PreliminaryCase = apps.get_model("cases", "PreliminaryCase")

        for comments, case_num in tqdm(
            self.values_list("comments", "case_num"), unit="Case"
        ):
            related_case_nums = self._derive_related_case_nums(comments, CASE_REGEX)
            tqdm.write(f"related_case_nums: {related_case_nums}")
            related_pcase_nums = self._derive_related_case_nums(comments, PCASE_REGEX)
            tqdm.write(f"related_pcase_nums: {related_pcase_nums}")
            if self.model == Case:
                related_case_nums.append(case_num)
            elif self.model == PreliminaryCase:
                related_pcase_nums.append(case_num)
            else:
                raise ValueError("Only works on Case/PreliminaryCase....")
            case_group = self._handle_case_group(related_case_nums, related_pcase_nums)
