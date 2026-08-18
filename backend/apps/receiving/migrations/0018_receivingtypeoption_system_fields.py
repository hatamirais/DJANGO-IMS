from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("receiving", "0017_alter_unit_price_precision"),
    ]

    operations = [
        migrations.AddField(
            model_name="receivingtypeoption",
            name="is_system",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="receivingtypeoption",
            name="requires_supplier",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="receivingtypeoption",
            name="sort_order",
            field=models.PositiveSmallIntegerField(default=100),
        ),
        migrations.AlterModelOptions(
            name="receivingtypeoption",
            options={"ordering": ["sort_order", "name"]},
        ),
    ]
