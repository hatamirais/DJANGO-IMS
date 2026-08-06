from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from django import template

from apps.core.decimal_validation import format_price_exact


register = template.Library()


def _to_decimal(value):
    if value is None:
        return Decimal("0")

    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


@register.filter
def id_decimal(value, places=2):
    """Format number with Indonesian separators (1.234.567,89)."""
    number = _to_decimal(value)

    try:
        places_int = int(places)
    except (TypeError, ValueError):
        places_int = 2

    if places_int < 0:
        places_int = 0

    formatted = f"{number:,.{places_int}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


@register.filter
def id_price_exact(value):
    """Format a stored unit price with Indonesian separators and exact decimals."""
    label = format_price_exact(value)
    if not label:
        return ""

    return _format_exact_indonesian(label)


@register.filter
def id_value_exact(value):
    """Format a calculated money value with Indonesian separators and exact decimals."""
    number = _to_decimal(value)
    label = format(number, "f")
    if "." in label:
        label = label.rstrip("0").rstrip(".")
    return _format_exact_indonesian(label or "0")


def _format_exact_indonesian(label):
    sign = ""
    if label.startswith("-"):
        sign = "-"
        label = label[1:]

    whole, separator, fractional = label.partition(".")
    grouped_whole = f"{int(whole or '0'):,}".replace(",", ".")
    if separator:
        return f"{sign}{grouped_whole},{fractional}"
    return f"{sign}{grouped_whole}"


@register.filter
def idr(value):
    """Format currency in Indonesian Rupiah style."""
    return f"Rp {id_decimal(value, 0)}"


@register.filter
def safe_media_url(value):
    """Allow only root-relative media URLs (offline-first deployment)."""
    if not value:
        return ""

    try:
        url = str(value).strip()
    except Exception:
        return ""

    if not url:
        return ""

    parsed = urlparse(url)
    if url.startswith("/") and not parsed.scheme and not parsed.netloc:
        return url

    return ""
