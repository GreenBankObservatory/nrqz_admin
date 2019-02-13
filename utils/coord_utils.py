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


CONCISE_COORD_FORMAT = "{:3d} {:02d} {:2.3f}"
VERBOSE_COORD_FORMAT = "{:3d}° {:02d}′ {:2.3f}″ {}"


def lat_to_string(latitude, concise=False):
    if isinstance(latitude, float):
        latitude = dd_to_dms(latitude)
    if len(latitude) != 3:
        raise ValueError("latitude must be a 3-tuple")

    if latitude[0] < 0:
        latitude = (abs(i) for i in latitude)
        lat_hemi = "S"
    else:
        lat_hemi = "N"

    if concise:
        return f"{CONCISE_COORD_FORMAT.format(*latitude)}"
    return f"{VERBOSE_COORD_FORMAT.format(*latitude, lat_hemi)}"


def long_to_string(longitude, concise=False):
    if isinstance(longitude, float):
        longitude = dd_to_dms(longitude)
    if len(longitude) != 3:
        raise ValueError("longitude must be a 3-tuple")

    if longitude[0] < 0:
        longitude = (abs(i) for i in longitude)
        long_hemi = "W"
    else:
        long_hemi = "E"

    if concise:
        return f"{CONCISE_COORD_FORMAT.format(*longitude)}"
    return f"{VERBOSE_COORD_FORMAT.format(*longitude, long_hemi)}"


def coords_to_string(latitude, longitude, concise=False):
    latitude_str = lat_to_string(latitude, concise=concise)
    longitude_str = long_to_string(longitude, concise=concise)
    return f"{latitude_str}, {longitude_str}"


# https://regex101.com/r/vMa4Ov/5
coord_regex_str = (
    r"(?P<degrees>\-?\d{1,3}(?:\.\d+)?)\D*(?:(?P<minutes>\d{1,2})\D+"
    r"(?P<seconds>\d{1,2}(?:\.\d+)?)[^NnEeWwSs]+)?(?P<hemisphere>[NnEeWwSs])?"
)
coord_regex = re.compile(coord_regex_str)


def point_to_string(point, concise=False):
    longitude, latitude = point.coords
    return coords_to_string(latitude, longitude, concise=concise)


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


def split_coords(coords_str):
    try:
        latitude, longitude = coords_str.split()
    except ValueError:
        # if "," not in coords_str and "\t" not in coords_str:
        #     raise ValueError("Must be comma- or tab-separated!")
        if "\t" in coords_str:
            latitude, longitude = coords_str.split("\t")
        elif "," in coords_str:
            latitude, longitude = coords_str.split(",")
        else:
            latitude, longitude = coords_str.split("-")
            longitude = f"-{longitude}"

    return latitude, longitude


def parse_coords(coords):
    if isinstance(coords, str):
        latitude, longitude = split_coords(coords)
        latitude = latitude.strip()
        longitude = longitude.strip()
        return (parse_coord(latitude), parse_coord(longitude))
    return coords
