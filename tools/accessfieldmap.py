from datetime import datetime
import pytz

from tools.fieldmap import FieldMap, coerce_num


def coerce_key(value):
    clean_value = value.strip()
    if clean_value in [None, ""]:
        return None
    float_value = float(value)
    int_value = int(float_value)
    if int_value == float_value:
        return int_value
    else:
        raise ValueError(f"{value} cannot be coerced to an int!")


def coerce_datetime(value):
    if value == "":
        return None
    date_str = value.split(" ")[0]
    month, day, year = date_str.split("/")
    return datetime(int(year), int(month), int(day), tzinfo=pytz.utc)


def coerce_positive_int(value):
    num = coerce_num(value)
    if num is None or num < 1:
        return None

    return int(num)

def coerce_bool(value):
    if value == "0":
        return False
    elif value == "1":
        return True
    else:
        raise ValueError(f"Unexpected boolean value: {value}")

def coerce_path(value):
    if value == "":
        return None

    return value.split("#")[1]



field_mappers = [
    FieldMap(to_field="nrqz_no", converter=coerce_key, from_field="NRQZ_NO"),
    FieldMap(to_field="comments", converter=None, from_field="COMMENTS"),
    FieldMap(to_field="applicant", converter=None, from_field="APPLICANT"),
    FieldMap(to_field="contact", converter=None, from_field="CONTACT"),
    FieldMap(to_field="phone", converter=None, from_field="PHONE"),
    FieldMap(to_field="fax", converter=None, from_field="FAX"),
    FieldMap(to_field="email", converter=None, from_field="EMAIL"),
    FieldMap(to_field="street", converter=None, from_field="ADDRESS"),
    FieldMap(to_field="city", converter=None, from_field="CITY"),
    FieldMap(to_field="county", converter=None, from_field="COUNTY"),
    FieldMap(to_field="state", converter=None, from_field="STATE"),
    FieldMap(to_field="zipcode", converter=None, from_field="ZIPCODE"),
    FieldMap(to_field="created_on", converter=coerce_datetime, from_field="DATEREC"),
    FieldMap(to_field="modified_on", converter=coerce_datetime, from_field="DATEALTERED"),
    FieldMap(to_field="completed", converter=coerce_bool, from_field="COMPLETED"),
    FieldMap(to_field="shutdown", converter=coerce_bool, from_field="SHUTDOWN"),
    FieldMap(to_field="completed_on", converter=coerce_datetime, from_field="DATECOMP"),
    FieldMap(to_field="sgrs_notify", converter=coerce_bool, from_field="SGRSNOTIFY"),
    FieldMap(to_field="sgrs_notified_on", converter=coerce_datetime, from_field="SGRSDATE"),
    FieldMap(to_field="radio_service", converter=None, from_field="RADIOSRV"),
    FieldMap(to_field="call_sign", converter=None, from_field="CALLSIGN"),
    FieldMap(to_field="fc_num", converter=None, from_field="FCNUMBER"),
    FieldMap(to_field="fcc_num", converter=None, from_field="FCCNUMBER"),
    FieldMap(to_field="num_freqs", converter=coerce_positive_int, from_field="NO_FREQS"),
    FieldMap(to_field="num_sites", converter=coerce_positive_int, from_field="NO_SITES"),
    FieldMap(to_field="num_outside", converter=coerce_positive_int, from_field="NO_OUTSIDE"),
    FieldMap(to_field="erpd_limit", converter=coerce_bool, from_field="ERPD_LIMIT"),
    FieldMap(to_field="si_waived", converter=coerce_bool, from_field="SIWAIVED"),
    FieldMap(to_field="si", converter=coerce_bool, from_field="SI"),
    FieldMap(to_field="si_done", converter=coerce_datetime, from_field="SIDONE"),
    FieldMap(to_field="hf_band", converter=coerce_bool, from_field="HF_BAND"),
    FieldMap(to_field="vhf_band", converter=coerce_bool, from_field="VHF_BAND"),
    FieldMap(to_field="uhf1_band", converter=coerce_bool, from_field="UHF1_BAND"),
    FieldMap(to_field="uhf2_band", converter=coerce_bool, from_field="UHF2_BAND"),
    FieldMap(to_field="l_band", converter=coerce_bool, from_field="L_BAND"),
    FieldMap(to_field="s_band", converter=coerce_bool, from_field="S_BAND"),
    FieldMap(to_field="c_band", converter=coerce_bool, from_field="C_BAND"),
    FieldMap(to_field="x_band", converter=coerce_bool, from_field="X_BAND"),
    FieldMap(to_field="ku_band", converter=coerce_bool, from_field="KU_BAND"),
    FieldMap(to_field="k_band", converter=coerce_bool, from_field="K_BAND"),
    FieldMap(to_field="ka_band", converter=coerce_bool, from_field="KA_BAND"),
    FieldMap(to_field="letter1", converter=coerce_path, from_field="LETTER1_Link"),
    FieldMap(to_field="letter2", converter=coerce_path, from_field="LETTER2_Link"),
    FieldMap(to_field="letter3", converter=coerce_path, from_field="LETTER3_Link"),
    FieldMap(to_field="letter4", converter=coerce_path, from_field="LETTER4_Link"),
    FieldMap(to_field="letter5", converter=coerce_path, from_field="LETTER5_Link"),
    FieldMap(to_field="letter6", converter=coerce_path, from_field="LETTER6_Link"),
    FieldMap(to_field="letter7", converter=coerce_path, from_field="LETTER7_Link"),
    FieldMap(to_field="letter8", converter=coerce_path, from_field="LETTER8_Link"),
]

# Generate a map of known_header->importer by "expanding" the from_fields of each FieldMap
# In this way we can easily and efficiently look up a given header and find its associated importer
# NOTE: applicant_field_map is the primary "export" of this module
applicant_field_map = {}
for importer in field_mappers:
    applicant_field_map[importer.from_field] = importer


if __name__ == "__main__":
    # Print out a simple report of the final header->field mappings
    # from_field_len is just the longest header in the map plus some padding
    from_field_len = max(len(from_field) for from_field in applicant_field_map) + 3
    for from_field, importer in applicant_field_map.items():
        print(f"{from_field!r:{from_field_len}}: {importer.to_field!r}")
