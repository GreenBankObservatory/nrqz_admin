"""Project-wide constants"""

# Unit conversions
FEET_IN_A_METER = 0.3048

# Data Sources
WEB = "web"
EXCEL = "excel"
ACCESS_PRELIM_TECHNICAL = "access_prelim_technical"
ACCESS_TECHNICAL = "access_technical"
ACCESS_PRELIM_APPLICATION = "access_prelim_application"
ACCESS_APPLICATION = "access_application"
NAM_APPLICATION = "nam_application"


# Misc.

# Empirically determined. This is solely to avoid obviously-wrong
# case numbers from being imported
MAX_VALID_CASE_NUMBER = 12000
MIN_VALID_CASE_NUMBER = 100


NAD27_SRID = 4267
NAD83_SRID = 4269
WGS84_SRID = 4326
NAVD88_SRID = 5703
