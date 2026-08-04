from django.db import migrations


PRICE_MAX_WHOLE_DIGITS = 13
PRICE_DECIMAL_PLACES = 10


def _violates_price_precision(value):
    if value is None:
        return False
    value = value.copy_abs()
    decimal_places = max(-value.as_tuple().exponent, 0)
    whole_digits = max(value.adjusted() + 1, 0) if value else 1
    return decimal_places > PRICE_DECIMAL_PLACES or whole_digits > PRICE_MAX_WHOLE_DIGITS


def validate_unit_price_precision(apps, schema_editor):
    checks = (
        ("receiving", "ReceivingItem", "unit_price"),
        ("receiving", "ReceivingOrderItem", "unit_price"),
    )
    violations = []
    for app_label, model_name, field_name in checks:
        model = apps.get_model(app_label, model_name)
        count = sum(
            1
            for value in model.objects.values_list(field_name, flat=True).iterator()
            if _violates_price_precision(value)
        )
        if count:
            violations.append(f"{model_name}.{field_name}: {count}")
    if violations:
        raise RuntimeError(
            "Cannot widen unit-price precision; existing values exceed 23,10: "
            + ", ".join(violations)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("receiving", "0015_backfill_no_expiry_sentinel"),
    ]

    operations = [
        migrations.RunPython(validate_unit_price_precision, migrations.RunPython.noop),
    ]
