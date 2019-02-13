from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


class DropUploadAdminMixin:
    class Media:
        css = {"all": ("media_archive/css/admin_file_drop.css",)}
        js = (
            "media_archive/js/admin_file_drop.js",
        )

    def get_urls(self):
        from django.conf.urls import url

        return [
            url(
                r"^upload/$",
                self.admin_site.admin_view(self.upload),
                name="media_archive_upload",
            )
        ] + super().get_urls()

    def upload(self, request):
        # We must initialize a fake-ChangeList to be able to get the currently
        # selected categories.
        # Code copied from django.contrib.admin.options.ModelAdmin.changelist_view
        if not self.has_change_permission(request, None):
            raise PermissionDenied

        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)
        list_select_related = self.get_list_select_related(request)

        # Check actions to see if any are available on this changelist
        actions = self.get_actions(request)
        if actions:
            # Add the action checkboxes if there are any actions available.
            list_display = ['action_checkbox'] + list(list_display)

        ChangeList = self.get_changelist(request)
        changelist = ChangeList(
            request, self.model, list_display,
            list_display_links, list_filter, self.date_hierarchy,
            search_fields, list_select_related, self.list_per_page,
            self.list_max_show_all, self.list_editable, self,
        )

        # Put uploaded file in selected categories
        if changelist.result_list:
            filtered_categories = changelist.result_list.first().categories.all()
        elif 'categories__exact' in changelist.params:
            from .models import MediaCategory
            filtered_categories = MediaCategory.objects.filter(
                categories__exact=int(changelist.params['categories__exact']))
        else:
            filtered_categories = None

        f = self.model()
        f.file = request.FILES["file"]
        f.save()

        if filtered_categories:
            for cat in filtered_categories:
                f.categories.add(cat)
        return JsonResponse({"success": True})
