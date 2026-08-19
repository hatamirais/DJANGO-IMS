from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("receiving", "0019_seed_system_receiving_types"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="receiving",
            name="cancelled_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cancelled_receivings",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="receiving",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="receiving",
            name="cancel_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="receiving",
            name="status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("SUBMITTED", "Diajukan"),
                    ("APPROVED", "Disetujui"),
                    ("PARTIAL", "Diterima Sebagian"),
                    ("RECEIVED", "Diterima Lengkap"),
                    ("CLOSED", "Ditutup"),
                    ("VERIFIED", "Terverifikasi"),
                    ("CANCELLED", "Dibatalkan"),
                ],
                default="DRAFT",
                max_length=20,
            ),
        ),
    ]
