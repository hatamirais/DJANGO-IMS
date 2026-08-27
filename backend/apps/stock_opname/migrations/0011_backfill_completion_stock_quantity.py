from django.db import migrations


CHUNK_SIZE = 1000
STOCK_INCREASE_TYPES = {"IN", "RETURN"}
STOCK_DECREASE_TYPES = {"OUT"}


def stock_layer_key(stock):
    return (
        stock.item_id,
        stock.location_id,
        stock.batch_lot,
        stock.source_document_number,
        stock.sumber_dana_id,
    )


def transaction_layer_key(transaction):
    return (
        transaction.item_id,
        transaction.location_id,
        transaction.batch_lot,
        transaction.source_document_number,
        transaction.sumber_dana_id,
    )


def batched(iterable, size):
    batch = []
    for value in iterable:
        batch.append(value)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def transactions_by_layer_for_items(items, Transaction, db_alias):
    dated_items = [
        item
        for item in items
        if item.created_at and item.stock_opname.completed_at
    ]
    if not dated_items:
        return {}

    stocks = [item.stock for item in dated_items]
    layer_keys = {stock_layer_key(stock) for stock in stocks}
    transactions = (
        Transaction.objects.using(db_alias)
        .filter(
            item_id__in={stock.item_id for stock in stocks},
            location_id__in={stock.location_id for stock in stocks},
            batch_lot__in={stock.batch_lot for stock in stocks},
            source_document_number__in={
                stock.source_document_number for stock in stocks
            },
            sumber_dana_id__in={stock.sumber_dana_id for stock in stocks},
            created_at__gt=min(item.created_at for item in dated_items),
            created_at__lte=max(
                item.stock_opname.completed_at for item in dated_items
            ),
        )
        .only(
            "item_id",
            "location_id",
            "batch_lot",
            "source_document_number",
            "sumber_dana_id",
            "transaction_type",
            "quantity",
            "created_at",
        )
    )

    grouped = {}
    for transaction in transactions:
        key = transaction_layer_key(transaction)
        if key in layer_keys:
            grouped.setdefault(key, []).append(transaction)
    return grouped


def reconstructed_completion_quantity(item, transactions_by_layer):
    stock = item.stock
    snapshot_at = item.created_at
    completed_at = item.stock_opname.completed_at
    if not snapshot_at or not completed_at:
        return item.system_quantity

    quantity = item.system_quantity
    transactions = transactions_by_layer.get(stock_layer_key(stock), [])

    # Start from the frozen item snapshot and replay ledger movements
    # up to completion. This avoids trusting mutable live Stock.quantity.
    for transaction in transactions:
        if not snapshot_at < transaction.created_at <= completed_at:
            continue
        if transaction.transaction_type in STOCK_INCREASE_TYPES:
            quantity += transaction.quantity
        elif transaction.transaction_type in STOCK_DECREASE_TYPES:
            quantity -= transaction.quantity
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

    for batch in batched(completed_items, CHUNK_SIZE):
        transactions_by_layer = transactions_by_layer_for_items(
            batch, Transaction, db_alias
        )
        for item in batch:
            item.completion_stock_quantity = reconstructed_completion_quantity(
                item,
                transactions_by_layer,
            )
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
