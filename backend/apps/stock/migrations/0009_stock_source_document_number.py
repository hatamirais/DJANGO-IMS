from django.db import migrations, models


def backfill_source_document_number(apps, schema_editor):
    Stock = apps.get_model("stock", "Stock")
    Transaction = apps.get_model("stock", "Transaction")
    OpeningBalanceImport = apps.get_model("stock", "OpeningBalanceImport")

    for stock in Stock.objects.select_related("receiving_ref").iterator():
        source_document_number = ""
        if stock.receiving_ref_id:
            source_document_number = stock.receiving_ref.document_number
        else:
            tx = (
                Transaction.objects.filter(
                    item_id=stock.item_id,
                    location_id=stock.location_id,
                    batch_lot=stock.batch_lot,
                    sumber_dana_id=stock.sumber_dana_id,
                    reference_type="INITIAL_IMPORT",
                    transaction_type="IN",
                )
                .order_by("created_at", "id")
                .first()
            )
            if tx:
                opening_balance = (
                    OpeningBalanceImport.objects.filter(pk=tx.reference_id)
                    .only("document_number")
                    .first()
                )
                if opening_balance:
                    source_document_number = opening_balance.document_number

        if not source_document_number:
            source_document_number = f"LEGACY-{stock.pk}"

        Stock.objects.filter(pk=stock.pk).update(
            source_document_number=source_document_number
        )


class Migration(migrations.Migration):

    dependencies = [
        ("stock", "0008_opening_balance_import"),
    ]

    operations = [
        migrations.AddField(
            model_name="stock",
            name="source_document_number",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Original source document that created this stock valuation layer.",
                max_length=100,
            ),
        ),
        migrations.RunPython(
            backfill_source_document_number,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="stock",
            name="uq_stock_batch",
        ),
        migrations.AlterField(
            model_name="stock",
            name="source_document_number",
            field=models.CharField(
                default="LEGACY",
                help_text="Original source document that created this stock valuation layer.",
                max_length=100,
            ),
        ),
        migrations.AddIndex(
            model_name="stock",
            index=models.Index(
                fields=["source_document_number"], name="idx_stock_source_doc"
            ),
        ),
        migrations.AddConstraint(
            model_name="stock",
            constraint=models.UniqueConstraint(
                fields=[
                    "item",
                    "location",
                    "batch_lot",
                    "sumber_dana",
                    "source_document_number",
                ],
                name="uq_stock_batch",
            ),
        ),
    ]
