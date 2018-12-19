from pprint import pprint

from django.test import TestCase

from importers.fieldmap import FormMap, FieldMap, FieldMapError
from django.forms import CharField, Form


class FooForm(Form):
    title = CharField()
    first_name = CharField()
    middle_name = CharField()
    last_name = CharField()
    sector_a = CharField()
    sector_b = CharField()
    sector_c = CharField()
    bar = CharField()
    flarm = CharField()
    location = CharField()


def handle_sectors(sectors):
    a, b, c = sectors.split(" ")
    return {"sector_a": a, "sector_b": b, "sector_c": c}


def handle_dms(latitude, longitude):
    lat_d, lat_m, lat_s = latitude.split(" ")
    long_d, long_m, long_s = longitude.split(" ")
    return {
        "lat_d": lat_d,
        "lat_m": lat_m,
        "lat_s": lat_s,
        "long_d": long_d,
        "long_m": long_m,
        "long_s": long_s,
    }


def handle_location(latitude, longitude):
    return (latitude, longitude)


def handle_person(gender, name):
    title = "Mr." if gender == "male" else "Mrs."
    first_name, middle_name, last_name = name.split(" ")
    return {
        "title": title,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
    }


def make_uppercase(value):
    return value.upper()


class FormMapTestCase(TestCase):
    def setUp(self):
        self.form_map = FormMap(
            field_maps=[
                # n:n
                FieldMap(
                    from_fields={"gender": ("gen",), "name": ("name", "n")},
                    converter=handle_person,
                    to_fields=("title", "first_name", "middle_name", "last_name"),
                ),
                # 1:n
                FieldMap(
                    from_field="sectors",
                    converter=handle_sectors,
                    to_fields=("sector_a", "sector_b", "sector_c"),
                ),
                # n:1
                FieldMap(
                    from_fields={
                        "latitude": ("LAT", "lat"),
                        "longitude": ("LONG", "long"),
                    },
                    converter=handle_location,
                    to_field="location",
                ),
                # 1:1, no converter
                FieldMap(from_field="foo", to_field="bar"),
                # 1:1, with converter
                FieldMap(from_field="flim", to_field="flarm", converter=make_uppercase),
            ],
            form_class=FooForm,
        )

    def test_complex(self):
        data = {
            "gender": "male",
            "name": "foo bar baz",
            "sectors": "a1 b2 c3",
            "foo": "blarg",
            "lat": "33",
            "long": "34",
            "unmapped": "doesn't matter",
            "flim": "abcd",
        }
        # with self.assertRaises(ValueError):
        #     # This should fail because we have an un-mapped header
        #     form_map.render_dict(data, allow_unprocessed=False)
        actual = self.form_map.render_dict(data)
        expected = {
            "title": "Mr.",
            "first_name": "foo",
            "middle_name": "bar",
            "last_name": "baz",
            "sector_a": "a1",
            "sector_b": "b2",
            "sector_c": "c3",
            "bar": "blarg",
            "flarm": "ABCD",
            "location": ("33", "34"),
        }
        self.assertEqual(actual, expected)

    def test_complex_with_missing_data(self):
        data = {
            "gender": "male",
            "name": "foo bar baz",
            "foo": "blarg",
            "lat": "33",
            "long": "34",
            "unmapped": "doesn't matter",
        }
        with self.assertRaises(ValueError):
            # This should fail because we have an un-mapped header
            self.form_map.render_dict(data, allow_unprocessed=False)
        actual = self.form_map.render_dict(data)
        expected = {
            "title": "Mr.",
            "first_name": "foo",
            "middle_name": "bar",
            "last_name": "baz",
            "bar": "blarg",
            "location": ("33", "34"),
        }
        self.assertEqual(actual, expected)

    def test_get_known_from_fields(self):
        actual = self.form_map.get_known_from_fields()
        expected = {
            "gender",
            "name",
            "sectors",
            "latitude",
            "longitude",
            "LAT",
            "lat",
            "LONG",
            "long",
            "foo",
            "flim",
            "n",
            "gen",
        }
        self.assertEqual(actual, expected)

    def test_unalias(self):
        headers = {"gender", "name", "foo", "lat", "long", "unmapped"}
        actual = self.form_map.unalias(headers)
        expected = {
            "gender": "gender",
            "name": "name",
            "latitude": "lat",
            "longitude": "long",
            "foo": "foo",
        }
        self.assertEqual(actual, expected)


class FieldMapTestCase(TestCase):
    def test_map_type(self):
        fm = FieldMap(from_field="foo", to_field="bar")
        self.assertEqual(fm.map_type, FieldMap.ONE_TO_ONE)

        fm = FieldMap(from_fields=["foo"], to_fields=["bar"])
        self.assertEqual(fm.map_type, FieldMap.ONE_TO_ONE)

        fm = FieldMap(
            from_field="foo", converter=lambda foo: foo, to_fields=["bar", "baz"]
        )
        self.assertEqual(fm.map_type, FieldMap.ONE_TO_MANY)

        fm = FieldMap(
            from_fields=["foo", "baz"], converter=lambda foo, baz: foo, to_field="bar"
        )
        self.assertEqual(fm.map_type, FieldMap.MANY_TO_ONE)

        fm = FieldMap(
            from_fields=["foo", "baz"],
            converter=lambda foo, baz: foo,
            to_fields=["bar", "faz"],
        )
        self.assertEqual(fm.map_type, FieldMap.MANY_TO_MANY)

    def test_from_field_to_field(self):
        fm = FieldMap(from_field="case_num", to_field="case_num")

    def test_from_fields_to_field_default_converter(self):
        with self.assertRaises(ValueError):
            FieldMap(from_fields=("latitude", "longitude"), to_field="location")

    def test_from_field_to_fields_default_converter(self):
        with self.assertRaises(ValueError):
            FieldMap(from_fields="nrqz_id", to_fields=("case_num", "site_name"))

    def test_from_fields_to_fields_default_converter(self):
        with self.assertRaises(ValueError):
            FieldMap(
                from_fields=("latitude", "longitude"),
                to_fields=("lat_m", "lat_s", "long_d", "long_m", "long_s"),
            )

    def test_from_fields_to_field_with_converter(self):
        field_map = FieldMap(
            from_fields=("latitude", "longitude"),
            converter=lambda latitude, longitude: dict(location=(latitude, longitude)),
            to_field="location",
        )
        actual = field_map.map(latitude="11 22 33", longitude="44 55 66")
        expected = dict(location=("11 22 33", "44 55 66"))
        self.assertEqual(actual, expected)

    def test_from_field_to_fields_with_converter(self):
        field_map = FieldMap(
            from_field="nrqz_id",
            converter=lambda nrqz_id: dict(
                case_num=nrqz_id[0:4], site_name=nrqz_id[5:]
            ),
            to_fields=("case_num", "site_name"),
        )
        actual = field_map.map(nrqz_id="1111 Mr. Tower")
        expected = dict(case_num="1111", site_name="Mr. Tower")
        self.assertEqual(actual, expected)

    def test_from_fields_to_fields_with_converter(self):
        field_map = FieldMap(
            from_fields=("latitude", "longitude"),
            converter=lambda latitude, longitude: dict(
                lat_d=latitude[0:2],
                lat_m=latitude[2:4],
                lat_s=latitude[4:6],
                long_d=longitude[0:2],
                long_m=longitude[2:4],
                long_s=longitude[4:6],
            ),
            to_fields=("lat_m", "lat_s", "long_d", "long_m", "long_s"),
        )
        actual = field_map.map(latitude="112233", longitude="445566")
        expected = dict(
            lat_d="11", lat_m="22", lat_s="33", long_d="44", long_m="55", long_s="66"
        )
        self.assertEqual(actual, expected)

    def test_aliases_simple(self):
        data = {"Bar": "baz"}
        field_map = FieldMap(to_field="foo", from_fields={"foo": ("Foo", "Bar")})
        actual = field_map.map(**data)
        expected = {"foo": data["Bar"]}
        self.assertEqual(actual, expected)

        data = {"Foo": "baz"}
        actual = field_map.map(**data)
        expected = {"foo": data["Foo"]}
        self.assertEqual(actual, expected)

    def test_aliases_errors(self):
        data = {"Non-existent": "baz"}
        field_map = FieldMap(to_field="foo", from_fields={"foo": ("Foo", "Bar")})
        with self.assertRaises(ValueError):
            field_map.map(**data)

    def test_aliases_1_to_n(self):
        def handle_location(latitude, longitude):
            return {"location": (latitude, longitude)}

        data = {"lat": "11 22 33", "long": "44 55 66"}
        field_map = FieldMap(
            to_field="location",
            converter=handle_location,
            from_fields={"latitude": ["lat", "LAT"], "longitude": ["long", "LONG"]},
        )
        actual = field_map.map(**data)
        expected = {"location": (data["lat"], data["long"])}
        self.assertEqual(actual, expected)

    def test_aliases_n_to_1(self):
        def handle_location(latitude, longitude):
            return {"location": (latitude, longitude)}

        data = {"LAT": 30.1, "long": 30.2}
        field_map = FieldMap(
            converter=handle_location,
            to_field="location",
            from_fields={"latitude": ["lat", "LAT"], "longitude": ["long", "LONG"]},
        )
        actual = field_map.map(**data)
        expected = {"location": (data["LAT"], data["long"])}
        self.assertEqual(actual, expected)

    def test_aliases_n_to_n(self):
        def handle_dms(latitude, longitude):
            lat_d, lat_m, lat_s = latitude.split(" ")
            long_d, long_m, long_s = longitude.split(" ")
            return {
                "lat_d": lat_d,
                "lat_m": lat_m,
                "lat_s": lat_s,
                "long_d": long_d,
                "long_m": long_m,
                "long_s": long_s,
            }

        data = {"LAT": "30 31 32", "long.": "33 34 35"}
        field_map = FieldMap(
            from_fields={"latitude": ("LAT", "lat."), "longitude": ("LONG", "long.")},
            converter=handle_dms,
            to_fields=("lat_d", "lat_m", "lat_s", "long_d", "long_m", "long_s"),
        )
        actual = field_map.map(**data)
        expected = {
            "lat_d": "30",
            "lat_m": "31",
            "lat_s": "32",
            "long_d": "33",
            "long_m": "34",
            "long_s": "35",
        }
        self.assertEqual(actual, expected)

    def test_invert_aliases(self):
        aliases = {"latitude": ("LAT", "lat."), "longitude": ("LONG", "long.")}
        actual = FieldMap._invert_aliases(aliases)
        expected = {
            "LAT": "latitude",
            "lat.": "latitude",
            "LONG": "longitude",
            "long.": "longitude",
        }

        return self.assertEqual(actual, expected)
