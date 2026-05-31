from django.apps import AppConfig


class NmjappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nmjapp'
    
    def ready(self):
        from . import scheduler
        scheduler.start()