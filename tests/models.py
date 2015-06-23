from django.db import models
from workflow_activity.models import WorkflowManagedInstance


class FlatPage(WorkflowManagedInstance):

    url = models.CharField('URL', max_length=100, db_index=True)
    title = models.CharField('title', max_length=200)
    content = models.TextField('content', blank=True)

