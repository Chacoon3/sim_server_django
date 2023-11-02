from django.apps import AppConfig
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class BmgtPlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bmgt435_elp'
    verbose_name = "BMGT435 Experiential Learning Platform"
    
    
    
bmgt435_file_system = FileSystemStorage(location=settings.STATIC_ROOT + "bmgt435/", base_url=settings.STATIC_URL + "bmgt435/")
print("location", bmgt435_file_system.location)
print("base location", bmgt435_file_system.base_location)
print("base url", bmgt435_file_system.base_url)
