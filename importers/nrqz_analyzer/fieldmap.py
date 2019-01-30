"""Field mappings for NRQZ Analyzer Data"""

from django_import_data import FormMap, OneToOneFieldMap, ManyToOneFieldMap

from cases.forms import CaseForm, PersonForm, FacilityForm, StructureForm

from importers.converters import (
    coerce_location,
    convert_nrqz_id_to_case_num,
    coerce_float,
)

NAM_APPLICATION = "nam_application"


def convert_street(caddr=None, caddr2=None):
    parts = []
    if caddr:
        parts.append(caddr)
    if caddr2:
        parts.append(caddr2)
    return " ".join(parts)


class ApplicantFormMap(FormMap):
    field_maps = [OneToOneFieldMap(from_field="legalname", to_field="name")]
    form_class = PersonForm
    form_defaults = {"data_source": NAM_APPLICATION}


class ContactFormMap(FormMap):
    field_maps = [
        ManyToOneFieldMap(
            from_fields=("caddr", "caddr2"), converter=convert_street, to_field="street"
        ),
        OneToOneFieldMap(from_field="ccty", to_field="city"),
        OneToOneFieldMap(from_field="cst", to_field="state"),
        OneToOneFieldMap(from_field="czip", to_field="zipcode"),
        OneToOneFieldMap(from_field="cperson", to_field="name"),
        OneToOneFieldMap(from_field="ccphone", to_field="phone_num"),
        OneToOneFieldMap(from_field="ccphone", to_field="phone_num"),
        # TODO
        # OneToOneFieldMap(from_field="cfax", to_field=""),
        OneToOneFieldMap(from_field="camendate", to_field="original_modified_on")
        # Unique id of contact? Ignore?
        # OneToOneFieldMap(from_field="cnumber", to_field="")
    ]
    form_class = PersonForm
    form_defaults = {"data_source": NAM_APPLICATION}


class CaseFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            from_field="nrqzID",
            converter=convert_nrqz_id_to_case_num,
            to_field="case_num",
        ),
        # TODO: Should this base Facility-level?
        OneToOneFieldMap(from_field="service", to_field="radio_service"),
    ]
    form_class = CaseForm
    form_defaults = {"data_source": NAM_APPLICATION}


class FacilityFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(from_field="nrqzID", to_field="nrqz_id"),
        OneToOneFieldMap(
            from_field="nrqzID",
            converter=convert_nrqz_id_to_case_num,
            to_field="case_num",
        ),
        ManyToOneFieldMap(
            from_fields={"latitude": ["lat"], "longitude": ["lon"]},
            converter=coerce_location,
            to_field="location",
        ),
        OneToOneFieldMap(from_field="gnd", to_field="amsl"),
        # OneToOneFieldMap(from_field="gps", to_field=""),
        # OneToOneFieldMap(from_field="1-ASurvey", to_field=""),
        # OneToOneFieldMap(from_field="2-CSurvey", to_field=""),
        # TODO: CHECK
        OneToOneFieldMap(from_field="freq", to_field="freq_low"),
        # TODO: CHECK
        OneToOneFieldMap(from_field="BandHi", to_field="freq_high"),
        # TODO: CHECK
        OneToOneFieldMap(from_field="sysType", to_field="technology"),
        OneToOneFieldMap(from_field="sitename", to_field="site_name"),
        # TODO
        # OneToOneFieldMap(from_field="nant", to_field="site_name"),
        OneToOneFieldMap(from_field="fccfn", to_field="fcc_file_num"),
        OneToOneFieldMap(from_field="call", to_field="call_sign"),
        OneToOneFieldMap(
            from_field="mxtxpo", converter=coerce_float, to_field="max_tx_power"
        ),
    ]
    form_class = FacilityForm
    form_defaults = {"data_source": NAM_APPLICATION}


class StructureFormMap(FormMap):
    field_maps = [OneToOneFieldMap("asr")]
    form_class = StructureForm
    form_defaults = {"data_source": NAM_APPLICATION}


APPLICANT_FORM_MAP = ApplicantFormMap()
CONTACT_FORM_MAP = ContactFormMap()
CASE_FORM_MAP = CaseFormMap()
FACILITY_FORM_MAP = FacilityFormMap()
STRUCTURE_FORM_MAP = StructureFormMap()