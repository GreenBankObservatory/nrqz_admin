from django.db.models.fields import NOT_PROVIDED
from django.test import TestCase

from .models import SensibleCharField


class SensibleCharFieldTestCase(TestCase):
    def test_disallow_null(self):
        with self.assertRaisesRegex(
            ValueError, "SensibleCharField doesn't allow null=True!"
        ):
            SensibleCharField(null=True)

    def test_default_to_none_if_blank_false(self):
        cf = SensibleCharField(blank=False)
        self.assertIsNone(cf.default)

    def test_default_to_none_if_blank_missing(self):
        cf = SensibleCharField()
        self.assertIsNone(cf.default)

    def test_no_default_if_blank_true(self):
        cf = SensibleCharField(blank=True)
        self.assertEqual(cf.default, NOT_PROVIDED)
