from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


PRICE_MAX_DIGITS = 23
PRICE_DECIMAL_PLACES = 10
PRICE_QUANT = Decimal("0.0000000001")


def validate_finite_decimal(value, *, field_label="Nilai"):
    if value in (None, ""):
        return value

    decimal_value = value
    if not isinstance(decimal_value, Decimal):
        try:
            decimal_value = Decimal(str(value).strip())
        except (InvalidOperation, TypeError, ValueError):
            return value

    if not decimal_value.is_finite():
        raise ValidationError(f"{field_label} tidak boleh NaN atau Infinity.")

    return decimal_value


def parse_decimal_input(value, *, field_label="Nilai", allow_empty=False):
    raw_value = (value or "").strip().replace(",", ".").replace(" ", "")
    if not raw_value:
        if allow_empty:
            return None
        return Decimal("0")

    try:
        decimal_value = Decimal(raw_value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError(f"format {field_label} tidak valid: '{raw_value}'") from exc

    return validate_finite_decimal(decimal_value, field_label=field_label)


def validate_decimal_precision(value, *, max_digits, decimal_places, field_label="Nilai"):
    if value in (None, ""):
        return value
    decimal_value = validate_finite_decimal(value, field_label=field_label)
    exponent = decimal_value.as_tuple().exponent
    actual_decimal_places = max(-exponent, 0)
    whole_digits = max(decimal_value.copy_abs().adjusted() + 1, 0) if decimal_value else 1
    max_whole_digits = max_digits - decimal_places
    if actual_decimal_places > decimal_places or whole_digits > max_whole_digits:
        raise ValidationError(
            f"{field_label} maksimal {max_digits} digit dan {decimal_places} angka desimal."
        )
    return decimal_value


def quantize_price(value):
    """Normalize unit-price precision without converting user-facing delimiters."""
    if value in (None, ""):
        return value
    return validate_finite_decimal(value, field_label="Harga satuan").quantize(
        PRICE_QUANT
    )


def format_price_exact(value):
    """Format a stored price with up to PRICE_DECIMAL_PLACES decimal places."""
    if value in (None, ""):
        return ""
    decimal_value = validate_finite_decimal(value, field_label="Harga satuan")
    label = format(decimal_value, "f")
    if "." in label:
        label = label.rstrip("0").rstrip(".")
    return label or "0"


def format_price_input(value):
    """Format a price for form JSON: cents when exact, more decimals when needed."""
    label = format_price_exact(value)
    if not label:
        return label
    if "." not in label:
        return f"{label}.00"
    whole, fractional = label.split(".", 1)
    if len(fractional) == 1:
        return f"{whole}.{fractional}0"
    return label
