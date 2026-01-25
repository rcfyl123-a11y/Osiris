# Osiris Project

A modular Django-based application framework designed for scalable web applications.

## Structure

```
osiris/
├── __init__.py
├── config.py           # Main configuration settings
├── settings.py         # Django settings
├── urls.py             # Main URL routing
├── wsgi.py             # WSGI configuration
├── manage.py           # Management script
└── apps/               # Individual applications
    └── todo/           # Example todo application
        ├── __init__.py
        ├── apps.py
        ├── models.py
        ├── views.py
        ├── urls.py
        ├── migrations/
        └── templates/
```

## Features

- **Modular Architecture**: Applications are organized in the `apps/` directory
- **Dynamic App Discovery**: New apps are automatically detected and registered
- **Scalable Design**: Easy to add new functionality as separate apps

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Start the server: `python manage.py runserver`

## Adding New Apps

To add a new app to the Osiris framework:

1. Create your app in the `osiris/apps/` directory
2. Make sure it has the proper Django app structure
3. Register it in your app's `apps.py`
4. The main Osiris system will automatically detect and load it

## Running the Project

```bash
cd osiris
python manage.py runserver
```

The application will be accessible at http://127.0.0.1:8000/

## Current Apps

- **Todo**: A simple todo list application demonstrating the modular architecture