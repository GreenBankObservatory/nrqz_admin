# Modified from: http://stackoverflow.com/a/323910/1883424
def itemAndNext(iterable):
    """Generator to yield an item and the next item.

    Args:
        iterable: An iterable

    Returns:
        tuple: A tuple of the current item and the next item"""

    iterator = iter(iterable)
    item = next(iterator)
    for next_item in iterator:
        yield (item, next_item)
        item = next_item
    yield (item, None)


def make_list_of_ranges_from_nums(nums):
    """Parse a list of numbers into a list of ranges.

    This is a helper function for get_str_from_nums(), and does all of the
    hard work of creating a list of ranges from a list of nums.

    Args:
        nums: A collection of numbers

    Returns:
        list: A list of length-2 tuples, with each tuple representing the
        min/max (inclusive) of a range.
    """

    # Make sure they are sorted
    nums = sorted(nums)
    ranges = []
    # The first range_start will be the first element of nums
    range_start = None
    for num, next_num in itemAndNext(nums):
        if not range_start:
            range_start = num

        if next_num is None or num + 1 != next_num:
            ranges.append((range_start, num))
            range_start = None

    return ranges


# Return this object's number ranges
#   as a nicely-formatted string
# Remember that the user's input string
#   could be something ridiculous,
#   such as '5-7,1-6', which yields
#   [1,2,3,4,5,6,7] and should be represented
#   as '1-7'
def get_str_from_nums(nums, join_str=","):
    """Create a string representation of a series of number ranges given a
    list of numbers.

    Remember that the user's input string could be something ridiculous,
    such as '5-7,1-6', which yields [1,2,3,4,5,6,7] and
    should be represented as '1-7'.

    Args:
        nums: A collection of numbers
        join_str: An optional argument representing the string that will be
        used to join the series of ranges together

    Returns:
        str: String representation of a series of number ranges
    """

    ranges_list = make_list_of_ranges_from_nums(nums)
    item_list = []

    for r in ranges_list:
        assert len(r) == 2
        if r[0] == r[1]:
            item_list.append(str(r[0]))
        else:
            item_list.append(str(r[0]) + "-" + str(r[1]))

    return join_str.join(item_list)
