from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("procurement", "0002_validate_unit_price_precision"),
    ]

    operations = [
        migrations.AlterField(
            model_name="procurementcontractline",
            name="original_unit_price",
            field=models.DecimalField(decimal_places=10, max_digits=23),
        ),
        migrations.AlterField(
            model_name="procurementamendmentline",
            name="revised_unit_price",
            field=models.DecimalField(decimal_places=10, max_digits=23),
        ),
    ]
