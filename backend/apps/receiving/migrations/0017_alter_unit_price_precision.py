from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("receiving", "0016_validate_unit_price_precision"),
    ]

    operations = [
        migrations.AlterField(
            model_name="receivingitem",
            name="unit_price",
            field=models.DecimalField(decimal_places=10, max_digits=23),
        ),
        migrations.AlterField(
            model_name="receivingorderitem",
            name="unit_price",
            field=models.DecimalField(decimal_places=10, default=0, max_digits=23),
        ),
    ]
