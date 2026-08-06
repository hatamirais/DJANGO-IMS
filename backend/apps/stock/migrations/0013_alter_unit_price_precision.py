from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stock", "0012_validate_unit_price_precision"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stock",
            name="unit_price",
            field=models.DecimalField(decimal_places=10, default=0, max_digits=23),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="unit_price",
            field=models.DecimalField(
                blank=True, decimal_places=10, max_digits=23, null=True
            ),
        ),
        migrations.AlterField(
            model_name="openingbalanceimportitem",
            name="unit_price",
            field=models.DecimalField(decimal_places=10, default=0, max_digits=23),
        ),
    ]
