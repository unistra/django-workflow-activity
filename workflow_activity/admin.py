# -*- coding: utf-8 -*-

"""
workflow_activity.admin
=======================

Enables the admin interface for the workflow_activity application. The
:py:class:~arc.workflow_activity.Activity can be managed from this interface
"""

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Action


class ActionAdmin(admin.ModelAdmin):
    list_display = ('content_object_display', 'actor_name', 'workflow',
        'transition', 'previous_state', 'process_date')
    list_display_links = ('content_object_display', )
    list_filter = ('workflow', 'previous_state')
    exclude = ('actor', )
    readonly_fields = ('content_type', 'object_id', 'actor_name', 'workflow',
        'transition', 'previous_state')

    def content_object_display(self, obj):
        return '{0.content_type} #{0.object_id}'.format(obj)
    content_object_display.short_description = _('Model instance')

    def actor_name(self, obj):
        return '{0.actor.last_name} {0.actor.first_name}'.format(obj)
    actor_name.short_description = _('Actor')

admin.site.register(Action, ActionAdmin)
