from rest_framework.permissions import BasePermission, SAFE_METHODS


# TODO: add this permission only if authorized users can only view information
#  on the site, while administrators can view, update, create and delete it
class IsAdminOrIfAuthenticatedReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            (
                    request.method in SAFE_METHODS
                    and request.user
                    and request.user.is_authenticated
            )
            or (request.user and request.user.is_staff)
        )
