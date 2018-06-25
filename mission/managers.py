from django.db import models


class MissionQuerySet(models.QuerySet):
    def values_as_instances(self, *fields, **expressions):
        clone = self._clone()
        if expressions:
            clone = clone.annotate(**expressions)
        clone._fields = fields
        return clone


class CustomManger(models.Manager):
    def get_queryset(self):
        return MissionQuerySet(self.model, using=self._db)  # Important!


class MissionObjectManager(CustomManger):
    pass
