# Osiris Django Project

## Overview
Osiris is a Django project with a modular architecture that allows for automatic discovery and loading of applications located in the `apps` directory.

## Architecture
- **Main Project Directory**: `/workspace/osiris` - Contains the main project settings and configuration
- **Apps Directory**: `/workspace/osiris/apps` - Contains individual Django applications that are automatically discovered and registered
- **Configuration**: Uses a modular configuration approach with `config.py` and `settings.py`

## Features
- Automatic app discovery: New apps in the `apps` directory are automatically detected and added to `INSTALLED_APPS`
- Modular configuration: Base settings in `config.py`, extended in `settings.py`
- Dynamic URL routing: App-specific URLs are automatically included in the main URL configuration

## Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r osiris/requirements.txt
   ```

2. **Run Migrations**:
   ```bash
   cd osiris
   python manage.py migrate
   ```

3. **Run Development Server**:
   ```bash
   python manage.py runserver
   ```

## Adding New Apps

To add a new app:
1. Create a new directory under `/workspace/osiris/apps/`
2. Initialize it as a Django app with `apps.py` and `__init__.py` files
3. Optionally create a `urls.py` file for app-specific routes
4. The app will be automatically discovered and registered

## Configuration Files

- `osiris/config.py`: Base configuration settings shared across the project
- `osiris/settings.py`: Extended settings including app discovery logic
- `osiris/urls.py`: Main URL configuration with dynamic app URL inclusion
- `osiris/wsgi.py`: WSGI application configuration
- `osiris/manage.py`: Django management utility entry point

## Project Structure
```
/workspace/
├── osiris/                 # Main project directory
│   ├── __init__.py         # Makes project a Python package
│   ├── config.py           # Base configuration
│   ├── settings.py         # Extended settings with app discovery
│   ├── urls.py             # Main URL configuration
│   ├── wsgi.py             # WSGI application
│   ├── manage.py           # Management utility
│   ├── apps/              # Applications directory
│   │   ├── __init__.py    # Package marker
│   │   └── blog/          # Example app
│   │       ├── __init__.py
│   │       ├── apps.py
│   │       ├── views.py
│   │       └── urls.py
│   └── static/            # Static files directory
└── README.md              # This file
```

## Environment Variables
- `SECRET_KEY`: Django secret key (defaults to placeholder if not set)
- `DEBUG`: Enable/disable debug mode ('True' or 'False', defaults to 'False')
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (defaults to localhost,127.0.0.1)