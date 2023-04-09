from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import BasePermission


class ReviewViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ['retrieve', 'list', 'partial_update', 'destroy',
                           'update']:
            return True

        if view.action == 'create':
            return request.user.is_authenticated

        if request.method == 'PUT':
            raise MethodNotAllowed(request.method)

    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return True

        return (
            request.user.is_authenticated
            and (request.user.is_staff
                 or request.user.is_moderator
                 or request.user == obj.author)
        )


class CommentViewSetPermission(ReviewViewSetPermission):
    pass
