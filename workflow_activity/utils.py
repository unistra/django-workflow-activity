# -*- coding: utf-8 -*-

"""
workflow_activity.utils
=======================

Utility functions for the workflow_activity application that can be used in the
workflows application.
"""

from . import _ENDING_STATES


def get_ending_states(workflow):
    """ Searches for the ending states of a workflow

    :param workflow: a workflow
    :type workflow: `workflows.models.Workflow <http://packages.python.org/django-workflows/api.html#workflows.models.Workflow>`_
    :return: a list of states
    :rtype: list of `workflows.models.State <http://packages.python.org/django-workflows/api.html#workflows.models.State>`_
    """
    ending_states = []
    if workflow.name in _ENDING_STATES:
        ending_states = _ENDING_STATES[workflow.name]
    else:
        ending_states = workflow.states.filter(transitions__isnull=True)
        _ENDING_STATES[workflow.name] = ending_states
    return ending_states
