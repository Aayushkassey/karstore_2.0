from django.apps import AppConfig


class RetentionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'retention'

    def ready(self):
        from retention.scheduler import start_scheduler
        start_scheduler()