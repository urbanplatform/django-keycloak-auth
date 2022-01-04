from dry_rest_permissions.generics import DRYPermissionFiltersBase


class DRYPermissionFilter(DRYPermissionFiltersBase):
    def filter_list_queryset(self, request, queryset, view):
        model = queryset.model
        q_filter = model.permission_filter(request)
        return queryset.filter(q_filter).distinct()
