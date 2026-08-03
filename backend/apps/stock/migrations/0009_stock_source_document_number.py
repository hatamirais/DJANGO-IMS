import hashlib

from django.db import migrations, models
from django.db.models import Sum


def _source_document_number(document_type, document_number, collision_documents):
    if document_number not in collision_documents:
        return document_number

    prefix = "RCV" if document_type == "RECEIVING" else "OBI"
    digest = hashlib.sha1(
        f"{document_type}:{document_number}".encode("utf-8")
    ).hexdigest()[:8]
    suffix_length = 100 - len(prefix) - len(digest) - 2
    return f"{prefix}-{digest}-{document_number[:suffix_length]}"


def _transfer_source_stock(Stock, transfer_out):
    source_stocks = Stock.objects.filter(
        item_id=transfer_out.item_id,
        location_id=transfer_out.location_id,
        batch_lot=transfer_out.batch_lot,
        sumber_dana_id=transfer_out.sumber_dana_id,
    ).exclude(source_document_number="")
    priced_source_stock = (
        source_stocks.filter(unit_price=transfer_out.unit_price)
        .order_by("pk")
        .first()
    )
    if priced_source_stock:
        return priced_source_stock
    return source_stocks.order_by("pk").first()


def backfill_source_document_number(apps, schema_editor):
    Stock = apps.get_model("stock", "Stock")
    Transaction = apps.get_model("stock", "Transaction")
    OpeningBalanceImport = apps.get_model("stock", "OpeningBalanceImport")
    Receiving = apps.get_model("receiving", "Receiving")
    StockTransferItem = apps.get_model("stock", "StockTransferItem")

    receiving_document_numbers = set(
        Receiving.objects.values_list("document_number", flat=True)
    )
    opening_document_numbers = set(
        OpeningBalanceImport.objects.values_list("document_number", flat=True)
    )
    collision_documents = receiving_document_numbers & opening_document_numbers

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
                source_document_number = _source_document_number(
                    "RECEIVING",
                    stock.receiving_ref.document_number,
                    collision_documents,
                )
        elif len(opening_reference_ids) == 1 and not receiving_reference_ids:
            opening_balance = (
                OpeningBalanceImport.objects.filter(pk=opening_reference_ids[0])
                .only("document_number")
                .first()
            )
            if opening_balance:
                source_document_number = _source_document_number(
                    "INITIAL_IMPORT",
                    opening_balance.document_number,
                    collision_documents,
                )
        elif stock.receiving_ref_id and not receiving_reference_ids and not opening_reference_ids:
            source_document_number = _source_document_number(
                "RECEIVING",
                stock.receiving_ref.document_number,
                collision_documents,
            )

        if not source_document_number:
            source_document_number = f"LEGACY-{stock.pk}"

        Stock.objects.filter(pk=stock.pk).update(
            source_document_number=source_document_number
        )

    changed = True
    while changed:
        changed = False
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
                destination_stock.source_document_number
                == f"LEGACY-{destination_stock.pk}"
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

            source_stock = _transfer_source_stock(Stock, transfer_out)
            if not source_stock or not source_stock.source_document_number:
                continue
            if source_stock.source_document_number in {
                "LEGACY",
                f"LEGACY-{source_stock.pk}",
            }:
                continue
            Stock.objects.filter(pk=destination_stock.pk).update(
                source_document_number=source_stock.source_document_number
            )
            changed = True

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
        .order_by(
            "reference_id",
            "item_id",
            "location_id",
            "batch_lot",
            "sumber_dana_id",
        )
        .annotate(quantity=Sum("quantity"))
    )
    for transfer_in in transfer_in_rows:
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

        source_stock = _transfer_source_stock(Stock, transfer_out)
        if not source_stock or not source_stock.source_document_number:
            continue
        if source_stock.source_document_number in {
            "LEGACY",
            f"LEGACY-{source_stock.pk}",
        }:
            continue

        destination_source_stock = (
            Stock.objects.filter(
                item_id=transfer_in["item_id"],
                location_id=transfer_in["location_id"],
                batch_lot=transfer_in["batch_lot"],
                sumber_dana_id=transfer_in["sumber_dana_id"],
                source_document_number=source_stock.source_document_number,
            )
            .order_by("pk")
            .first()
        )
        destination_stock = (
            Stock.objects.filter(
                item_id=transfer_in["item_id"],
                location_id=transfer_in["location_id"],
                batch_lot=transfer_in["batch_lot"],
                sumber_dana_id=transfer_in["sumber_dana_id"],
            )
            .exclude(source_document_number=source_stock.source_document_number)
            .order_by("pk")
            .first()
        )
        if not destination_stock:
            continue
        if destination_stock.source_document_number in {
            "LEGACY",
            f"LEGACY-{destination_stock.pk}",
        }:
            continue
        transfer_quantity = transfer_in["quantity"]
        if StockTransferItem.objects.filter(
            stock_id=destination_stock.pk,
            transfer__status="DRAFT",
        ).exists():
            continue
        if destination_stock.reserved:
            continue
        if destination_stock.quantity < transfer_quantity:
            continue

        reattributed_destination = False
        if (
            destination_stock.quantity == transfer_quantity
            and destination_stock.receiving_ref_id is None
        ):
            Stock.objects.filter(pk=destination_stock.pk).update(
                expiry_date=source_stock.expiry_date,
                unit_price=source_stock.unit_price,
                receiving_ref_id=source_stock.receiving_ref_id,
                source_document_number=source_stock.source_document_number,
            )
            reattributed_destination = True
        elif destination_source_stock:
            Stock.objects.filter(pk=destination_source_stock.pk).update(
                quantity=destination_source_stock.quantity + transfer_quantity
            )
        else:
            Stock.objects.create(
                item_id=transfer_in["item_id"],
                location_id=transfer_in["location_id"],
                batch_lot=transfer_in["batch_lot"],
                expiry_date=source_stock.expiry_date,
                quantity=transfer_quantity,
                reserved=0,
                unit_price=source_stock.unit_price,
                sumber_dana_id=transfer_in["sumber_dana_id"],
                receiving_ref_id=source_stock.receiving_ref_id,
                source_document_number=source_stock.source_document_number,
            )
        if not reattributed_destination:
            Stock.objects.filter(pk=destination_stock.pk).update(
                quantity=destination_stock.quantity - transfer_quantity
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
        migrations.RemoveConstraint(
            model_name="stock",
            name="uq_stock_batch",
        ),
        migrations.RunPython(
            backfill_source_document_number,
            migrations.RunPython.noop,
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
