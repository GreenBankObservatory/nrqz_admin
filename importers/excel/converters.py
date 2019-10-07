from datetime import date

from importers.converters import (
    coerce_bool,
    coerce_float,
    coerce_none,
    convert_mdy_datetime,
)


def convert_excel_path(path):
    # If the value is a date, then it can't be a path; return None
    if isinstance(path, date):
        return None

    # If the value can be converted to a bool, then it can't be a path; return None
    try:
        coerce_bool(path)
    except ValueError:
        pass
    else:
        return None

    # If the value can be converted to a date, then it can't be a path; return None
    try:
        convert_mdy_datetime(path)
    except ValueError:
        pass
    else:
        return None

    # If the value can be converted to a float, then it can't be a path; return None
    try:
        coerce_float(path)
    except ValueError:
        pass
    else:
        return None

    # If the value has a slash of some kind in it, then it is a path
    if r"\\" or r"/" in path:
        return path

    # Otherwise blow up
    raise ValueError(f"Something is wrong with path value: {path}")


def convert_sgrs_approval(sgrs_approval):
    # If it is already a date, then that's awesome; just use that
    # This also obviously indicates that sgrs_approval should be True
    if isinstance(sgrs_approval, date):
        sgrs_responded_on = sgrs_approval
        sgrs_approval = True
    else:
        # Otherwise, we try two things:
        # 1. Convert to a bool
        try:
            sgrs_approval = coerce_bool(sgrs_approval)
        except ValueError:
            # 2. If that didn't work, convert it to a datetime
            try:
                sgrs_responded_on = convert_mdy_datetime(sgrs_approval)
            except ValueError:
                # 3. If that doesn't work, do a very basic check
                # to see if it's a path or not. If it is, then SGRS has NOT approved!
                if r"\\" or r"/" in sgrs_approval:
                    sgrs_approval = False
                # If it isn't a path, then reject it; something is wrong
                else:
                    # And if that didn't work, raise an error
                    raise ValueError(
                        f"sgrs_approval ({sgrs_approval!r}) couldn't be converted to a date, boolean, or path!"
                    )
                sgrs_responded_on = None
            else:
                # If it did work, sgrs_approval must be true (since we know the date on which they approved)
                sgrs_approval = True
                sgrs_responded_on = None
        else:
            # If we successfully convert to bool, we obviously can't know the date on which they
            # responed (because a bool was there instead of a date)
            sgrs_responded_on = None

    return {"sgrs_approval": sgrs_approval, "sgrs_responded_on": sgrs_responded_on}


def convert_dominant_path(dominant_path):
    if coerce_none(dominant_path) is None:
        return None

    clean_dominant_path = str(dominant_path).strip().lower()
    if not clean_dominant_path:
        return None

    if clean_dominant_path.startswith("d"):
        return "diffraction"
    elif clean_dominant_path.startswith("s"):
        return "scatter"
    elif clean_dominant_path.startswith("f"):
        return "free_space"

    raise ValueError(f"Dominant path {dominant_path} could not be converted!")


def convert_nrao_aerpd(nrao_aerpd, meets_erpd_limit=None):
    """Convert nrqao_aerpd to a float. Convert meets_erpd_limit to a bool"""
    known_meets_erpd_limit_truthy_values = ["meets nrao limit"]
    known_meets_erpd_limit_falsey_values = ["exceedes app requested erpd", "pending"]
    if isinstance(meets_erpd_limit, str):
        clean_meets_erpd_limit = meets_erpd_limit.strip().lower()
        if coerce_none(clean_meets_erpd_limit) is None:
            meets_erpd_limit = False
        elif clean_meets_erpd_limit in known_meets_erpd_limit_truthy_values:
            meets_erpd_limit = True
        elif clean_meets_erpd_limit in known_meets_erpd_limit_falsey_values:
            meets_erpd_limit = False
        else:
            raise ValueError(
                f"meets_erpd_limit ({meets_erpd_limit!r}) is an unknown string value! "
                f"Known values: {known_meets_erpd_limit_truthy_values}"
            )
    else:
        meets_erpd_limit = False

    return {
        "nrao_aerpd": coerce_float(nrao_aerpd),
        "meets_erpd_limit": meets_erpd_limit,
    }
