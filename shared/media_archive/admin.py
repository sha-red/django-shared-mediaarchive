from django import VERSION as DJANGO_VERSION
from django.contrib import admin
from django.contrib.admin.filters import ChoicesFieldListFilter, FieldListFilter
from django.db.models import Count
from django.utils.encoding import smart_text
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _

from imagekit.admin import AdminThumbnail

from .conf import USE_TRANSLATABLE_FIELDS
from .forms import MediaCategoryAdminForm
from . import admin_actions, mixins, models

if USE_TRANSLATABLE_FIELDS:
    from shared.multilingual.utils import i18n_fields, lang_suffix
else:
    def i18n_fields(field_name, languages=None):
        return [field_name]

    def lang_suffix(language_code=None, fieldname=""):
        return fieldname


class CategoryFieldListFilter(ChoicesFieldListFilter):
    """
    Customization of ChoicesFilterSpec which sorts in the user-expected format.

        my_model_field.category_filter = True
    """

    template = "media_archive/admin/select_filter.html"

    def __init__(self, f, request, params, model, model_admin,
                 field_path=None):
        super(CategoryFieldListFilter, self).__init__(
            f, request, params, model, model_admin, field_path)

        # Restrict results to categories which are actually in use:
        if DJANGO_VERSION < (1, 8):
            related_model = f.related.parent_model
            related_name = f.related.var_name
        elif DJANGO_VERSION < (2, 0):
            related_model = f.rel.to
            related_name = f.related_query_name()
        else:
            related_model = f.remote_field.model
            related_name = f.related_query_name()

        self.lookup_choices = sorted(
            [
                (i.pk, '%s (%s)' % (i, i._related_count))
                for i in related_model.objects.annotate(
                    _related_count=Count(related_name)
                ).exclude(_related_count=0)
            ],
            key=lambda i: i[1],
        )

    def choices(self, cl):
        yield {
            'selected': self.lookup_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display': _('All')
        }

        for pk, title in self.lookup_choices:
            yield {
                'selected': pk == int(self.lookup_val or '0'),
                'query_string': cl.get_query_string({self.lookup_kwarg: pk}),
                'display': mark_safe(smart_text(title))
            }


FieldListFilter.register(
    lambda f: getattr(f, 'category_filter', False),
    CategoryFieldListFilter,
    take_priority=True)


@admin.register(models.MediaCategory)
class MediaCategoryAdmin(admin.ModelAdmin):
    form = MediaCategoryAdminForm
    list_display = ['path']
    list_filter = ['parent']
    list_per_page = 25
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    raw_id_fields = ['parent']


def image_thumbnail_image(obj):
    # TODO Return default placeholder image instead of None
    return obj.image.thumbnail


@admin.register(models.MediaRole)
class MediaRoleAdmin(admin.ModelAdmin):
    list_display = i18n_fields('name')


class MediaAdminBase(admin_actions.MediaBaseActionsMixin, mixins.DropUploadAdminMixin, admin.ModelAdmin):
    list_display = ['is_public', 'admin_thumbnail', 'get_name_display',
        'get_categories_display',
        'modified']  # , 'created']
    list_display_links = ('admin_thumbnail', 'get_name_display')
    # list_editable = ['is_public']
    list_per_page = 25
    list_filter = ['is_public', 'categories', 'role']
    search_fields = [
        *i18n_fields('name'),
        'slug',
        *i18n_fields('caption'),
        *i18n_fields('credits'),
        *i18n_fields('copyright'),
    ]
    date_hierarchy = 'modified'
    ordering = ['-modified']

    fieldsets = (
        (None, {
            'fields': [
                'is_public',
                'file',
                *i18n_fields('name'),
                'role',
            ]}),
        (_("Texte"), {
            'fields': [
                *i18n_fields('caption'),
                *i18n_fields('credits'),
                *i18n_fields('copyright'),
            ]}),
        (_("Ordnung"), {
            'fields': [
                'categories',
            ]}),
    )
    filter_horizontal = ['categories']

    admin_thumbnail = AdminThumbnail(
        image_field='thumbnail',
        template='imagekit/admin/selectable_thumbnail.html')
    admin_thumbnail.short_description = _("Foto")

    # TODO class Media: add switch_languages script

    def get_name_display(self, obj):
        return format_html(
            "<small>{categories}</small><br>{caption}",
            categories=", ".join([str(p) for p in obj.categories.all()]),
            caption=str(obj),
        )
    get_name_display.short_description = _("Name")
    get_name_display.admin_order_field = lang_suffix(fieldname='name')

    def get_categories_display(self, obj):
        return mark_safe("<br>".join([str(c) for c in obj.categories.all()]))
    get_categories_display.short_description = _("Arbeitsmappen")
    get_categories_display.admin_order_field = 'categories__name'


@admin.register(models.Image)
class ImageAdmin(MediaAdminBase):
    actions = [
        admin_actions.assign_category,
        'change_is_public_action',
        admin_actions.add_images_to_gallery,
    ]


@admin.register(models.Download)
class DownloadAdmin(MediaAdminBase):
    list_display = ['is_public', '__str__']
    list_display_links = ['__str__']
    actions = [
        admin_actions.assign_category,
        'change_is_public_action',
    ]


class ImageGalleryRelInline(admin.TabularInline):
    model = models.ImageGalleryRel
    fields = ['admin_thumbnail', 'image', 'position']
    readonly_fields = ['admin_thumbnail']
    raw_id_fields = ['image']
    extra = 0
    verbose_name = _("Bild")
    verbose_name_plural = _("Bilder")

    admin_thumbnail = AdminThumbnail(
        image_field=image_thumbnail_image,
        template='imagekit/admin/selectable_thumbnail.html')
    admin_thumbnail.short_description = _("Foto")


@admin.register(models.Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('is_public', 'name', 'get_image_count')
    list_display_links = ['name']
    list_filter = ['is_public']
    search_fields = [
        *i18n_fields('name'),
        'slug',
        *i18n_fields('caption'),
        *i18n_fields('credits'),
    ]

    fieldsets = (
        (None, {
            'fields': [
                'is_public',
                *i18n_fields('name'),
                'slug',
            ]}),
        (_("Texte"), {
            'fields': [
                *i18n_fields('caption'),
                *i18n_fields('credits'),
            ]}),
        (_("Weiteres"), {
            'classes': ['collapse'],
            'fields': [
                'order_index',
            ]}),
    )
    prepopulated_fields = {
        'slug': ['name'],
    }

    inlines = [ImageGalleryRelInline]

    def get_image_count(self, obj):
        return obj.images.count()
    get_image_count.short_description = _("Bilder")

