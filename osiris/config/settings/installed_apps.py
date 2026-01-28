INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # DEBUG_TOOLS
    "debug_toolbar",

    "apps.core.apps.CoreConfig",
    "apps.rca.apps.RCAConfig",

    # ibm-db2 service
    # "apps.ibmdb.apps.IBMDBConfig",
]
