from django.db import migrations
from django.db.models import Count


SYSTEM_RECEIVING_TYPES = [
    {
        "code": "PROCUREMENT",
        "name": "Pengadaan",
        "is_active": True,
        "is_system": True,
        "requires_supplier": True,
        "sort_order": 10,
    },
    {
        "code": "GRANT",
        "name": "Hibah",
        "is_active": True,
        "is_system": True,
        "requires_supplier": False,
        "sort_order": 20,
    },
]


def seed_system_receiving_types(apps, schema_editor):
    ReceivingTypeOption = apps.get_model("receiving", "ReceivingTypeOption")
    Receiving = apps.get_model("receiving", "Receiving")

    for option in SYSTEM_RECEIVING_TYPES:
        ReceivingTypeOption.objects.update_or_create(
            code=option["code"],
            defaults={
                "name": option["name"],
                "is_active": option["is_active"],
                "is_system": option["is_system"],
                "requires_supplier": option["requires_supplier"],
                "sort_order": option["sort_order"],
            },
        )

    valid_codes = ReceivingTypeOption.objects.filter(is_active=True).values_list(
        "code",
        flat=True,
    )
    invalid_types = list(
        Receiving.objects.exclude(receiving_type__in=valid_codes)
        .exclude(receiving_type="RETURN_RS")
        .values("receiving_type")
        .annotate(row_count=Count("id"))
        .order_by("receiving_type")
    )
    if invalid_types:
        total = sum(row["row_count"] for row in invalid_types)
        sample = ", ".join(
            f"{row['receiving_type'] or '<blank>'}={row['row_count']}"
            for row in invalid_types[:5]
        )
        raise RuntimeError(
            "Cannot migrate receiving types: found "
            f"{total} receiving row(s) without an active receiving_type_options row. "
            f"Sample: {sample}"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("receiving", "0018_receivingtypeoption_system_fields"),
    ]

    operations = [
        migrations.RunPython(seed_system_receiving_types, migrations.RunPython.noop),
    ]
