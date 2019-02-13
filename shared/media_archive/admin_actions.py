from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.translation import ngettext, gettext_lazy as _
from django.shortcuts import render

from shared.utils.admin_actions import AdminActionBase, TargetActionBase
from . import models


class AddImagesToGalleryAction(TargetActionBase):
    target_model = models.Gallery
    related_field_name = 'gallery_set'

    __name__ = title = _("Add images to gallery")
    queryset_action_label = _("The selected images will be added to the following gallery:")
    action_button_label = _("Add Images")

    def apply(self, queryset, form):
        gallery = self.get_target(form)
        count = 0
        for image in queryset:
            _, created = \
                models.ImageGalleryRel.objects.get_or_create(
                    image=image,
                    gallery=gallery)
            if created:
                count += 1
        return count


add_images_to_gallery = AddImagesToGalleryAction('add_images_to_gallery')


class AssignCategoryAction(TargetActionBase):
    target_model = models.MediaCategory
    related_field_name = 'categories'

    __name__ = title = _("Assign category to images")
    short_description = title
    queryset_action_label = _("Images which will be assigned to the chosen category:")
    action_button_label = _("Add Images")

    def apply(self, queryset, form):
        category = self.get_target(form)
        count = 0
        for mediafile in queryset:
            getattr(mediafile, self.related_field_name).add(category)
            count += 1
        return count


assign_category = AssignCategoryAction('assign_category')


class MediaBaseActionsMixin:
    def change_is_public_action(self, request, queryset):
        modeladmin = self
        options_template_name = 'media_archive/admin/action_forms/change_is_public.html'

        class AccessAllowedForm(forms.Form):
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            # is_public = forms.BooleanField(label=_("Öffentlich sichtbar"))
            is_public = forms.TypedChoiceField(
                coerce=lambda x: x == 'True',
                choices=((False, _("Nicht veröffentlicht")), (True, _("Veröffentlicht"))),
                widget=forms.RadioSelect
            )

        form = None
        if 'apply' in request.POST:
            form = AccessAllowedForm(request.POST)
            if form.is_valid():
                chosen_is_public = form.cleaned_data['is_public']
                count = queryset.update(is_public=chosen_is_public)
                message = ngettext(
                    'Successfully set %(count)d media file to %(chosen_is_public)s.',
                    'Successfully set %(count)d media files to %(chosen_is_public)s.',
                    count) % {'count': count, 'chosen_is_public': chosen_is_public}
                modeladmin.message_user(request, message)
                return HttpResponseRedirect(request.get_full_path())
        if 'cancel' in request.POST:
            return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = AccessAllowedForm(initial={
                '_selected_action': request.POST.getlist(
                    admin.ACTION_CHECKBOX_NAME),
            })

        return render(request, options_template_name, context={
            'mediafiles': queryset,
            'action_form': form,
            'opts': modeladmin.model._meta,
            'queryset': queryset,
        })
    change_is_public_action.short_description = _("Zugriff für ausgewählte Mediendateien setzen")

