from django.db import models


class ReportPermission(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("view_reports", "Can view reports"),)
