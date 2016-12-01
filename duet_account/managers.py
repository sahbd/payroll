from django.db import models
from model_utils.managers import PassThroughManager

from .models import SalarySheet

class SalarySheetQueryset(models.query.QuerySet):
    def with_amount(self):
        return self.annotate(total=Sum('salarySheetDetails_set__amount')


class SalarySheetManager(models.Manager):
    def get_queryset(self):
        return SalarySheetQueryset(self.model, using=self._db)

    def all(self):
        return self.get_queryset().with_amount()

