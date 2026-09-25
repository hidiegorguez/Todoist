def get_duration_label(n):
    if n < 5:
        return 'Short'
    if n < 61:
        return 'Med'
    return 'Long'


def priority_inversal(n):
    """Todoist API priority is inverted: 4 is the highest, 1 the lowest."""
    return 5 - n
