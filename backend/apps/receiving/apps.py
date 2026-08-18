from django.apps import AppConfig, apps
from django.db import OperationalError, ProgrammingError
from django.db.models.signals import post_migrate


SYSTEM_RECEIVING_TYPES = [
    {
        "code": "PROCUREMENT",
        "name": "Pengadaan",
        "is_active": True,
        "is_system": True,
        "requires_supplier": True,
        "sort_order": 10,
    },
    {
        "code": "GRANT",
        "name": "Hibah",
        "is_active": True,
        "is_system": True,
        "requires_supplier": False,
        "sort_order": 20,
    },
]


def ensure_system_receiving_types(sender, using, **kwargs):
    ReceivingTypeOption = apps.get_model("receiving", "ReceivingTypeOption")
    try:
        for option in SYSTEM_RECEIVING_TYPES:
            receiving_type, created = (
                ReceivingTypeOption.objects.using(using).get_or_create(
                    code=option["code"],
                    defaults={
                        "name": option["name"],
                        "is_active": option["is_active"],
                        "is_system": option["is_system"],
                        "requires_supplier": option["requires_supplier"],
                        "sort_order": option["sort_order"],
                    },
                )
            )
            if not created and not receiving_type.is_system:
                receiving_type.is_system = True
                receiving_type.save(update_fields=["is_system"])
    except (OperationalError, ProgrammingError):
        return


class ReceivingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.receiving"
    verbose_name = "Receiving"

    def ready(self):
        post_migrate.connect(ensure_system_receiving_types, sender=self)
