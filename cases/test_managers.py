from django.test import TestCase

from cases.models import Case, CaseGroup, PreliminaryCase


class CaseManagerTest(TestCase):
    def _common(self, case_1, case_2, case_3):
        self.assertEqual(CaseGroup.objects.count(), 0)

        Case.objects.build_case_groups()

        case_1.refresh_from_db()
        case_2.refresh_from_db()
        case_3.refresh_from_db()

        self.assertEqual(CaseGroup.objects.count(), 1)
        self.assertTrue(
            list(case_1.case_groups.all())
            == list(case_2.case_groups.all())
            == list(case_3.case_groups.all())
        )
        case_group = case_1.case_groups.first()
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

        Case.objects.build_case_groups()

        case_1.refresh_from_db()
        case_2.refresh_from_db()
        case_3.refresh_from_db()

        # We should have 2 total Case Groups, 1 for Case 1/2 and 1 for Case 3
        self.assertEqual(CaseGroup.objects.count(), 2)
        # Case 1 and 2 should have the same Case Group
        self.assertEqual(list(case_1.case_groups.all()), list(case_2.case_groups.all()))
        # Case 1/2's Case Group should contain exactly Case 1 and 2
        self.assertEqual(
            list(case_1.case_groups.first().cases.order_by("case_num")),
            [case_1, case_2],
        )
        # Case 3's Case Group should contain exactly Case 3
        self.assertEqual(
            list(case_3.case_groups.first().cases.order_by("case_num")), [case_3]
        )

    def test_no_references(self):
        case_1 = Case.objects.create(case_num=1)
        case_2 = Case.objects.create(case_num=2)
        case_3 = Case.objects.create(case_num=3)

        self.assertEqual(CaseGroup.objects.count(), 0)

        Case.objects.build_case_groups()
        self.assertEqual(CaseGroup.objects.count(), 3)
        self.assertEqual(CaseGroup.objects.all()[0].cases.first(), case_1)
        self.assertEqual(CaseGroup.objects.all()[1].cases.first(), case_2)
        self.assertEqual(CaseGroup.objects.all()[2].cases.first(), case_3)

    def test_pm(self):
        c7 = Case.objects.create(case_num=7)
        # PC1 is related to C7 via its comments
        pc1 = PreliminaryCase.objects.create(case_num=1, comments="NRQZ#7")
        # PC2 and PC3 are related together via their comments, and should end up in
        # the same PCG
        pc2 = PreliminaryCase.objects.create(case_num=2, comments="NRQZ#P3")
        # Note that PC3 is related to C7 via its comments
        pc3 = PreliminaryCase.objects.create(case_num=3, comments="NRQZ#P2 NRQZ#7")

        # Now we loop through all of our PCs and perform "post import actions" on them
        # Basically this is calling handle_pcase_group and derive_cases_from_comments
        # on each PC.
        Case.objects.build_case_groups()
        pc1.refresh_from_db()
        pc2.refresh_from_db()
        pc3.refresh_from_db()
        # The result should be, in this case, that there is a single PCG with
        # all 3 PCs in it
        self.assertTrue(
            list(pc1.case_groups.all())
            == list(pc2.case_groups.all())
            == list(pc3.case_groups.all())
        )
        # self.assertEqual(
        #     list(pc1.pcase_group.prelim_cases.order_by("case_num")), [pc1, pc2, pc3]
        # )

    # def test_simple(self):
    #     c13 = Case.objects.create(case_num=13)
    #     c44 = Case.objects.create(case_num=44)
    #     pc1 = PreliminaryCase.objects.create(case_num=1, comments="NRQZ#13 NRQZ#44")
    #     Case.objects.build_case_groups()

    #     self.assertEqual(pc1.case, c13)

    def test_case_stuff(self):
        c7 = Case.objects.create(case_num=7, comments="NRQZ#P1")
        # PC1 is related to C7 via its comments
        pc1 = PreliminaryCase.objects.create(case_num=1)

        # Now we loop through all of our PCs and perform "post import actions" on them
        # Basically this is calling handle_pcase_group and derive_cases_from_comments
        # on each PC.
        Case.objects.build_case_groups()
        c7.refresh_from_db()
        pc1.refresh_from_db()
        # # The result should be, in this case, that there is a single PCG with
        # # all 3 PCs in it
        # self.assertTrue(pc1.pcase_group == pc2.pcase_group == pc3.pcase_group)
        # self.assertEqual(
        #     list(pc1.pcase_group.prelim_cases.order_by("case_num")), [pc1, pc2, pc3]
        # )
        self.assertEqual(list(c7.case_groups.all()), list(pc1.case_groups.all()))
