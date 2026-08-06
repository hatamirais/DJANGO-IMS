from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("distribution", "0012_validate_unit_price_precision"),
    ]

    operations = [
        migrations.AlterField(
            model_name="distributionitem",
            name="issued_unit_price",
            field=models.DecimalField(
                blank=True, decimal_places=10, max_digits=23, null=True
            ),
        ),
    ]
