django-workflow-activity
========================
.. image:: https://travis-ci.org/unistra/django-workflow-activity.svg?branch=master
    :target: https://travis-ci.org/unistra/django-workflow-activity

.. image:: https://coveralls.io/repos/unistra/django-workflow-activity/badge.svg?branch=master
    :target: https://coveralls.io/r/unistra/django-workflow-activity?branch=master

Install
-------

Install the package via pypi: ::
    
    pip install django-workflow-activity

Add the installed application in the django settings file: ::

    INSTALLED_APPS = (
        ...
        'workflow_activity'
    )

Migrate the database: ::

    python manage.py migrate

Usage
-----

To create workflows and permissions, see the following documentations:

- https://pythonhosted.org/django-workflows
- https://pythonhosted.org/django-permissions

To use workflow activity methods on a class : ::

    from workflow_activity.models import WorkflowManagedInstance

    class MyClass(WorkflowManagedInstance):
        ...
        
To add a workflow to an object: ::

    myobj = MyClass()
    myobj.set_workflow('My workflow')

Now, you can use methods on your object like: ::

    myobj.last_state()
    myobj.last_transition()
    myobj.last_actor()
    myobj.last_action()
    myobj.allowed_transitions(request.user)
    myobj.is_editable_by(request.user, permission='edit')
    myobj.state()
    myobj.change_state(transition, request.user)
    ...

And managers like: ::

    MyClass.objects.filter()
    MyClass.pending.filter()
    MyClass.ended.filter()   
    ...

