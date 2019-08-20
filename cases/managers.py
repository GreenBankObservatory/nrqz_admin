import os
import re

from tqdm import tqdm

from django.apps import apps
from django.contrib.gis.db.models.functions import AsKML, Azimuth, Distance
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
    Count,
    Max,
)
from django.utils.functional import cached_property

from django_import_data.querysets import TrackedFileQueryset

from importers.converters import coerce_none

# https://regex101.com/r/g6NM6e/5
CASE_REGEX = re.compile(r"(?<=(?:NRQZ|CASE))\D*(\d{3,7}.*)", re.IGNORECASE)
# https://regex101.com/r/2RRmH7/3
PCASE_REGEX = re.compile(r"P(\d{3,7})", re.IGNORECASE)

# Match groups of 3-7 digits that are not preceded or followed by a letter. Also,
# ignore groups of digits greater than 7 digits in a row. This is intended for use
# on fields that we KNOW should have case numbers in them (as opposed to
# comments, which can have any kind of number). However, they might also have
# PCase numbers, ULS #s, etc. which complicates things
# https://regex101.com/r/LnzShM/2/
NAM_CASE_REGEX = re.compile(r"[a-z]\d+|\d+[a-z]|\d{7,}|(\d{3,7})", re.IGNORECASE)


def derive_nums_from_text(comments, regex):
    """Given a string, derive all related case nums using given regexes"""
    return set(int(num) for num in regex.findall(comments) if num)


def derive_related_case_nums_from_comments(comments):
    """Given a string, derive all related case nums using given regexes"""
    case_nums = set()

    # Get our case nums
    case_nums_groups = CASE_REGEX.findall(comments)
    if case_nums_groups:
        # For every capture group...
        for case_nums_group in case_nums_groups:
            case_nums_from_group = derive_nums_from_text(
                case_nums_group, NAM_CASE_REGEX
            )
            case_nums.update(
                case_num
                for case_num in case_nums_from_group
                # Exclude case nums that could be a date instead... just in case
                if case_num > 2999 or case_num < 2000
            )

        tqdm.write(
            f"-\nParsed {case_nums} with {CASE_REGEX} from\n---\n{comments}\n---"
        )

    return case_nums


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
    def audit_case_groups(self):
        """Return Cases not in a Case Group, but with comments containing numbers"""
        return self.annotate(
            num_related_pcases=Count("case_groups__pcases", distinct=True),
            num_related_cases=Count("case_groups__cases", distinct=True),
            num_related=F("num_related_pcases") + F("num_related_cases"),
        ).filter(comments__regex=r"\d", num_related=0)

    def annotate_stuff(self, queryset=None):
        if queryset is None:
            queryset = self.all()
        queryset = queryset.annotate(
            num_facilities=Count("facilities"),
            sgrs_pending=Count("id", filter=Q(facilities__sgrs_approval=None)),
            sgrs_approvals=Count("id", filter=Q(facilities__sgrs_approval=True)),
        )
        queryset = queryset.annotate(
            sgrs_approval=CASE(
                When(sgrs_pending__gt=0, then=Value(None)),
                When(sgrs_approvals=F("num_facilities"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        queryset = queryset.annotate(
            num_facilities=Count("facilities"),
            erpd_limit_pending=Count("id", filter=Q(facilities__meets_erpd_limit=None)),
            erpd_limit_pass=Count("id", filter=Q(facilities__meets_erpd_limit=True)),
        )
        queryset = queryset.annotate(
            meets_erpd_limit=CASE(
                When(erpd_limit_pending__gt=0, then=Value(None)),
                When(erpd_limit_pass=F("num_facilities"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        queryset = queryset.annotate(num_facilities=Count("facilities"))
        queryset = queryset.annotate(si_done=Max("facilities__si_done"))
        return queryset


class CaseGroupManager(Manager):
    def _build_case_group(self, case_nums, pcase_nums):
        """Create or a CaseGroup from given case_nums and pcase_nums

        If multiple CaseGroups are found for the given case_nums and pcase_nums,
        merge them together
        """

        Case = apps.get_model("cases", "Case")
        CaseGroup = apps.get_model("cases", "CaseGroup")
        PreliminaryCase = apps.get_model("cases", "PreliminaryCase")

        tqdm.write(f"case_nums: {case_nums}")
        related_cases = Case.objects.filter(case_num__in=case_nums)
        # related_cases |= Case.objects.filter(case_groups__cases__case_num__in=case_nums)

        related_pcases = PreliminaryCase.objects.filter(case_num__in=pcase_nums)
        # related_pcases = PreliminaryCase.objects.filter(
        # case_groups__pcases__case_num__in=pcase_nums
        # )
        tqdm.write(f"related_cases: {related_cases}; related_pcases: {related_pcases}")
        if not (related_cases.exists() or related_pcases.exists()):
            return None
        # Now, grab the unique set of all existing, PCaseGroups that these related
        # PCases are already associated with
        existing_case_groups = CaseGroup.objects.filter(
            Q(cases__in=related_cases) | Q(pcases__in=related_pcases)
        ).distinct()
        tqdm.write(f"existing_case_groups: {existing_case_groups}")
        # If there aren't any, then we'll need to create one
        if existing_case_groups.count() == 0:
            case_group = CaseGroup.objects.create()
            tqdm.write(f"Created {case_group}")
            if related_cases.exists():
                case_group.cases.add(*related_cases)
            if related_pcases.exists():
                case_group.pcases.add(*related_pcases)
        # If there is exactly one already in existence, we can just use it
        elif existing_case_groups.count() == 1:
            case_group = existing_case_groups.first()
            tqdm.write(f"Found {case_group}")
            if related_cases.exists():
                case_group.cases.add(*related_cases)
            if related_pcases.exists():
                case_group.pcases.add(*related_pcases)
        # TODO: An alternative strategy, where we _don't_ merge the existing_case_groups?
        # else:
        #     tqdm.write(f"Found multiple existing PCGs; " "adding to all of them ")
        #     for case_group in existing_case_groups.all():
        #         if related_cases.exists():
        #             tqdm.write(f"  Added {related_cases} to {case_group}")
        #             case_group.cases.add(*related_cases)
        #         if related_pcases.exists():
        #             case_group.pcases.add(*related_pcases)
        #             tqdm.write(f"  Added {related_pcases} to {case_group}")
        # If there is more than one, then we need to merge them together
        else:
            # Pick the first one as the one to keep (doesn't actually matter which one)
            case_group_to_keep = existing_case_groups.first()
            # We need to generate a list in memory from the QuerySet so that
            # this will be accurate after the deletions
            existing_case_groups_ids = list(
                existing_case_groups.values_list("id", flat=True)
            )
            case_groups_to_delete = existing_case_groups.exclude(
                id=case_group_to_keep.id
            )
            assert case_groups_to_delete.count() > 0, case_groups_to_delete.count()
            other_cases = case_groups_to_delete.values_list("cases", flat=True).filter(
                cases__isnull=False
            )
            other_pcases = case_groups_to_delete.values_list(
                "pcases", flat=True
            ).filter(pcases__isnull=False)
            if other_cases.exists():
                case_group_to_keep.cases.add(*other_cases, *related_cases)
            if other_pcases.exists():
                case_group_to_keep.pcases.add(*other_pcases, *related_pcases)
            for case_group_to_delete in case_groups_to_delete:
                case_group_to_delete.cases.set(Case.objects.none())
                case_group_to_delete.pcases.set(PreliminaryCase.objects.none())
            # Update all of the related PCase's PCGs to the one we want to keep
            # Delete the others, since they serve no purpose now
            # NOTE: We can't simply delete case_groups_to_delete here, because it
            # should now be empty (because by nulling out its cases and pcases
            # we have effectively filtered everything out of it)
            deletions = (
                CaseGroup.objects.filter(id__in=existing_case_groups_ids)
                .exclude(id=case_group_to_keep.id)
                .delete()
            )
            assert deletions[0] > 0, deletions
            tqdm.write(
                f"Found multiple existing PCGs {existing_case_groups_ids}. "
                f"Set all PCGs to {case_group_to_keep}, kept "
                f"{case_group_to_keep}; deletions: {deletions}"
            )
            case_group = case_group_to_keep

        return case_group, related_cases, related_pcases

    def _build_case_groups(self, comments, case_num, model_class):
        Case = apps.get_model("cases", "Case")
        PreliminaryCase = apps.get_model("cases", "PreliminaryCase")

        related_case_nums = derive_related_case_nums_from_comments(comments)
        tqdm.write(f"related_case_nums: {related_case_nums}")
        related_pcase_nums = derive_nums_from_text(comments, PCASE_REGEX)
        tqdm.write(f"related_pcase_nums: {related_pcase_nums}")
        tqdm.write("=" * 80)
        if model_class == Case:
            related_case_nums.add(case_num)
        elif model_class == PreliminaryCase:
            related_pcase_nums.add(case_num)
        else:
            raise ValueError(
                f"Only works on Case/PreliminaryCase....; got {model_class}"
            )
        self._build_case_group(related_case_nums, related_pcase_nums)

    def _build_case_groups_from_cases(self):
        Case = apps.get_model("cases", "Case")
        for comments, case_num in tqdm(
            Case.objects.values_list("comments", "case_num"), unit="Case"
        ):
            self._build_case_groups(comments, case_num, Case)

    def _build_case_groups_from_pcases(self):
        PreliminaryCase = apps.get_model("cases", "PreliminaryCase")

        for comments, case_num in tqdm(
            PreliminaryCase.objects.values_list("comments", "case_num"), unit="PCase"
        ):
            self._build_case_groups(comments, case_num, PreliminaryCase)

    def _build_case_groups_from_row_data(self):
        RowData = apps.get_model("django_import_data", "RowData")
        row_data_with_possible_links = RowData.objects.filter(
            data__main_dict__has_any_keys=["nrqz_links", "PrevCases"]
        )
        for prev_cases, nrqz_links in tqdm(
            row_data_with_possible_links.values_list(
                "data__main_dict__PrevCases", "data__main_dict__nrqzLinks"
            ),
            unit="RowData",
        ):
            prev_cases = coerce_none(prev_cases)
            nrqz_links = coerce_none(nrqz_links)
            tqdm.write(f"prev_cases: {prev_cases!r}, nrqz_links: {nrqz_links!r}")
            related_case_nums = set()
            related_pcase_nums = set()
            if prev_cases:
                related_case_nums.update(
                    derive_nums_from_text(prev_cases, NAM_CASE_REGEX)
                )
                related_pcase_nums.update(
                    derive_nums_from_text(prev_cases, PCASE_REGEX)
                )

            if nrqz_links:
                related_case_nums.update(
                    derive_nums_from_text(nrqz_links, NAM_CASE_REGEX)
                )
                related_pcase_nums.update(
                    derive_nums_from_text(nrqz_links, PCASE_REGEX)
                )

            tqdm.write(
                f"related_case_nums: {related_case_nums}, related_pcase_nums: {related_pcase_nums}"
            )
            self._build_case_group(related_case_nums, related_pcase_nums)

    def build_all_case_groups(self, max_attempts=5):
        num_case_groups = self.count()
        prev_num_case_groups = None
        num_attempts = 0
        while num_case_groups != prev_num_case_groups and num_attempts < max_attempts:
            for grouper in tqdm(
                [
                    self._build_case_groups_from_cases,
                    self._build_case_groups_from_pcases,
                    self._build_case_groups_from_row_data,
                ],
                unit="grouper",
            ):
                grouper()

            prev_num_case_groups = num_case_groups
            num_case_groups = self.count()
            num_attempts += 1

        print(f"Number of CaseGroups stabilized at {num_case_groups}")


class AttachmentManager(Manager):
    # def derive_is_active(self):
    #     attachments = self.all()
    #     for attachment in tqdm(attachments):
    #         attachment.is_active = os.path.isfile(attachment.path)

    #     return self.bulk_update(attachments, ["is_active"])

    def get_queryset(self):
        return TrackedFileQueryset(self.model, using=self._db)

    def get_by_natural_key(self, path):
        return self.get(path=path)


class PersonManager(Manager):
    def get_by_natural_key(self, name, email):
        print("THIS IS A HACK; IF YOU ARE SEEING THIS IT IS BAD")
        return self.filter(name=name, email=email).first()
