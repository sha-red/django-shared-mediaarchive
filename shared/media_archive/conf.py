from django.conf import settings

USE_TRANSLATABLE_FIELDS = (
    getattr(settings, 'CONTENT_PLUGINS_USE_TRANSLATABLE_FIELDS', False) or
    getattr(settings, 'USE_TRANSLATABLE_FIELDS', False)
)


UPLOAD_TO = getattr(settings, 'MEDIARCHIVE_UPLOAD_TO', 'archive')
