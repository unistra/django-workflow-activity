# -*- coding: utf-8 -*-

"""
workflow_activity.models
========================

The models defined here add an history logger to all models that are processed
within a workflow. ::

* :py:class:`~arc.workflow_activity.Action' is the main model that stores
data on each action made by a user through an application interface

"""

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.dispatch import receiver
from django.dispatch import Signal
from django.db.models.signals import m2m_changed
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from model_utils.managers import PassThroughManager
from permissions.utils import has_permission
import workflows.models
from workflows.utils import get_allowed_transitions
from workflows.utils import get_state
from workflows.utils import set_state

from . import managers
from .utils import get_ending_states


# signals to send when the state of a workflow managed instance is changed
changed_state = Signal(providing_args=['transition', 'actor',
    'previous_state'])


class Action(models.Model):
    """ This model is an history logger for actions made on a managed worklow
    instance. The following informations were made available : ::
        
    .. py:attribute:: actor

        The last actor for the processed workflow on the instance

    .. py:attribute:: process_date

        The date the action were performed by the actor

    .. py:attribute:: transition

        The transition that where called by the actor

    .. py:attribute:: previous_state

        The previous state of the managed instance, before the transition
        were called by the actor

    .. py:attribute:: workflow

        The workflow that were processed when transition were called by
        the actor

    .. py:attribute:: content_type

        The real model of the workflow managed instance

    .. py:attribute:: object_id

        The identifier of the workflow managed instance

    .. py:attribute:: content_object

        The generic foreign key between the workflow managed instance and
        the activity

    .. py:attribute:: creation_date

        Creation datetime of the action

    """

    actor = models.ForeignKey('auth.User', verbose_name=_('Actor'),
            related_name='workflow_actions', null=True)
    process_date = models.DateTimeField(verbose_name=_('Creation date'),
            auto_now_add=True)
    transition = models.ForeignKey('workflows.Transition',
            verbose_name=_('Transition'), related_name='+')
    previous_state = models.ForeignKey('workflows.State',
            verbose_name=_('Previous state'), related_name='+')
    workflow = models.ForeignKey('workflows.Workflow',
            verbose_name=_('Workflow'), related_name='+')
    creation_date = models.DateTimeField(verbose_name=_('Date of creation'),
            auto_now_add=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')


    class Meta:
        verbose_name = _('Action')
        verbose_name_plural = _('Actions')


    def __unicode__(self):
        return u'{0.content_type} #{0.object_id} - {0.workflow} - ' \
            '{0.actor.first_name} {0.actor.last_name} - {0.transition}'\
            .format(self)


class WorkflowManagedInstance(models.Model):
    """ Abstract model that must be inherited by models you want to manage an
    history with actions, change and get states easily on instance, get edit
    property and permission and get allowed transitions for users. ::

    .. py:attribute:: actions

        actions on instance as a Django generic relation

    .. py:attribute:: state_relation

        relation to states on instance as a Django generic relation

    .. py:attribute:: initializer

        user who initiates the workflow on instance (can be null)

    .. py:attribute:: creation_date
        
        date of creation of the managed instance
    """

    actions = generic.GenericRelation(Action, 
            content_type_field='content_type',
            object_id_field='object_id')
    state_relation = generic.GenericRelation('workflows.StateObjectRelation',
            object_id_field='content_id')
    initializer = models.ForeignKey('auth.User', verbose_name=_('Initializer'),
        related_name='initiated_%(class)ss'.lower(), null=True)
    creation_date = models.DateTimeField(verbose_name=_('Date of creation'),
            auto_now_add=True)


    class Meta:
        abstract = True


    objects = PassThroughManager(managers.WorkflowManagedInstanceBaseQuerySet)
    pending = managers.PendingManager(
            managers.WorkflowManagedInstanceBaseQuerySet)
    ended = managers.EndedManager(managers.WorkflowManagedInstanceBaseQuerySet)


    @property
    def state(self):
        """ Get the state in workflow for the instance of the workflow managed
        model

        :return: the state of the managed instance
        :rtype: `workflows.models.State <http://packages.python.org/django-workflows/api.html#workflows.models.State>`_
        """
        return get_state(self)

    def change_state(self, transition, actor):
        """ Set new state for the instance of the workflow managed model

        :param transition: a transition object
        :type transition: `workflows.models.Transition <http://packages.python.org/django-workflows/api.html#workflows.models.Transition>`_
        :param actor: a user object
        :type actor: `django.contrib.auth.User <https://docs.djangoproject.com/en/1.4/topics/auth/#users>`_

        This method send a signal to the application to notify a managed
        instance is changing state. The signal provides several arguments as
        the previous state, the executed transition and the actor.
        """
        actual_state = self.state
        set_state(self, transition.destination)
        changed_state.send_robust(sender=self, transition=transition,
                actor=actor, previous_state=actual_state)

    @property
    def is_editable(self):
        """ Is this managed instance editable in fact of the state
        """
        state = self.state
        return state is not None and \
                state not in get_ending_states(state.workflow)

    def is_editable_by(self, user, permission='edit'):
        """ Is this managed instance editable by user in fact of state and his
        role permission

        :param user: a user object
        :type user: `django.contrib.auth.User <https://docs.djangoproject.com/en/1.4/topics/auth/#users>`_
        :param permission: the permisson to match
        :type permission: a string
        """
        return self.is_editable and has_permission(self, user, permission)

    def allowed_transitions(self, user):
        """ Allowed transitions user can do on the managed instance

        :param user: a user object
        :type user: `django.contrib.auth.User <https://docs.djangoproject.com/en/1.4/topics/auth/#users>`_
        :return: allowed transitions
        :rtype: a list of `workflows.models.Transition <http://packages.python.org/django-workflows/api.html#workflows.models.Transition>`_
        """
        return get_allowed_transitions(self, user)

    def allowed_transition(self, transition_id, user):
        """ Allowed transition on managed instance based on a transition id
        check for the user trying to execute it

        :param transition_id: the transition_id the user wants to execute
        :type transition_id: an integer
        :param user: a user object
        :type user: `django.contrib.auth.User <https://docs.djangoproject.com/en/1.4/topics/auth/#users>`_
        :return: the transition if allowed
        :rtype: `workflows.models.Transition <http://packages.python.org/django-workflows/api.html#workflows.models.Transition>`_
        """
        for transition in self.allowed_transitions(user):
            if transition.id == transition_id:
                return transition
        return None

    def last_action(self):
        """ Last action on managed instance

        :return: the latest action on managed instance
        :rtype: :py:class:`arc.workflow_activity.Action`
        """
        return self.actions.latest('process_date')

    def last_actor(self):
        """ Last actor on managed instance

        :return: a user object
        :rtype: `django.contrib.auth.User <https://docs.djangoproject.com/en/1.4/topics/auth/#users>`_
        """
        try:
            return self.last_action().actor
        except Action.DoesNotExist:
            return None

    def last_transition(self):
        """ Last transition executed on managed instance

        :return: the transition
        :rtype: `workflows.models.Transition <http://packages.python.org/django-workflows/api.html#workflows.models.Transition>`_
        """
        try:
            return self.last_action().transition
        except Action.DoesNotExist:
            return None

    def last_state(self):
        """ Previous state of the managed instance

        :return: the previous state on the managed instance
        :rtype: `workflows.models.State <http://packages.python.org/django-workflows/api.html#workflows.models.State>`_
        """
        try:
            return self.last_action().previous_state
        except Action.DoesNotExist:
            return None


@receiver(m2m_changed, sender=workflows.models.State.transitions.through)
@receiver(post_save, sender=workflows.models.State)
def update_ending_states(sender, **kwargs):
    """ When new states are created or new transitions are added to states, the
    ENDING_STATES static variable must be updated

    :param sender: the model that send the signal
    """
    # signal send when a state is saved
    is_new_state = sender == workflows.models.State and kwargs['created']
    # signal send when transitions are added to a state
    transition_added = sender == workflows.models.State.transitions.through \
        and kwargs['action'] == 'post_add'

    if is_new_state or transition_added:
        from . import _ENDING_STATES
        workflow = kwargs['instance'].workflow
        # update the value for the right workflow in the static variable
        if workflow.name in _ENDING_STATES:
            del _ENDING_STATES[workflow.name]
            _ENDING_STATES[workflow.name] = get_ending_states(workflow)


@receiver(changed_state)
def create_action(sender, **kwargs):
    """ When a workflow managed instance is changing state, this function
    receive the signal and create a new action for the instance. Only model
    that inherits WorkflowManagedInstance will be matched to create actions

    :param sender: the instance that send the signal
    """
    managed_instance = sender
    if managed_instance.__class__.__base__ == WorkflowManagedInstance:
        managed_instance.actions.create(transition=kwargs['transition'],
            actor=kwargs['actor'], previous_state=kwargs['previous_state'],
            workflow=kwargs['previous_state'].workflow)
