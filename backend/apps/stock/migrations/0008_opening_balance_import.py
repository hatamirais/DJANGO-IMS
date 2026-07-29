from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("items", "0010_item_barcode"),
        ("stock", "0007_backfill_no_expiry_sentinel"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpeningBalanceImport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("document_number", models.CharField(max_length=100, unique=True)),
                ("effective_date", models.DateField()),
                ("posted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("notes", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_opening_balance_imports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "opening_balance_imports",
                "ordering": ["-effective_date", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OpeningBalanceImportItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("batch_lot", models.CharField(max_length=100)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                (
                    "quantity",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "unit_price",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="opening_balance_import_items",
                        to="items.item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="opening_balance_import_items",
                        to="items.location",
                    ),
                ),
                (
                    "opening_balance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="stock.openingbalanceimport",
                    ),
                ),
                (
                    "sumber_dana",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="opening_balance_import_items",
                        to="items.fundingsource",
                    ),
                ),
            ],
            options={
                "db_table": "opening_balance_import_items",
                "ordering": ["item", "expiry_date", "batch_lot"],
            },
        ),
        migrations.AddIndex(
            model_name="openingbalanceimport",
            index=models.Index(
                fields=["effective_date"], name="idx_opening_balance_date"
            ),
        ),
        migrations.AddIndex(
            model_name="openingbalanceimportitem",
            index=models.Index(
                fields=["item", "location", "batch_lot"],
                name="idx_opening_balance_item_batch",
            ),
        ),
    ]
