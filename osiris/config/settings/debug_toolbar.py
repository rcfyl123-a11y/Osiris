from .environment import DEBUG

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,  # Показывать только в DEBUG режиме
    "SHOW_COLLAPSED": True,  # Свернутая панель
}
