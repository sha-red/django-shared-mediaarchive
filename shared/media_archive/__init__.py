try:
    from ._version import __version__
except ImportError:
    __version__ = '0.1'

VERSION = __version__.split('+')
VERSION = tuple(list(map(int, VERSION[0].split('.'))) + VERSION[1:])


default_app_config = 'shared.media_archive.apps.MediaArchiveConfig'
