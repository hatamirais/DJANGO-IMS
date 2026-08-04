import hashlib

from django.db import migrations, models


def _source_document_number(document_type, document_number, collision_documents):
    if document_number not in collision_documents:
        return document_number

    prefix = "RCV" if document_type == "RECEIVING" else "OBI"
    digest = hashlib.sha1(
        f"{document_type}:{document_number}".encode("utf-8")
    ).hexdigest()[:8]
    suffix_length = 100 - len(prefix) - len(digest) - 2
    return f"{prefix}-{digest}-{document_number[:suffix_length]}"


def backfill_transaction_source_document_number(apps, schema_editor):
    Transaction = apps.get_model("stock", "Transaction")
    Stock = apps.get_model("stock", "Stock")
    OpeningBalanceImport = apps.get_model("stock", "OpeningBalanceImport")
    Receiving = apps.get_model("receiving", "Receiving")

    receiving_document_numbers = set(
        Receiving.objects.values_list("document_number", flat=True)
    )
    opening_document_numbers = set(
        OpeningBalanceImport.objects.values_list("document_number", flat=True)
    )
    collision_documents = receiving_document_numbers & opening_document_numbers

    def transfer_source_document_number(tx):
        source_tx = tx
        if tx.transaction_type == "IN":
            source_tx = (
                Transaction.objects.filter(
                    reference_type="TRANSFER",
                    transaction_type="OUT",
                    reference_id=tx.reference_id,
                    item_id=tx.item_id,
                    batch_lot=tx.batch_lot,
                    sumber_dana_id=tx.sumber_dana_id,
                )
                .exclude(location_id=tx.location_id)
                .order_by("pk")
                .first()
            )
            if not source_tx:
                return ""

        source_stocks = Stock.objects.filter(
            item_id=source_tx.item_id,
            location_id=source_tx.location_id,
            batch_lot=source_tx.batch_lot,
            sumber_dana_id=source_tx.sumber_dana_id,
        ).exclude(source_document_number="")
        source_document_number = (
            source_stocks.filter(unit_price=source_tx.unit_price)
            .order_by("pk")
            .values_list("source_document_number", flat=True)
            .first()
        )
        if source_document_number:
            resolved_source_document_number = source_document_number
        else:
            resolved_source_document_number = (
                source_stocks.order_by("pk")
                .values_list("source_document_number", flat=True)
                .first()
                or ""
            )

        return resolved_source_document_number

    for tx in Transaction.objects.iterator():
        source_document_number = ""
        matching_stock_source_numbers = list(
            Stock.objects.filter(
                item_id=tx.item_id,
                location_id=tx.location_id,
                batch_lot=tx.batch_lot,
                sumber_dana_id=tx.sumber_dana_id,
            )
            .values_list("source_document_number", flat=True)
            .distinct()
            .order_by("source_document_number")
        )
        matching_price_stock_source_numbers = list(
            Stock.objects.filter(
                item_id=tx.item_id,
                location_id=tx.location_id,
                batch_lot=tx.batch_lot,
                sumber_dana_id=tx.sumber_dana_id,
                unit_price=tx.unit_price,
            )
            .values_list("source_document_number", flat=True)
            .distinct()
            .order_by("source_document_number")
        )
        if tx.reference_type == "INITIAL_IMPORT":
            opening_balance = (
                OpeningBalanceImport.objects.filter(pk=tx.reference_id)
                .only("document_number")
                .first()
            )
            if opening_balance:
                source_document_number = _source_document_number(
                    "INITIAL_IMPORT",
                    opening_balance.document_number,
                    collision_documents,
                )
        elif tx.reference_type == "RECEIVING":
            receiving = (
                Receiving.objects.filter(pk=tx.reference_id)
                .only("document_number")
                .first()
            )
            if receiving:
                source_document_number = _source_document_number(
                    "RECEIVING",
                    receiving.document_number,
                    collision_documents,
                )
        elif tx.reference_type == "TRANSFER":
            source_document_number = transfer_source_document_number(tx)

        if tx.reference_type == "TRANSFER" and source_document_number:
            pass
        elif len(matching_stock_source_numbers) == 1:
            source_document_number = matching_stock_source_numbers[0]
        elif len(matching_price_stock_source_numbers) == 1:
            source_document_number = matching_price_stock_source_numbers[0]
        elif (
            source_document_number
            and matching_stock_source_numbers
            and source_document_number not in matching_stock_source_numbers
        ):
            source_document_number = ""

        if not source_document_number:
            source_document_number = "LEGACY"

        Transaction.objects.filter(pk=tx.pk).update(
            source_document_number=source_document_number
        )


class Migration(migrations.Migration):

    dependencies = [
        ("receiving", "0015_backfill_no_expiry_sentinel"),
        ("stock", "0009_stock_source_document_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="source_document_number",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Original source document for the stock valuation layer moved by this transaction.",
                max_length=100,
            ),
        ),
        migrations.RunPython(
            backfill_transaction_source_document_number,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="transaction",
            name="source_document_number",
            field=models.CharField(
                default="LEGACY",
                help_text="Original source document for the stock valuation layer moved by this transaction.",
                max_length=100,
            ),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(
                fields=["source_document_number"], name="idx_trans_source_doc"
            ),
        ),
    ]
