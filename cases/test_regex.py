from .managers import (
    CASE_REGEX,
    PCASE_REGEX,
    NAM_CASE_REGEX,
    derive_nums_from_text,
    derive_related_case_nums_from_comments,
)

from django.test import TestCase


class RegexTest(TestCase):
    def _test_regex(self, regex, expectations):
        for string_to_parse, expected_case_nums in expectations:
            actual = derive_nums_from_text(string_to_parse, regex)
            self.assertEqual(actual, expected_case_nums)

    def test_nam_case_regex(self):
        """Test NAM_CASE_REGEX across representative data"""
        expectations = [
            ("ULS Case NRQZ ID 2222", {2222}),
            ("Prev Job Num: 333333CCCSSL02 - NRQZ ID 3333 L5 15MAR2013", {3333}),
            ("NRQZ#6996-2 Foo 111111CCCCAA00", {6996}),
            ("NRQZ#6954, NRAZ#6954-1", {6954}),
            ("NRQZ#6666-3/06DEC2000 and NRQZ#1111/16JUN1986", {1111, 6666}),
            ("Not available (Cellular NRQZ#3333)", {3333}),
            ("Foo 111111AAAAAA01 / NRQZ ID 4444", {4444}),
            ("8888", {8888}),
            ("8888 / p2222", {8888}),
            ("9999/07AUG2012, EWA# 88888888888888, ULS 0000000000", {9999}),
            ("7211, 7210, 4444", {4444, 7210, 7211}),
            ("5555/P4444", {5555}),
            ("None listed", set()),
        ]
        self._test_regex(NAM_CASE_REGEX, expectations)

    def test_pcase_regex(self):
        """Test PCASE_REGEX across representative data"""
        expectations = [
            ("Foo 111111AAAAAA01 / NRQZ ID 4444", set()),
            ("8888", set()),
            ("8888 / p2222", {2222}),
            ("9999/07AUG2012, EWA# 88888888888888, ULS 0000000000", set()),
            ("5555/P4444", {4444}),
            ("None listed", set()),
        ]
        self._test_regex(PCASE_REGEX, expectations)

    def test_derive_related_case_nums_from_comments(self):
        expectations = [
            (
                "Previous reviews under NRQZ ID 3333 and 4444\n"
                "This assignment was approved under NRQZ#5555/21MAY86 with record note S367.\n"
                "This assignment was approved under NRQZ#4444-11/18May2000 with record note S367.",
                {3333, 5555, 4444},
            ),
            ("11 April 2222: Discussed ... in 2000. There ... NRQZID 7777", {7777}),
            ("Previous reviews under NRQZ#1111 and NRQZ#4444-11", {1111, 4444}),
            ("Previous evaluation under NRQZ#1722/08AUG89", {1722}),
            (
                'This request is for evaluation of 0000GSM and 000/0000LTE at Foo\'s "VA11111D" site.',
                set(),
            ),
            (
                "Previous case analyses: NRQZ ID 4454, 4839, and 8038",
                {4454, 4839, 8038},
            ),
            (
                "Foo Bar\n\n"
                "Foo Bar Inc\n"
                "111 Foo Rd \n"
                "Foo, Bar\n"
                "Phone 777-333-9999\n"
                "Fax 777-333-9999\n"
                "4324324 --Return        06/20/2013\n",
                set(),
            ),
        ]
        for string_to_parse, expected_case_nums in expectations:
            actual = derive_related_case_nums_from_comments(string_to_parse)
            self.assertEqual(
                actual, expected_case_nums, f"Attempted to parse: {string_to_parse!r}"
            )
