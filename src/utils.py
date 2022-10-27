def if_any_none(*items):
    for item in items:
        if item is None:
            return True
    return False
