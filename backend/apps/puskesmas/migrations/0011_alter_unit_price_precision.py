from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("puskesmas", "0010_validate_unit_price_precision"),
    ]

    operations = [
        migrations.AlterField(
            model_name="puskesmasreceiptconfirmationitem",
            name="unit_price",
            field=models.DecimalField(
                decimal_places=10,
                help_text="Harga satuan aktual yang diterima Puskesmas",
                max_digits=23,
            ),
        ),
    ]
