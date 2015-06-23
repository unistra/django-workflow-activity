import sys
from django.conf import settings
from django.core.management import execute_from_command_line

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            },
        },
        INSTALLED_APPS=(
            'django.contrib.auth',                                                      
            'django.contrib.contenttypes',                                              
            'django.contrib.sessions',                                                  
            'django.contrib.sites',                                                     
            'django.contrib.messages',                                                  
            'django.contrib.staticfiles',                                               
            'django.contrib.flatpages',                                                 
            'workflows',
            'permissions',
            'workflow_activity',
        ),
        MIDDLEWARE_CLASSES = (
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
        ),
        ROOT_URLCONF=None,
        USE_TZ=True,
        SECRET_KEY='foobar',
        # SILENCED_SYSTEM_CHECKS=['1_7.W001'],
    )


def runtests():
    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    execute_from_command_line(argv)

if __name__ == '__main__':
    runtests()
