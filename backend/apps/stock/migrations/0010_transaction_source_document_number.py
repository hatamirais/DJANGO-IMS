from django.db import migrations, models


def backfill_transaction_source_document_number(apps, schema_editor):
    Transaction = apps.get_model("stock", "Transaction")
    Stock = apps.get_model("stock", "Stock")
    OpeningBalanceImport = apps.get_model("stock", "OpeningBalanceImport")
    Receiving = apps.get_model("receiving", "Receiving")

    for tx in Transaction.objects.iterator():
        source_document_number = ""
        matching_stock_source_numbers = list(
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
                source_document_number = opening_balance.document_number
        elif tx.reference_type == "RECEIVING":
            receiving = (
                Receiving.objects.filter(pk=tx.reference_id)
                .only("document_number")
                .first()
            )
            if receiving:
                source_document_number = receiving.document_number

        if len(matching_stock_source_numbers) == 1:
            source_document_number = matching_stock_source_numbers[0]
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
