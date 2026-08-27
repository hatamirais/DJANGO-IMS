from django.db import migrations, models


def backfill_completion_stock_quantity(apps, schema_editor):
    StockOpname = apps.get_model("stock_opname", "StockOpname")
    StockOpnameItem = apps.get_model("stock_opname", "StockOpnameItem")
    db_alias = schema_editor.connection.alias

    completed_opname_ids = (
        StockOpname.objects.using(db_alias).filter(status="COMPLETED").values("pk")
    )
    StockOpnameItem.objects.using(db_alias).filter(
        stock_opname_id__in=completed_opname_ids,
        completion_stock_quantity__isnull=True,
    ).update(completion_stock_quantity=models.F("system_quantity"))


class Migration(migrations.Migration):

    dependencies = [
        ("stock", "0013_alter_unit_price_precision"),
        ("stock_opname", "0010_stockopnameitem_completion_stock_quantity"),
    ]

    operations = [
        migrations.RunPython(
            backfill_completion_stock_quantity,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
