from django.apps import AppConfig
import threading

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        # Run in background thread to avoid initialization issues
        def delayed_start():
            import time
            time.sleep(5)  # Wait for everything to initialize
            from .signals import start_scheduler
            start_scheduler()
        
        if not threading.current_thread().daemon:
            threading.Thread(target=delayed_start, daemon=True).start()