import os
import sys

import django
from django.conf import settings


def runtests():
    settings_file = 'django_influxdb.settings.test'
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)

    django.setup()

    from django.test.runner import DiscoverRunner
    runner_class = DiscoverRunner
    test_args = ['django_influxdb']

    failures = runner_class(
        verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
