from django.db import models


class TaskDuplicates(models.Model):
    task_id = models.CharField(blank=True, null=False, max_length=200)
    query_string = models.CharField(blank=True, null=False, max_length=400)
