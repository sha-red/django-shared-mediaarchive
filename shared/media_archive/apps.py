from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MediaArchiveConfig(AppConfig):
    name = 'shared.media_archive'
    verbose_name = _("Digital Media File Archive")
