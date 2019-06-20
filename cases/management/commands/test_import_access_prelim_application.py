from django.test import TestCase

from cases.models import Case, PreliminaryCase, PreliminaryCaseGroup
from .import_access_prelim_application import (
    derive_cases_from_comments,
    handle_pcase_group,
    post_import_actions,
)


# class PreliminaryCaseGroupTestCase(TestCase):
#     def test_create(self):
#         pc1 = PreliminaryCase.objects.create(case_num=1, comments="NRQZ#P2 NRQZ#P3")
#         pc2 = PreliminaryCase.objects.create(case_num=2)
#         pc3 = PreliminaryCase.objects.create(case_num=3)

#         handle_pcase_group(pc1)
#         self.assertEqual(
#             list(pc1.pcase_group.prelim_cases.order_by("case_num")), [pc1, pc2, pc3]
#         )

#     def test_existing(self):
#         pc2 = PreliminaryCase.objects.create(case_num=2)
#         pcg = PreliminaryCaseGroup.objects.create()
#         pcg.prelim_cases.add(pc2)
#         self.assertEqual(list(pcg.prelim_cases.all()), [pc2])

#         pc1 = PreliminaryCase.objects.create(case_num=1, comments="NRQZ#P2 NRQZ#P3")
#         pc3 = PreliminaryCase.objects.create(case_num=3)

#         handle_pcase_group(pc1)
#         self.assertEqual(
#             list(pc1.pcase_group.prelim_cases.order_by("case_num")), [pc1, pc2, pc3]
#         )

#     def test_merge(self):
#         pc2 = PreliminaryCase.objects.create(case_num=2)
#         pcg1 = PreliminaryCaseGroup.objects.create()
#         pcg1.prelim_cases.add(pc2)
#         self.assertEqual(list(pcg1.prelim_cases.all()), [pc2])

#         pc3 = PreliminaryCase.objects.create(case_num=3)
#         pcg2 = PreliminaryCaseGroup.objects.create()
#         pcg2.prelim_cases.add(pc3)
#         self.assertEqual(list(pcg2.prelim_cases.all()), [pc3])

#         pc1 = PreliminaryCase.objects.create(case_num=1, comments="NRQZ#P2 NRQZ#P3")
#         self.assertEqual(pc1.pcase_group, None)

#         handle_pcase_group(pc1)
#         self.assertEqual(
#             list(pc1.pcase_group.prelim_cases.order_by("case_num")), [pc1, pc2, pc3]
#         )


class PreliminaryCaseGroupCaseTestCase(TestCase):
    def test_simple(self):
        c13 = Case.objects.create(case_num=13)
        c44 = Case.objects.create(case_num=44)
        pc1 = PreliminaryCase.objects.create(case_num=1, comments="NRQZ#13 NRQZ#44")
        derive_cases_from_comments(pc1)

        self.assertEqual(pc1.case, c13)

    def test_post_import_actions(self):
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
        post_import_actions()
        pc1.refresh_from_db()
        pc2.refresh_from_db()
        pc3.refresh_from_db()
        # The result should be, in this case, that there is a single PCG with
        # all 3 PCs in it
        self.assertTrue(pc1.pcase_group == pc2.pcase_group == pc3.pcase_group)
        self.assertEqual(
            list(pc1.pcase_group.prelim_cases.order_by("case_num")), [pc1, pc2, pc3]
        )
