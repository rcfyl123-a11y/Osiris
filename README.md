# Osiris Framework

This is the main repository for the Osiris application framework.

## Structure

The main application code is located in the `osiris/` directory:

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
```

## Getting Started

To run the Osiris application:

1. Navigate to the osiris directory: `cd osiris`
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Start the development server: `python manage.py runserver`

## Applications

All modular applications are stored in the `osiris/apps/` directory. Each application follows Django's standard app structure and is automatically discovered and loaded by the framework.

Current applications:
- `todo` - A sample todo list application
