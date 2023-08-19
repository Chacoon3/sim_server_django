from django.apps import AppConfig
from django.core.files.storage import FileSystemStorage


class BmgtPlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bmgt435_platform'
    verbose_name = "BMGT435 Experiential Learning Platform"
    
    
    
bmgt435_file_sys = FileSystemStorage()
