def money_format(x):
    """
    Format a number as currency.

    Args:
        x (int or float): The number to format.

    Returns:
        str: The formatted currency string.
    """
    if isinstance(x, (int, float)):
        return "R${:,.2f}".format(x)
    return x
