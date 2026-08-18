from django.db import DEFAULT_DB_ALIAS, migrations
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
    db_alias = schema_editor.connection.alias if schema_editor else DEFAULT_DB_ALIAS

    for option in SYSTEM_RECEIVING_TYPES:
        receiving_type, created = ReceivingTypeOption.objects.using(db_alias).get_or_create(
            code=option["code"],
            defaults={
                "name": option["name"],
                "is_active": option["is_active"],
                "is_system": option["is_system"],
                "requires_supplier": option["requires_supplier"],
                "sort_order": option["sort_order"],
            },
        )
        if not created:
            update_fields = []
            for field in (
                "name",
                "is_active",
                "is_system",
                "requires_supplier",
                "sort_order",
            ):
                if getattr(receiving_type, field) != option[field]:
                    setattr(receiving_type, field, option[field])
                    update_fields.append(field)
            if update_fields:
                receiving_type.save(using=db_alias, update_fields=update_fields)

    valid_codes = set(
        ReceivingTypeOption.objects.using(db_alias).values_list(
            "code",
            flat=True,
        )
    )
    missing_historical_codes = list(
        Receiving.objects.using(db_alias)
        .exclude(receiving_type__in=valid_codes)
        .exclude(receiving_type="")
        .exclude(receiving_type="RETURN_RS")
        .values_list("receiving_type", flat=True)
        .distinct()
        .order_by("receiving_type")
    )
    ReceivingTypeOption.objects.using(db_alias).bulk_create(
        [
            ReceivingTypeOption(
                code=code,
                name=code,
                is_active=False,
                is_system=False,
                requires_supplier=False,
                sort_order=100,
            )
            for code in missing_historical_codes
        ],
        ignore_conflicts=True,
    )

    valid_codes = ReceivingTypeOption.objects.using(db_alias).values_list(
        "code",
        flat=True,
    )
    invalid_types = list(
        Receiving.objects.using(db_alias)
        .exclude(receiving_type__in=valid_codes)
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
            f"{total} receiving row(s) without a receiving_type_options row. "
            f"Sample: {sample}"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("receiving", "0018_receivingtypeoption_system_fields"),
    ]

    operations = [
        migrations.RunPython(seed_system_receiving_types, migrations.RunPython.noop),
    ]
