import re

# https://regex101.com/r/g6NM6e/1
CASE_REGEX = re.compile(
    r"(?:(?:NRQZ ID )|(?:NRQZ#)|(?:Case\s*))(?P<case_num>\d+)", re.IGNORECASE
)
CASE_REGEX2 = re.compile(r"(?P<case_num>\d{3,})-\d{,4}")

PCASE_REGEX = re.compile(r"NRQZ#P(\d+)", re.IGNORECASE)


def derive_related_case_nums(case):
    """Given a case/pcase, attempt to derive all related case numbers"""
    matches1 = CASE_REGEX.findall(case.comments)
    matches2 = CASE_REGEX2.findall(case.comments)

    case_nums = set()
    if matches1:
        case_nums.update(int(case_num) for case_num in matches1)

    if matches2:
        case_nums.update(int(case_num) for case_num in matches2)

    return list(case_nums)


def derive_related_pcases(case):
    """Given a case/pcase, attempt to derive all related case numbers"""

    m = PCASE_REGEX.findall(case.comments)
    if m:
        pcase_nums = [int(pcase_num) for pcase_num in m]
    else:
        pcase_nums = []

    return pcase_nums
