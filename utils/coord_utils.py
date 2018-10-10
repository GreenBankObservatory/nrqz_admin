import math


def dms_to_dd(degrees, minutes, seconds):
    """Convert degrees, minutes, seconds to decimal degress"""

    dd = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    return dd

# https://en.wikipedia.org/wiki/Decimal_degrees#Example
def dd_to_dms(decimal):
    d = math.trunc(decimal)
    m = math.trunc((math.fabs(decimal) * 60) % 60)
    s = (math.fabs(decimal) * 60 * 60) % 60

    return (d, m, s)
