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
    Case: {},
    Person: {
        # Contact address, line 1
        "caddr": None,
        # Contact address, line 2
        "caddr2": None,
        # Contact city
        "ccty": None,
        # Contact state
        "cst": None,
        # Contact zip
        "czip": None,
        # Contact name
        "cperson": None,
        # Contact phone
        "ccphone": "phone_num",
        # Contact fax
        "cfax": "fax_num",
        # Contact cell phone
        "ccell": None,
        # Contact email
        "cemail": "email",
        # Last modified date (probably ignore this, it looks like it's manual)
        "camendate": None,
        # Unique id of contact? Ignore?
        "cnumber": None,
    },
    "unsorted": {
        # Site name/location
        "sitename": "name",
        # Number of antennas
        "nant": None,
        # Previous NRQZ case numbers, comma-separated
        "nrqzLinks": None,
        # ???
        "AgencyNo": None,
        # Federal Government Entity (bool)
        "Fed": None,
        # Requested action (1-4)
        "action": None,
        # File/Docket/Assignment #
        "fccfn": None,
        # Call sign
        "call": None,
        # Radio service/station class
        "service": None,
        # Applicant name
        "legalname": None,
        # City/State
        "cityst": None,
        # ASR num.
        "asr": None,
        # Application reason/purpose
        "purpose": None,
        # Transmitter manufacturer
        "txmanuf": None,
        # Max transmitter output power
        "mxtxpo": None,
        # Antenna manufacturer
        "amanuf": None,
        # Bottom loss components
        "bcomp": None,
        # Top loss components
        "tcomp": None,
        # Can have more than one of these? ---
        # Antenna Type
        "type": None,
        # cragl ; Antenna center of radiation above ground level (m)
        "agl": None,
        # MxG ; Antenna maximum gain (dBi)
        "mxg": None,
        # Az ; Azimuth of antenna main beam or center of the pan range (degress True) (blank if omni)
        "aaz": None,
        # MeBT ; Mechanical Down Tilt (deg) (negative if up tilt)
        "mbt": None,
        # mBTaz ; Mechnical Down tilt Azimuth (deg)
        "mbtaz": None,
        # elBT ; Electrical Down tilt (deg) (negative if up tilt)
        "ebt": None,
        # MxEbt ; Maximum tilt range if electrical beam tilt is user adjustable (deg) (ex 0-8, 2-4, etc)
        "mxebt": None,
        # TxPwr ; Transmitter output power (dBW or xx.xxx w (Watts))
        "txpo": None,
        # Lbot ; Loss at tower bottom, includes jumper, filters, etc. (dB)
        "lbot": None,
        # LtxLine ; Loss of main transmission line (dB)
        "ltl": None,
        # Ltop ; Loss at tower top, includes jumper, filters, etc. (dB)
        "ltop": None,
        # ?? This can't be right.... verify this map
        # PanRange ; Pan Range if Beam Azimuth is user adjustable (deg) (ex. 60 if pan = +- 30 degrees)
        "EbtRng": None,
        # ???
        "qzLim": None,
        # ???
        "erp2gbt": None,
        # ???
        "sel": None,
        # ???
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
    },
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
