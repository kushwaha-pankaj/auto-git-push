from django.apps import AppConfig


class FrontendhomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "frontendhome"
    
    def ready(self):
        import frontendhome.signals  # Make sure this path matches your structure
