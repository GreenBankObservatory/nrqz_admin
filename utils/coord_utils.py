import math
import re


def dms_to_dd(degrees, minutes, seconds):
    """Convert degrees, minutes, seconds to decimal degress"""

    fd = float(degrees)
    if fd < 0:
        return fd - float(minutes) / 60 - float(seconds) / 3600

    return fd + float(minutes) / 60 + float(seconds) / 3600


# https://en.wikipedia.org/wiki/Decimal_degrees#Example
def dd_to_dms(decimal):
    d = math.trunc(decimal)
    m = math.trunc((math.fabs(decimal) * 60) % 60)
    s = (math.fabs(decimal) * 60 * 60) % 60

    return (d, m, s)


def coords_to_string(latitude, longitude, concise=False):
    if isinstance(latitude, float):
        latitude = dd_to_dms(latitude)
    if isinstance(longitude, float):
        longitude = dd_to_dms(longitude)

    if concise:
        coord_format = "{:3d} {:02d} {:2.3f}"
        return f"{coord_format.format(*latitude)}, {coord_format.format(*longitude)}"
    else:
        if latitude[0] < 0:
            latitude = (abs(i) for i in latitude)
            lat_hemi = "S"
        else:
            lat_hemi = "N"

        if longitude[0] < 0:
            longitude = (abs(i) for i in longitude)
            long_hemi = "W"
        else:
            long_hemi = "E"
        coord_format = "{:3d}° {:02d}′ {:2.3f}″"
        return f"{coord_format.format(*latitude)} {lat_hemi}, {coord_format.format(*longitude)} {long_hemi}"


# https://regex101.com/r/vMa4Ov/5
coord_regex_str = (
    r"(?P<degrees>\-?\d{1,3}(?:\.\d+)?)\D*(?:(?P<minutes>\d{1,2})\D+"
    r"(?P<seconds>\d{1,2}(?:\.\d+)?)[^NnEeWwSs]+)?(?P<hemisphere>[NnEeWwSs])?"
)
coord_regex = re.compile(coord_regex_str)


def parse_coord(coord):
    match = coord_regex.match(coord)
    if not match:
        raise ValueError(f"Failed to parse {coord!r} with regex {coord_regex_str!r}")
    degrees = float(match["degrees"])
    if match["minutes"]:
        minutes = float(match["minutes"])
    else:
        minutes = None
    if match["seconds"]:
        seconds = float(match["seconds"])
    else:
        seconds = None

    if match["hemisphere"]:
        if degrees < 0:
            raise ValueError(
                "Cannot parse coordinate that indicates both a negative "
                "'degrees' and a 'hemisphere' (got '{degrees} {hemisphere}', "
                "from original value of {coord!r}, which makes no sense)".format(
                    degrees=match["degrees"],
                    hemisphere=match["hemisphere"],
                    coord=coord,
                )
            )
        hemisphere = match["hemisphere"].upper()
        if hemisphere in ["S", "W"]:
            degrees = -1 * degrees

    if minutes is None or seconds is None:
        return degrees
    else:
        return dms_to_dd(degrees=degrees, minutes=minutes, seconds=seconds)


def parse_coords(coords):
    try:
        latitude, longitude = coords.split()
    except ValueError:
        if "," not in coords:
            raise ValueError("Must be comma-separated!")
        latitude, longitude = coords.split(",")
    latitude = latitude.strip()
    longitude = longitude.strip()
    return (parse_coord(latitude), parse_coord(longitude))
