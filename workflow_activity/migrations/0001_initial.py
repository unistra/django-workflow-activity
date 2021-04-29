# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('workflows', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('process_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='Date of creation')),
                ('object_id', models.PositiveIntegerField()),
                ('actor', models.ForeignKey(related_name='workflow_actions', verbose_name='Actor', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('previous_state', models.ForeignKey(related_name='+', verbose_name='Previous state', to='workflows.State', on_delete=models.CASCADE)),
                ('transition', models.ForeignKey(related_name='+', verbose_name='Transition', to='workflows.Transition', on_delete=models.CASCADE)),
                ('workflow', models.ForeignKey(related_name='+', verbose_name='Workflow', to='workflows.Workflow', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Action',
                'verbose_name_plural': 'Actions',
            },
            bases=(models.Model,),
        ),
    ]
