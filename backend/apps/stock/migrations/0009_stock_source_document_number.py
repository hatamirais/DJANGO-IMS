from django.db import migrations, models


def backfill_source_document_number(apps, schema_editor):
    Stock = apps.get_model("stock", "Stock")
    Transaction = apps.get_model("stock", "Transaction")
    OpeningBalanceImport = apps.get_model("stock", "OpeningBalanceImport")

    for stock in Stock.objects.select_related("receiving_ref").iterator():
        source_document_number = ""

        stock_transaction_filters = {
            "item_id": stock.item_id,
            "location_id": stock.location_id,
            "batch_lot": stock.batch_lot,
            "sumber_dana_id": stock.sumber_dana_id,
            "transaction_type": "IN",
        }
        receiving_reference_ids = list(
            Transaction.objects.filter(
                **stock_transaction_filters,
                reference_type="RECEIVING",
            )
            .values_list("reference_id", flat=True)
            .distinct()
        )
        opening_reference_ids = list(
            Transaction.objects.filter(
                **stock_transaction_filters,
                reference_type="INITIAL_IMPORT",
            )
            .values_list("reference_id", flat=True)
            .distinct()
        )

        if len(receiving_reference_ids) == 1 and not opening_reference_ids:
            if stock.receiving_ref_id == receiving_reference_ids[0]:
                source_document_number = stock.receiving_ref.document_number
        elif len(opening_reference_ids) == 1 and not receiving_reference_ids:
            opening_balance = (
                OpeningBalanceImport.objects.filter(pk=opening_reference_ids[0])
                .only("document_number")
                .first()
            )
            if opening_balance:
                source_document_number = opening_balance.document_number
        elif stock.receiving_ref_id and not receiving_reference_ids and not opening_reference_ids:
            source_document_number = stock.receiving_ref.document_number

        if not source_document_number:
            source_document_number = f"LEGACY-{stock.pk}"

        Stock.objects.filter(pk=stock.pk).update(
            source_document_number=source_document_number
        )

    transfer_in_rows = (
        Transaction.objects.filter(
            reference_type="TRANSFER",
            transaction_type="IN",
        )
        .exclude(reference_id__isnull=True)
        .values(
            "reference_id",
            "item_id",
            "location_id",
            "batch_lot",
            "sumber_dana_id",
        )
        .distinct()
    )
    for transfer_in in transfer_in_rows:
        destination_stock = (
            Stock.objects.filter(
                item_id=transfer_in["item_id"],
                location_id=transfer_in["location_id"],
                batch_lot=transfer_in["batch_lot"],
                sumber_dana_id=transfer_in["sumber_dana_id"],
            )
            .only("pk", "source_document_number")
            .first()
        )
        if not destination_stock:
            continue
        if not (
            destination_stock.source_document_number == f"LEGACY-{destination_stock.pk}"
            or destination_stock.source_document_number == "LEGACY"
        ):
            continue

        transfer_out = (
            Transaction.objects.filter(
                reference_type="TRANSFER",
                transaction_type="OUT",
                reference_id=transfer_in["reference_id"],
                item_id=transfer_in["item_id"],
                batch_lot=transfer_in["batch_lot"],
                sumber_dana_id=transfer_in["sumber_dana_id"],
            )
            .exclude(location_id=transfer_in["location_id"])
            .order_by("pk")
            .first()
        )
        if not transfer_out:
            continue

        source_stock = (
            Stock.objects.filter(
                item_id=transfer_out.item_id,
                location_id=transfer_out.location_id,
                batch_lot=transfer_out.batch_lot,
                sumber_dana_id=transfer_out.sumber_dana_id,
            )
            .exclude(source_document_number="")
            .order_by("pk")
            .first()
        )
        if source_stock and source_stock.source_document_number:
            Stock.objects.filter(pk=destination_stock.pk).update(
                source_document_number=source_stock.source_document_number
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
