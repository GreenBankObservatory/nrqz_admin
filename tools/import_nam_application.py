from pprint import pprint

from django import setup
setup()

from cases.models import Case, Antenna, Person, Site

key_to_thing = {
    Antenna: {
        "nrqzID": "nrqz_id",
        "lat": "lat",
        "lon": "lon",
        "gnd": "amsl",
        "gps": None,
        "1-ASurvey": None,
        "2-CSurvey": None,
        # TODO: Will probably need special handling
        "freq": "freq_low",
        # TODO: Will definitely need special handling
        "BandHi": "freq_high",
        # TODO: Will definitely need special handling
        "sysType": "technology",
    },
    Case: {

    },
    Person: {
        "caddr": None,
        "caddr2": None,
        "ccty": None,
        "cst": None,
        "czip": None,
        "cperson": None,
        "ccphone": "phone_num",
        "cfax": "fax_num",
        "ccell": None,
        "cemail": "email",
        "camendate": None,
        "cnumber": None,
    },
    Site: {
        "sitename": "name",
        "nant": None,
    },
    "unsorted": {
        "nrqzLinks": None,
        "AgencyNo": None,
        "Fed": None,
        "action": None,
        "fccfn": None,
        "call": None,
        "service": None,
        "legalname": None,
        "cityst": None,
        "asr": None,

        "purpose": None,
        "txmanuf": None,
        "mxtxpo": None,
        "amanuf": None,
        "bcomp": None,
        "tcomp": None,
        "type": None,
        "agl": None,
        "mxg": None,
        "aaz": None,
        "mbt": None,
        "mbtaz": None,
        "ebt": None,
        "mxebt": None,
        "txpo": None,
        "lbot": None,
        "ltl": None,
        "ltop": None,
        "EbtRng": None,
        "qzLim": None,
        "erp2gbt": None,
        "sel": None,
        "o1dis": None,
        "o1elev": None,
        "hznang": None,
        "pathtype": None,
        "aref": None,
        "tpa": None,
        "ga2gbt": None,
        "PanRng": None,
        "date": None,
        "apprvdate": None,
        "spare": None,
        "disgbt": None,
        "azgbt": None,
        "analogLim": None,
        "declin": None,
        "AzGaRange": None,
        "ElevGaRange": None,
        "PrevCases": None,
        "EbtGaRange": None,
        "CTsrc": None,
        "Rfreq": None,
        "sysBW": None,
        "qzPwrDen": None,
        "Lfs": None,
        "receivedDate": None,
        "SGobjects": None,
        "apprDate": None,
        "completeDate": None,
        "sgrs": None,
        "ha": None,
        "insp": None,
        "siWaived": None,
        "erpLimReq": None,
        "caplname": None,
        "AlterableTilt": None,
        "AlterablePan": None,
        "AlterableBW": None,
    }
}


def foo(path):
    with open(path) as file:
        lines = file.readlines()

    app_dict = {}
    for line in lines:
        stripped = line.strip()
        if stripped:
            parts = stripped.split(":")
            key = parts[0]
            value = ":".join(parts[1:])

            if key not in app_dict:
                app_dict[key] = value
            else:
                raise ValueError(f"Key {key} found more than once!")

    # pprint(app_dict)
    return app_dict

def bar(app_dict):
    antenna = Antenna()
    for key, value in key_to_thing.items():
        if value:
            if value[0] == Antenna:
                print(f"Setting field {value[1]} to {app_dict[key]}")
                setattr(antenna, value[1], app_dict[key])


path = "/home/sandboxes/tchamber/projects/nrqz_admin/examples/5763-1 AT&T_SW800/nrqzApplication.txt"
bar(foo(path))



# keys = [
#     ""
# ]
