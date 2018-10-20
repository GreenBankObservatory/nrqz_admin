def prompt(string, valid_responses=None):
    if valid_responses:
        types = set([type(vr) for vr in valid_responses])
        if not len(types) == 1:
            raise ValueError("valid_responses must all be of the same type")

        response_type = types.pop()

    print("{} {}".format(string, valid_responses))
    while True:
        response = input().strip().lower()
        if not valid_responses:
            return response

        try:
            response = response_type(response)
            valid_responses.index(response)
        except (TypeError, ValueError):
            print("Invalid response; please choose from: {}"
                  .format(valid_responses))
        else:
            return response
