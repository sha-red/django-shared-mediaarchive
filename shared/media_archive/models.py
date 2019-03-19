import logging
import posixpath
import re

from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from imagefield.fields import ImageField, PPOIField
from imagekit.models import ImageSpecField
from imagekit.processors import Adjust, Thumbnail, ResizeToFit
from shared.utils.models.slugs import DowngradingSlugField, slugify

from .conf import UPLOAD_TO, USE_TRANSLATABLE_FIELDS

if USE_TRANSLATABLE_FIELDS:
    from content_plugins.fields import TranslatableCleansedRichTextField
    from shared.multilingual.utils.fields import TranslatableCharField
    from shared.multilingual.utils import i18n_fields
else:
    TranslatableCharField = models.CharField
    from content_plugins.fields import TranslatableCleansedRichTextField

    def i18n_fields(field_name, languages=None):
        return [field_name]


logger = logging.getLogger(__name__)


class MediaCategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("parent")


class MediaCategory(models.Model):
    name = models.CharField(_("name"), max_length=200)
    parent = models.ForeignKey(
        'self', blank=True, null=True,
        on_delete=models.CASCADE,
        related_name='children', limit_choices_to={'parent__isnull': True},
        verbose_name=_("Übergeordnet"))
    slug = models.SlugField(_('slug'), max_length=150)

    objects = MediaCategoryManager()

    class Meta:
        verbose_name = _("Working Folder")
        verbose_name_plural = _("Working Folders")
        ordering = ['parent__name', 'name']

    def __str__(self):
        if self.parent_id:
            return '%s - %s' % (self.parent.name, self.name)
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    save.alters_data = True

    def path_list(self):
        if self.parent is None:
            return [self]
        p = self.parent.path_list()
        p.append(self)
        return p

    def path(self):
        return ' - '.join((f.name for f in self.path_list()))


class Gallery(models.Model):
    internal_name = models.CharField(_("Internal Name"), max_length=500,
        help_text=_("Internal use only, not publicly visible."))
    name = TranslatableCharField(_("Name"), max_length=200, null=True, blank=True,
        help_text=_("Publicly visible name."))
    slug = models.SlugField(_("Slug"), null=True, blank=True)
    credits = TranslatableCharField(_("Credits"), null=True, blank=True, max_length=500)
    caption = TranslatableCleansedRichTextField(_("Caption"), null=True, blank=True)
    is_public = models.BooleanField(_("Active"), default=False)
    order_index = models.PositiveIntegerField(_("Order Index"), default=0)
    # background_color = models.ForeignKey('site_pages.Color', on_delete=models.PROTECT,
    #     null=True, blank=True,
    #     verbose_name=_("Background color"),
    #     help_text=_("The background color is used until the first image is loaded."))
    images = models.ManyToManyField('Image', blank=True,
        verbose_name=_("Images"),
        through='ImageGalleryRel')

    class Meta:
        verbose_name = _("Image Gallery")
        verbose_name_plural = _("Image Galleries")
        ordering = i18n_fields('name')

    def __str__(self):
        return self.internal_name or self.name or self.slug

    def public_images(self):
        return self.images.filter(is_public=True)


def filename_to_slug(instance, field):
    n, e = posixpath.splitext(instance.file.name)
    return slugify(n)


class FileTypeMixin(models.Model):
    type = models.CharField(_('file type'),
        max_length=12, editable=False, choices=())

    filetypes = []
    filetypes_dict = {}

    class Meta:
        abstract = True

    @classmethod
    def register_filetypes(cls, *types):
        cls.filetypes[0:0] = types
        choices = [t[0:2] for t in cls.filetypes]
        cls.filetypes_dict = dict(choices)
        cls._meta.get_field('type').choices[:] = choices

    def determine_file_type(self, name):
        for type_key, type_name, type_test in self.filetypes:
            if type_test(name):
                return type_key
        return self.filetypes[-1][0]

    def save(self, *args, **kwargs):
        self.type = self.determine_file_type(self.file.name)
        super().save(*args, **kwargs)
    save.alters_data = True


class DeleteOldFileMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.file:
            self._original_file_name = self.file.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # User uploaded a new file. Try to get rid of the old file in
        # storage, to avoid having orphaned files hanging around.
        if getattr(self, '_original_file_name', None):
            if self.file.name != self._original_file_name:
                self.delete_mediafile(self._original_file_name)

    def delete_mediafile(self, name=None):
        if name is None:
            name = self.file.name
        try:
            self.file.storage.delete(name)
        except Exception as e:
            logger.warn("Cannot delete media file %s: %s" % (name, e))


class MediaRole(models.Model):
    id_text = models.CharField(primary_key=True, max_length=20,
        help_text=_("Dieser Wert wird in der Programmierung benutzt und darf nicht verändert werden."))
    name = TranslatableCharField(_("name"), max_length=200)

    class Meta:
        verbose_name = _("Bild-Typ")
        verbose_name_plural = _("Bild-Typen")
        ordering = i18n_fields('name')

    def __str__(self):
        return self.name


class MediaBaseManager(models.Manager):
    def public_objects(self):
        return self.get_queryset().filter(is_public=True)


class MediaBase(DeleteOldFileMixin, models.Model):
    created = models.DateTimeField(_("Hochgeladen"), auto_now_add=True)
    modified = models.DateTimeField(_("Geändert"), auto_now=True)
    is_public = models.BooleanField(_("Veröffentlicht"), default=True,
        help_text=_("Nur als \"öffentlich sichtbar\" markierte Mediendaten werden öffentlich angezeigt."))

    # file = models.FileField(_("Datei"))
    file_size = models.IntegerField(_("file size"),
        blank=True, null=True, editable=False)
    slug = DowngradingSlugField(blank=True,
        populate_from=filename_to_slug, unique_slug=True)

    role = models.ForeignKey(MediaRole, on_delete=models.PROTECT,
        verbose_name=_("Typ"),
        null=True, blank=True)
    name = TranslatableCharField(_("Name"), max_length=200, null=True, blank=True)
    caption = TranslatableCleansedRichTextField(_("Bildunterschrift"), blank=True)
    credits = TranslatableCharField(_("Credits"), max_length=500, null=True, blank=True)
    copyright = TranslatableCharField(_('Rechteinhaber/in'), max_length=2000, blank=True)

    categories = models.ManyToManyField(MediaCategory,
        verbose_name=_("Arbeitsmappe"), blank=True)
    categories.category_filter = True

    objects = MediaBaseManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name or strip_tags(self.caption) or posixpath.basename(self.file.name)

    def save(self, *args, **kwargs):
        if self.file:
            try:
                self.file_size = self.file.size
            except (OSError, IOError, ValueError) as e:
                logger.error("Unable to read file size for %s: %s" % (self, e))
        super().save(*args, **kwargs)
    save.alters_data = True


class Image(MediaBase):
    image_width = models.PositiveIntegerField(
        _("image width"), blank=True, null=True, editable=False
    )
    image_height = models.PositiveIntegerField(
        _("image height"), blank=True, null=True, editable=False
    )
    image_ppoi = PPOIField(_("primary point of interest"))
    # file = models.ImageField(_("Datei"))
    file = ImageField(
        _("image"),
        upload_to=UPLOAD_TO,
        width_field="image_width",
        height_field="image_height",
        ppoi_field="image_ppoi",
        blank=True,
    )

    thumbnail = ImageSpecField(source='file',
        processors=[Adjust(contrast=1.2, sharpness=1.1),
                    Thumbnail(100, 50)],
        format='JPEG', options={'quality': 90})

    article_image = ImageSpecField(source='file',
        processors=[ResizeToFit(800, 800)],
        format='JPEG', options={'quality': 90})

    gallery_image = ImageSpecField(source='file',
        processors=[ResizeToFit(800, 800)],
        format='JPEG', options={'quality': 90})

    lightbox_image = ImageSpecField(source='file',
        processors=[ResizeToFit(1600, 1600)],
        format='JPEG', options={'quality': 90})
    highres_image = lightbox_image

    gallery_image_thumbnail = ImageSpecField(source='file',
        processors=[
            Adjust(contrast=1.2, sharpness=1.1),
            # ResizeToFit(180, 120)
            ResizeToFit(220, 155)
        ],
        format='JPEG', options={'quality': 90})

    type = 'image'

    class Meta:
        verbose_name = _("Bild")
        verbose_name_plural = _("Bilder")
        ordering = ['imagegalleryrel__position']

    #
    # Accessors to GIF images
    # FIXME ImageKit should leave alone GIF images in the first place
    # TODO Need more robust method to get image type

    def gif_gallery_image_thumbnail(self, image_spec_name='gallery_image_thumbnail'):
        # Return gif image URLs without converting.
        name, ext = posixpath.splitext(self.file.name)
        if ext == '.gif':
            return self.file
        else:
            return getattr(self, image_spec_name)

    def gif_lightbox_image(self):
        return self.gif_gallery_image_thumbnail(image_spec_name='lightbox_image')


class ImageGalleryRel(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    gallery = models.ForeignKey(Gallery, models.CASCADE)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Bild")
        verbose_name_plural = _("Bilder")
        ordering = ['position']


class Download(FileTypeMixin, MediaBase):
    file = models.FileField(_("Datei"),
        upload_to=UPLOAD_TO)

    class Meta:
        verbose_name = _("Download")
        verbose_name_plural = _("Downloads")
        ordering = i18n_fields('name')

    def get_display_name(self):
        return self.name or posixpath.basename(self.file.name)


Download.register_filetypes(
    # Should we be using imghdr.what instead of extension guessing?
    ('image', _('Image'), lambda f: re.compile(
        r'\.(bmp|jpe?g|jp2|jxr|gif|png|tiff?)$', re.IGNORECASE).search(f)),
    ('video', _('Video'), lambda f: re.compile(
        r'\.(mov|m[14]v|mp4|avi|mpe?g|qt|ogv|wmv|flv)$',
        re.IGNORECASE).search(f)),
    ('audio', _('Audio'), lambda f: re.compile(
        r'\.(au|mp3|m4a|wma|oga|ram|wav)$', re.IGNORECASE).search(f)),
    ('pdf', _('PDF document'), lambda f: f.lower().endswith('.pdf')),
    ('swf', _('Flash'), lambda f: f.lower().endswith('.swf')),
    ('txt', _('Text'), lambda f: f.lower().endswith('.txt')),
    ('rtf', _('Rich Text'), lambda f: f.lower().endswith('.rtf')),
    ('zip', _('Zip archive'), lambda f: f.lower().endswith('.zip')),
    ('doc', _('Microsoft Word'), lambda f: re.compile(
        r'\.docx?$', re.IGNORECASE).search(f)),
    ('xls', _('Microsoft Excel'), lambda f: re.compile(
        r'\.xlsx?$', re.IGNORECASE).search(f)),
    ('ppt', _('Microsoft PowerPoint'), lambda f: re.compile(
        r'\.pptx?$', re.IGNORECASE).search(f)),
    ('other', _('Binary'), lambda f: True),  # Must be last
)
