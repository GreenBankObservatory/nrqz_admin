from django.test import TestCase

from cases.models import Case, CaseGroup
from .import_access_application import (
    # derive_cases_from_comments,
    handle_case_group,
    post_import_actions,
)


class FooTest(TestCase):
    def _common(self, case_1, case_2, case_3):
        self.assertEqual(CaseGroup.objects.count(), 0)

        post_import_actions()

        case_1.refresh_from_db()
        case_2.refresh_from_db()
        case_3.refresh_from_db()

        self.assertEqual(CaseGroup.objects.count(), 1)
        self.assertTrue(case_1.case_group == case_2.case_group == case_3.case_group)
        case_group = case_1.case_group
        self.assertEqual(
            list(case_group.cases.order_by("case_num")), [case_1, case_2, case_3]
        )

    def test_reference_type_1(self):
        # Case 1 directly references 2 and 3
        case_1 = Case.objects.create(case_num=1, comments="NRQZ#2 NRQZ#3")
        case_2 = Case.objects.create(case_num=2)
        case_3 = Case.objects.create(case_num=3)
        self._common(case_1, case_2, case_3)

    def test_reference_type_2(self):
        # Case 1 directly references 2
        case_1 = Case.objects.create(case_num=1, comments="NRQZ#2")
        # Case 2 directly references 3
        case_2 = Case.objects.create(case_num=2, comments="NRQZ#3")
        # Case 3 doesn't reference anything, but this shouldn't matter
        case_3 = Case.objects.create(case_num=3)
        self._common(case_1, case_2, case_3)

    def test_non_existent_case_num_reference(self):
        # Case 1 directly references 2
        case_1 = Case.objects.create(case_num=1, comments="NRQZ#2")
        # Case 2 directly references 3
        case_2 = Case.objects.create(case_num=2, comments="NRQZ#3")
        # Case 3 references Case 25, which doesn't exist (and will be ignored)
        case_3 = Case.objects.create(case_num=3, comments="NRQZ#25")
        self._common(case_1, case_2, case_3)

    def test_multiple_case_groups(self):
        case_1 = Case.objects.create(case_num=1, comments="NRQZ#2")
        case_2 = Case.objects.create(case_num=2)
        case_3 = Case.objects.create(case_num=3, comments="NRQZ#25")

        self.assertEqual(CaseGroup.objects.count(), 0)

        post_import_actions()

        case_1.refresh_from_db()
        case_2.refresh_from_db()
        case_3.refresh_from_db()

        self.assertEqual(CaseGroup.objects.count(), 2)
        self.assertTrue(case_1.case_group == case_2.case_group)
        self.assertEqual(
            list(case_1.case_group.cases.order_by("case_num")), [case_1, case_2]
        )
        self.assertEqual(list(case_3.case_group.cases.order_by("case_num")), [case_3])

    def test_no_references(self):
        Case.objects.create(case_num=1)
        Case.objects.create(case_num=2)
        Case.objects.create(case_num=3)

        self.assertEqual(CaseGroup.objects.count(), 0)

        post_import_actions()
        self.assertEqual(CaseGroup.objects.count(), 0)
