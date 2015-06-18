# -*- coding: utf-8 -*-

"""
workflow_activity.managers
==========================

The module defines 2 managers that inherits BaseManager. They are already
plugged into the WorkflowManagedInstance model and are also available in each
model that inherits the WorkflowManagedInstance model.
"""

from django.db.models.query import QuerySet
from model_utils.managers import PassThroughManager



class WorkflowManagedInstanceBaseQuerySet(QuerySet):
    """ Base for all managers of workflow managed instances.
    """

    def by_state(self, state_name):
        """ Search workflow managed instances by state

        :param state_name: the name of the state
        :type state_name: a string
        """
        return self.filter(state_relation__state__name=state_name)


class PendingManager(PassThroughManager):
    """ Manager that filters the instances that are currently managed by a
    workflow
    """

    def get_query_set(self):
        """ Only the instances that are in non ending states 
        """
        return super(PendingManager, self).get_query_set()\
            .filter(state_relation__state__isnull=False)\
            .exclude(state_relation__state__transitions__isnull=True)

    def editable_by_roles(self, roles, edit='edit'):
        """ Only the instances that are editable by some roles (based on
        permissions for this role)

        :param roles: a list of roles
        :type roles: list of `permissions.models.Role
        <http://pythonhosted.org/django-permissions/api.html#models>`_
        :param edit: the codename of the permission to match
        :type edit: a string
        """
        return self.filter(
            state_relation__state__statepermissionrelation__role__in=roles,
            state_relation__state__statepermissionrelation__permission__codename=edit
        )


class EndedManager(PassThroughManager):
    """ Manager that filters the instances that are currently in a ended state
    of a workflow
    """

    def get_query_set(self):
        """ Only the instances that are in ending states 
        """
        return super(EndedManager, self).get_query_set()\
            .filter(state_relation__state__transitions__isnull=True)
