from django.test import TestCase

from importers.fieldmap import FormMap, FieldMap, FieldMapError


class FormMapTestCase(TestCase):
    # def test_multiple_from_fields_with_non_callable_to_fields(self):
    #     """If multiple from_fields are given, to_fields must be callable"""

    #     data = {"latitude": 30.1, "longitude": 30.2}
    #     fm = FormMap(FieldMap(from_fields=("latitude", "longitude"), to_field="potato"))
    #     with self.assertRaises(FieldMapError):
    #         fm.render(data)

    # def test_callable_from_fields(self):
    #     """from_fields cannot be or contain any callable"""

    #     # If from_fields is a callable, this should be an error
    #     data = {"location_from": (30.1, 30.2)}
    #     fm = FormMap({lambda x: "foo": "location_to"})
    #     with self.assertRaises(FieldMapError):
    #         fm.render(data)

    #     # Same thing, but in a tuple...
    #     fm = FormMap({(lambda x: "foo",): "location_to"})
    #     with self.assertRaises(KeyError):
    #         fm.render(data)

    def test_1_to_1(self):
        data = {"location_from": (30.1, 30.2)}

        field_map = FieldMap(from_field="location_from", to_field="location_to")
        form_map = FormMap(field_maps=[field_map])
        actual = form_map.render(data)
        expected = {"location_to": data["location_from"]}
        self.assertEqual(actual, expected)

    def test_n_to_1(self):
        def handle_location(latitude, longitude):
            return {"location": (latitude, longitude)}

        data = {"latitude": 30.1, "longitude": 30.2}
        field_map = FieldMap(
            from_fields=("latitude", "longitude"),
            converter=handle_location,
            to_field="location",
        )
        form_map = FormMap(field_maps=[field_map])
        actual = form_map.render(data)
        expected = {"location": (data["latitude"], data["longitude"])}
        self.assertEqual(actual, expected)

    def test_1_to_n(self):
        def handle_sectors(sectors):
            a, b, c = sectors
            return {"a": a, "b": b, "c": c}

        data = {"sectors": (1, 2, 3)}
        field_map = FieldMap(
            from_field="sectors", converter=handle_sectors, to_fields=("a", "b", "c")
        )
        form_map = FormMap(field_maps=[field_map])
        actual = form_map.render(data)
        expected = {"a": 1, "b": 2, "c": 3}
        self.assertEqual(actual, expected)

    def test_n_to_n(self):
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

        data = {"latitude": "30 31 32", "longitude": "33 34 35"}
        field_map = FieldMap(
            from_fields=("latitude", "longitude"),
            converter=handle_dms,
            to_fields=("lat_d", "lat_m", "lat_s", "long_d", "long_m", "long_s"),
        )
        form_map = FormMap(field_maps=[field_map])
        actual = form_map.render(data)
        expected = {
            "lat_d": "30",
            "lat_m": "31",
            "lat_s": "32",
            "long_d": "33",
            "long_m": "34",
            "long_s": "35",
        }
        self.assertEqual(actual, expected)


class FieldMapTestCase(TestCase):
    def test_from_field_to_field(self):
        fm = FieldMap(from_field="case_num", to_field="case_num")
        print(fm)

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
        print(field_map)
        actual = field_map.map("11 22 33", "44 55 66")
        expected = dict(location=("11 22 33", "44 55 66"))
        self.assertEqual(actual, expected)

    def test_from_field_to_fields_with_converter(self):
        field_map = FieldMap(
            from_fields="nrqz_id",
            converter=lambda nrqz_id: dict(
                case_num=nrqz_id[0:4], site_name=nrqz_id[5:]
            ),
            to_fields=("case_num", "site_name"),
        )
        print(field_map)
        actual = field_map.map("1111 Mr. Tower")
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
        print(field_map)
        actual = field_map.map("112233", "445566")
        expected = dict(
            lat_d="11", lat_m="22", lat_s="33", long_d="44", long_m="55", long_s="66"
        )
        self.assertEqual(actual, expected)

    def test_aliases(self):
        pass
