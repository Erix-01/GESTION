from django import template

register = template.Library()

@register.filter(is_safe=True)
def format_fcfa(value):
    """Format a number as FCFA with thousands separator and no unnecessary decimals.

    Examples:
    1000 -> '1 000 FCFA'
    1234.5 -> '1 234.50 FCFA'
    None/invalid -> ''
    """
    if value is None:
        return ''
    try:
        # Convert Decimal or strings to float for formatting
        # Keep two decimals if there is fractional part
        val = float(value)
    except Exception:
        try:
            val = float(str(value))
        except Exception:
            return ''

    # Determine if integer
    if val.is_integer():
        formatted = f"{int(val):,}".replace(',', ' ')
        return f"{formatted} FCFA"
    else:
        # Keep two decimal places
        formatted = f"{val:,.2f}".replace(',', ' ')
        return f"{formatted} FCFA"