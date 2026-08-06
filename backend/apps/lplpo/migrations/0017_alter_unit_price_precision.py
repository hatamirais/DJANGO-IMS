from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lplpo", "0016_validate_unit_price_precision"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lplpoitem",
            name="harga_satuan",
            field=models.DecimalField(
                decimal_places=10,
                default=0,
                help_text=(
                    "January may be suggested from same-month confirmed receipt "
                    "confirmations; later periods use same-month weighted-average receipt "
                    "prices or carry forward the previous month's price"
                ),
                max_digits=23,
            ),
        ),
    ]
