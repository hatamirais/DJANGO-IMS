from django.db import migrations


def backfill_completion_stock_quantity(apps, schema_editor):
    StockOpname = apps.get_model("stock_opname", "StockOpname")
    StockOpnameItem = apps.get_model("stock_opname", "StockOpnameItem")

    completed_opname_ids = StockOpname.objects.filter(status="COMPLETED").values("pk")
    completed_items = (
        StockOpnameItem.objects.filter(
            stock_opname_id__in=completed_opname_ids,
            completion_stock_quantity__isnull=True,
        )
        .select_related("stock")
        .iterator(chunk_size=1000)
    )

    batch = []
    for item in completed_items:
        item.completion_stock_quantity = item.stock.quantity
        batch.append(item)
        if len(batch) >= 1000:
            StockOpnameItem.objects.bulk_update(
                batch,
                ["completion_stock_quantity"],
            )
            batch = []

    if batch:
        StockOpnameItem.objects.bulk_update(
            batch,
            ["completion_stock_quantity"],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("stock_opname", "0010_stockopnameitem_completion_stock_quantity"),
    ]

    operations = [
        migrations.RunPython(
            backfill_completion_stock_quantity,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
