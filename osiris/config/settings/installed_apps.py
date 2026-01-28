from .environment import ENABLE_DEBUG_TOOLBAR


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "osiris.apps.accounts.apps.AccountsConfig",
    "osiris.apps.blog.apps.BlogConfig",
    "osiris.apps.rca.apps.RcaConfig",

    # ibm-db2 service
    # "apps.ibmdb.apps.IBMDBConfig",
]

if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
