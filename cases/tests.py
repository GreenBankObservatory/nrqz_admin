from django.db.models.fields import NOT_PROVIDED
from django.test import TestCase

from .models import SensibleCharField


class SensibleCharFieldTestCase(TestCase):
    def test_disallow_null(self):
        with self.assertRaisesRegex(
            ValueError,
            "SensibleCharField doesn't allow null=True unless unique=True AND blank=True!",
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

    def test_null_allowed_if_blank_true_and_unique_true(self):
        # In this situation, null can be left out entirely...
        cf = SensibleCharField(blank=True, unique=True)
        self.assertEqual(cf.null, True)

        # ...or it can be given is True explicitly...
        cf = SensibleCharField(blank=True, unique=True, null=True)
        self.assertEqual(cf.null, True)

        # ...but it can't be set to False (we raise an error instead of silently ignoring this)
        with self.assertRaisesRegex(
            ValueError,
            "SensibleCharField doesn't allow null=False if unique=True AND blank=True!",
        ):
            SensibleCharField(blank=True, unique=True, null=False)

    def test_dont_set_default_to_none_if_null_is_allowed(self):
        cf = SensibleCharField(blank=True, unique=True, null=True)
        self.assertEqual(cf.default, NOT_PROVIDED)
