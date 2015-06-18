# -*- coding: utf-8 -*-

"""
"""

from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from django.contrib.flatpages.models import FlatPage
from django.test import TestCase
import permissions
from workflows.tests import create_workflow
from workflows.utils import set_workflow
from workflows.models import State
from workflows.models import StatePermissionRelation
from workflows.models import Transition
from workflows.models import Workflow
from workflows.models import WorkflowPermissionRelation

from .models import Action
from .models import WorkflowManagedInstance
from .models import changed_state
from .utils import get_ending_states


# patch FlatPage to make work inheritance with WorkflowManagedInstance
del FlatPage.objects
FlatPage.__bases__ = (WorkflowManagedInstance, )
for manager in ('objects', 'ended', 'pending'):
    manager =  getattr(FlatPage, manager)
    manager.model = FlatPage
    manager._inherited = True
for field_name in ('state_relation', 'actions'):
    field = WorkflowManagedInstance._meta.get_field_by_name(field_name)[0]
    field.model = FlatPage
    FlatPage._meta.add_field(field)
FlatPage._meta.add_field(FlatPage.initializer.field)


class ActionTest(TestCase):

    def setUp(self):
        create_workflow(self)
        self.user = User.objects.create(username='test_user',
            first_name='Test', last_name='User')
        self.flat_page = FlatPage.objects.create(url='/page-1', title='Page 1',
                initializer=self.user)

    def test_unicode(self):
        """
        """
        action = Action.objects.create(actor=self.user, workflow=self.w,
            transition=self.make_public, previous_state=self.private,
            content_object=self.flat_page)
        self.assertEqual(action.__unicode__(),
            u'page statique #1 - Standard - Test User - Make public')


class WorkflowManagedInstanceTest(TestCase):
    """
    """

    def setUp(self):
        """
        """
        create_workflow(self)

        # roles
        self.anonymous = permissions.utils.register_role('Anonymous')
        self.publisher = permissions.utils.register_role('Publisher')


        self.anonymous_user = User.objects.create(username='anonymous_user')
        permissions.utils.add_role(self.anonymous_user, self.anonymous)
        self.test_user = User.objects.create(username='test_user',
            first_name='Test', last_name='User')
        permissions.utils.add_role(self.test_user, self.publisher)

        self.flat_page = FlatPage.objects.create(url='/page-1', title='Page 1',
                initializer=self.test_user)

        # permissions
        self.edit = permissions.utils.register_permission('Edit', 'edit')
        self.view = permissions.utils.register_permission('View', 'view')

        # state, transition
        self.rejected = State.objects.create(name='Rejected', workflow=self.w)
        self.reject = Transition.objects.create(name='Reject',
                workflow=self.w, destination=self.rejected,
                permission=self.edit)
        self.private.transitions.add(self.reject)

        # permissions for the workflow
        WorkflowPermissionRelation.objects.create(workflow=self.w,
                permission=self.edit)
        WorkflowPermissionRelation.objects.create(workflow=self.w,
                permission=self.view)

        # permissions for states
        StatePermissionRelation.objects.create(state=self.public,
                permission=self.view, role=self.publisher)
        StatePermissionRelation.objects.create(state=self.private,
                permission=self.edit, role=self.publisher)
        StatePermissionRelation.objects.create(state=self.private,
                permission=self.view, role=self.publisher)
        StatePermissionRelation.objects.create(state=self.rejected,
                permission=self.view, role=self.publisher)

        # permissions on transition
        self.make_public.permission = self.edit
        self.make_public.save()
        self.make_private.permission = self.edit
        self.make_private.save()

        set_workflow(self.flat_page, self.w)

    def tearDown(self):
        """
        """
        self.flat_page.delete()
    
    def test_manage_state(self):
        """
        """
        # testing initial state
        self.assertEqual(self.flat_page.state, self.private)
        # testing changing state
        self.flat_page.change_state(self.make_public, self.test_user)
        self.assertEqual(self.flat_page.state, self.public)

    def test_editable(self):
        """
        """
        # check if content object is editable and editable by different users
        # at initial state
        self.assertTrue(self.flat_page.is_editable)
        self.assertTrue(self.flat_page.is_editable_by(self.test_user))
        self.assertFalse(self.flat_page.is_editable_by(self.anonymous_user))

        # check if content object is editable and editable by different users
        # when changing state
        self.flat_page.change_state(self.make_public, self.test_user)
        self.assertTrue(self.flat_page.is_editable)
        self.assertFalse(self.flat_page.is_editable_by(self.test_user))
        self.assertFalse(self.flat_page.is_editable_by(self.anonymous_user))

        # changing state to an ending state
        self.flat_page.change_state(self.reject, self.test_user)
        self.assertFalse(self.flat_page.is_editable)

    def test_allowed_transitions(self):
        """
        """

        result = self.flat_page.allowed_transitions(self.anonymous_user)
        self.assertListEqual(result, [])
        result = self.flat_page.allowed_transitions(self.test_user)
        self.assertEqual(len(result), 2)

        self.flat_page.change_state(self.make_public, self.test_user)
        result = self.flat_page.allowed_transitions(self.anonymous_user)
        self.assertListEqual(result, [])
        result = self.flat_page.allowed_transitions(self.test_user)
        self.assertEqual(result, [])
        
    def test_allowed_transition(self):
        """
        """
        result = self.flat_page.allowed_transition(self.make_private.id,
                self.test_user)
        self.assertIsNone(result)
        result = self.flat_page.allowed_transition(self.make_public.id,
                self.test_user)
        self.assertEqual(result, self.make_public)

        self.flat_page.change_state(self.make_public, self.test_user)
        result = self.flat_page.allowed_transition(self.make_private.id,
                self.test_user)
        self.assertIsNone(result)

    def test_create_actions(self):
        """
        """
        self.flat_page.change_state(self.make_public, self.test_user)

        actions = self.flat_page.actions.all()
        self.assertEqual(actions.count(), 1)

        self.flat_page.change_state(self.make_private, self.test_user)
        self.assertEqual(actions.count(), 2)

        action = actions[1]
        self.assertEqual(action.previous_state, self.public)
        self.assertEqual(action.transition, self.make_private)
        self.assertEqual(action.actor, self.test_user)
        self.assertEqual(action.workflow, self.w)
        self.assertIsInstance(action.content_object, FlatPage)

    def test_last_action(self):
        """
        """
        new_action = Action.objects.create(actor=self.test_user,
                transition=self.make_public, previous_state=self.private,
                workflow=self.w, content_object=self.flat_page)

        self.assertEqual(self.flat_page.last_action(), new_action)

    def test_no_action(self):
        """
        """
        self.assertRaises(Action.DoesNotExist, self.flat_page.last_action)
        self.assertIsNone(self.flat_page.last_transition())
        self.assertIsNone(self.flat_page.last_actor())
        self.assertIsNone(self.flat_page.last_state())

    def test_last_transition(self):
        """
        """
        Action.objects.create(actor=self.test_user,
                transition=self.make_public, previous_state=self.private,
                workflow=self.w, content_object=self.flat_page)
        self.assertEqual(self.flat_page.last_transition(), self.make_public)

    def test_last_actor(self):
        """
        """
        Action.objects.create(actor=self.test_user,
                transition=self.make_public, previous_state=self.private,
                workflow=self.w, content_object=self.flat_page)
        self.assertEqual(self.flat_page.last_actor(), self.test_user)


    def test_last_state(self):
        """
        """
        Action.objects.create(actor=self.test_user,
                transition=self.make_public, previous_state=self.private,
                workflow=self.w, content_object=self.flat_page)
        self.assertEqual(self.flat_page.last_state(), self.private)

    def test_get_editable_instances(self):
        """
        """
        second_page = FlatPage.objects.create(url='/page-2', title='Page 2',
                initializer=self.test_user)
        third_page = FlatPage.objects.create(url='/page-3', title='Page 3',
                initializer=self.test_user)
        fourth_page = FlatPage.objects.create(url='/page-4', title='Page 4',
                initializer=self.test_user)
        fifth_page = FlatPage.objects.create(url='/page-5', title='Page 5',
            initializer=self.test_user)

        set_workflow(self.flat_page, self.w)
        set_workflow(second_page, self.w)
        set_workflow(third_page, self.w)

        result = FlatPage.pending.editable_by_roles([self.publisher])
        self.assertListEqual(list(result), [self.flat_page, second_page, 
            third_page])
        result = FlatPage.pending.editable_by_roles([self.anonymous])
        self.assertListEqual(list(result), [])

        self.flat_page.change_state(self.make_public, self.test_user)
        second_page.change_state(self.reject, self.test_user)

        result = FlatPage.pending.editable_by_roles([self.publisher])
        self.assertListEqual(list(result), [third_page])
        

class WorkflowInstanceManager(TestCase):
    """
    """

    def setUp(self):
        create_workflow(self)
        self.user = User.objects.create(username='test_user',
            first_name='Test', last_name='User')
        self.first_page = FlatPage.objects.create(url='/page-1',
                title='Page 1', initializer=self.user)
        self.second_page = FlatPage.objects.create(url='/page-2',
                title='Page 2', initializer=self.user)
        self.third_page = FlatPage.objects.create(url='/page-3',
                title='Page 3', initializer=self.user)
        self.fourth_page = FlatPage.objects.create(url='/page-4',
                title='Page 4', initializer=self.user)
        self.fifth_page = FlatPage.objects.create(url='/page-5',
                title='Page 5', initializer=self.user)
        
        # new transition and state
        self.rejected = State.objects.create(name='Rejected', workflow=self.w)
        self.reject = Transition.objects.create(name='Reject',
                workflow=self.w, destination=self.rejected)
        self.private.transitions.add(self.reject)

    def tearDown(self):
        self.first_page.delete()
        self.second_page.delete()
        self.third_page.delete()
        self.fourth_page.delete()
        self.fifth_page.delete()

    def test_by_state(self):
        set_workflow(self.first_page, self.w)
        set_workflow(self.second_page, self.w)
        set_workflow(self.third_page, self.w)

        result = FlatPage.objects.by_state('Private')
        self.assertListEqual(list(result), [self.first_page, self.second_page,
            self.third_page])
        self.assertIsInstance(result, QuerySet)

        self.first_page.change_state(self.make_public, self.user)

        result = FlatPage.objects.by_state('Public')
        self.assertListEqual(list(result), [self.first_page])


    def test_pending_manager(self):
        set_workflow(self.first_page, self.w)
        set_workflow(self.second_page, self.w)
        set_workflow(self.third_page, self.w)

        result = FlatPage.pending.all()
        self.assertListEqual(list(result), [self.first_page, self.second_page,
            self.third_page])

        self.first_page.change_state(self.make_public, self.user)
        self.second_page.change_state(self.reject, self.user)
        result = FlatPage.pending.all()
        self.assertListEqual(list(result), [self.first_page, self.third_page])

        result = result.by_state('Private')
        self.assertListEqual(list(result), [self.third_page])

    def test_ended_manager(self):
        set_workflow(self.first_page, self.w)
        set_workflow(self.second_page, self.w)
        set_workflow(self.third_page, self.w)

        result = FlatPage.ended.all()
        self.assertListEqual(list(result), [])

        self.first_page.change_state(self.make_public, self.user)
        self.second_page.change_state(self.reject, self.user)
        result = FlatPage.ended.all()
        self.assertListEqual(list(result), [self.second_page])

        result = result.by_state('Rejected')
        self.assertListEqual(list(result), [self.second_page])


class EndingStatesTest(TestCase):
    """
    """

    def test_get_ending_states(self):
        """
        """

        # no defined state for workflow
        self.w = Workflow.objects.create(name='Standard')
        self.assertListEqual(list(get_ending_states(self.w)), [])

        self.private = State.objects.create(name='Private', workflow=self.w)
        self.public = State.objects.create(name='Public', workflow=self.w)

        # two states with no transition -> ending states
        self.assertListEqual(list(get_ending_states(self.w)), [self.private,
            self.public])

        self.make_public = Transition.objects.create(name='Make public',
                workflow=self.w, destination=self.public)
        self.private.transitions.add(self.make_public)
        
        # branching a transition on a state
        self.assertListEqual(list(get_ending_states(self.w)), [self.public])

        self.make_private = Transition.objects.create(name='Make private',
                workflow=self.w, destination=self.private)
        self.public.transitions.add(self.make_private)

        # cycle transitions -> no ending states
        self.assertListEqual(list(get_ending_states(self.w)), [])


class StateChangedSignalsTest(TestCase):
    """
    """

    def setUp(self):
        """
        """
        create_workflow(self)
        self.user = User.objects.create(username='test_user',
            first_name='Test', last_name='User')
        self.flat_page = FlatPage.objects.create(url='/page-1', title='Page 1',
            initializer=self.user)

        set_workflow(self.flat_page, self.w)

    def _receive_signal(self, sender, **kwargs):
        self.sender = sender
        self.signal_args = kwargs

    def test_changing_state(self):
        """
        """
        # connecting to the signal with a receiver function
        changed_state.connect(self._receive_signal, sender=self.flat_page)

        # changing state - signal sent
        self.flat_page.change_state(self.make_public, self.user)
        
        self.assertEqual(self.sender.__class__.__base__,
                WorkflowManagedInstance)
        self.assertEqual(self.signal_args['previous_state'], self.private)
        self.assertEqual(self.signal_args['actor'], self.user)
        self.assertEqual(self.signal_args['transition'], self.make_public)
