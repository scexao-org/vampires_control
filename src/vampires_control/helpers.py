def get_dominant_filter(main_filter, diff_filter):
    # check if Halpha or SII filters are in
    if "HA" in diff_filter.upper():
        return "Halpha"
    elif "SII" in diff_filter.upper():
        return "SII"
    # otherwise use the main filter
    return main_filter
