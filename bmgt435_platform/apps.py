from django.apps import AppConfig
import multiprocessing


class BmgtPlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bmgt435_platform'
    verbose_name = "BMGT435 Experiential Learning Platform"
    app_process_pool = multiprocessing.Pool(processes=4)
