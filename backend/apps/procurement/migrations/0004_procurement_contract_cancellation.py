from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("procurement", "0003_alter_unit_price_precision"),
    ]

    operations = [
        migrations.AddField(
            model_name="procurementcontract",
            name="cancel_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="procurementcontract",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="procurementcontract",
            name="cancelled_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cancelled_procurement_contracts",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="procurementcontract",
            name="status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("SUBMITTED", "Diajukan"),
                    ("APPROVED", "Disetujui"),
                    ("CLOSED", "Ditutup"),
                    ("CANCELLED", "Dibatalkan"),
                ],
                default="DRAFT",
                max_length=20,
            ),
        ),
    ]
