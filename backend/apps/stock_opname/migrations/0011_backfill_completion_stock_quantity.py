from django.db import migrations


STOCK_INCREASE_TYPES = {"IN", "RETURN"}
STOCK_DECREASE_TYPES = {"OUT"}


def reconstructed_completion_quantity(item, Transaction, db_alias):
    stock = item.stock
    completed_at = item.stock_opname.completed_at
    if not completed_at:
        return item.system_quantity

    quantity = stock.quantity
    later_transactions = Transaction.objects.using(db_alias).filter(
        item_id=stock.item_id,
        location_id=stock.location_id,
        batch_lot=stock.batch_lot,
        source_document_number=stock.source_document_number,
        sumber_dana_id=stock.sumber_dana_id,
        created_at__gt=completed_at,
    ).only("transaction_type", "quantity")

    # Transactions are append-only. Roll later ledger movements backward so
    # legacy completed opnames do not freeze deployment-time live stock.
    for transaction in later_transactions:
        if transaction.transaction_type in STOCK_INCREASE_TYPES:
            quantity -= transaction.quantity
        elif transaction.transaction_type in STOCK_DECREASE_TYPES:
            quantity += transaction.quantity
        else:
            return item.system_quantity

    return quantity


def backfill_completion_stock_quantity(apps, schema_editor):
    StockOpname = apps.get_model("stock_opname", "StockOpname")
    StockOpnameItem = apps.get_model("stock_opname", "StockOpnameItem")
    Transaction = apps.get_model("stock", "Transaction")
    db_alias = schema_editor.connection.alias

    completed_opname_ids = (
        StockOpname.objects.using(db_alias).filter(status="COMPLETED").values("pk")
    )
    completed_items = (
        StockOpnameItem.objects.using(db_alias)
        .filter(
            stock_opname_id__in=completed_opname_ids,
            completion_stock_quantity__isnull=True,
        )
        .select_related("stock", "stock_opname")
        .iterator(chunk_size=1000)
    )

    batch = []
    for item in completed_items:
        item.completion_stock_quantity = reconstructed_completion_quantity(
            item,
            Transaction,
            db_alias,
        )
        batch.append(item)
        if len(batch) >= 1000:
            StockOpnameItem.objects.using(db_alias).bulk_update(
                batch,
                ["completion_stock_quantity"],
            )
            batch = []

    if batch:
        StockOpnameItem.objects.using(db_alias).bulk_update(
            batch,
            ["completion_stock_quantity"],
        )


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
