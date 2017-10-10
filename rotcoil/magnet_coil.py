"""Main coil information."""

_dict = {
    'BS': 3,
    'BQF': 26.25,
    'BQD': 27.50,
    'S15': 11.25,
    'Q14': 20.00,
    'Q20': 23.25,
    'Q30': 23.25,
}


def get_number_of_turns(magnet_name):
    """Get the main coil number of turns for the specified magnet."""
    nr_turns = None
    for key in _dict.keys():
        if key in magnet_name:
            nr_turns = _dict[key]
    return nr_turns
