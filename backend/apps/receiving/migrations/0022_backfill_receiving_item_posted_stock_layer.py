from collections import defaultdict, deque

from django.db import migrations


def backfill_receiving_item_posted_stock_layer(apps, schema_editor):
    Receiving = apps.get_model("receiving", "Receiving")
    ReceivingItem = apps.get_model("receiving", "ReceivingItem")
    Transaction = apps.get_model("stock", "Transaction")

    receiving_ids = (
        ReceivingItem.objects.filter(posted_sumber_dana__isnull=True)
        .exclude(receiving_id__isnull=True)
        .values_list("receiving_id", flat=True)
        .distinct()
    )
    receiving_by_id = {
        receiving.pk: receiving
        for receiving in Receiving.objects.filter(pk__in=receiving_ids).only(
            "pk",
            "document_number",
            "sumber_dana_id",
        )
    }

    for receiving_id, receiving in receiving_by_id.items():
        transaction_layers = defaultdict(deque)
        transactions = (
            Transaction.objects.filter(
                reference_type="RECEIVING",
                reference_id=receiving_id,
                transaction_type="IN",
            )
            .order_by("pk")
            .values(
                "item_id",
                "location_id",
                "batch_lot",
                "quantity",
                "unit_price",
                "sumber_dana_id",
                "source_document_number",
            )
        )
        for tx in transactions:
            key = (
                tx["item_id"],
                tx["location_id"],
                tx["batch_lot"],
                tx["quantity"],
                tx["unit_price"],
            )
            transaction_layers[key].append(tx)

        pending_updates = []
        items = (
            ReceivingItem.objects.filter(
                receiving_id=receiving_id,
                posted_sumber_dana__isnull=True,
            )
            .order_by("pk")
            .only(
                "pk",
                "item_id",
                "location_id",
                "batch_lot",
                "quantity",
                "unit_price",
                "posted_sumber_dana_id",
                "posted_source_document_number",
            )
        )
        for item in items:
            key = (
                item.item_id,
                item.location_id,
                item.batch_lot,
                item.quantity,
                item.unit_price,
            )
            if not transaction_layers[key]:
                continue
            tx = transaction_layers[key].popleft()
            item.posted_sumber_dana_id = (
                tx["sumber_dana_id"] or receiving.sumber_dana_id
            )
            item.posted_source_document_number = (
                tx["source_document_number"] or receiving.document_number
            )
            pending_updates.append(item)

        if pending_updates:
            ReceivingItem.objects.bulk_update(
                pending_updates,
                ["posted_sumber_dana", "posted_source_document_number"],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("receiving", "0021_receiving_item_posted_stock_layer"),
        ("stock", "0013_alter_unit_price_precision"),
    ]

    operations = [
        migrations.RunPython(
            backfill_receiving_item_posted_stock_layer,
            migrations.RunPython.noop,
        ),
    ]
