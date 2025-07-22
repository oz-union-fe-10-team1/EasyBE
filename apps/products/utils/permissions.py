# apps/products/utils/permissions.py

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    관리자는 모든 권한, 일반 사용자는 읽기만 가능
    """

    def has_permission(self, request, view):
        # 읽기 권한은 모든 사용자에게 허용
        if request.method in permissions.SAFE_METHODS:
            return True

        # 쓰기 권한은 관리자만
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    객체 소유자는 수정 가능, 다른 사용자는 읽기만 가능
    """

    def has_object_permission(self, request, view, obj):
        # 읽기 권한은 모든 사용자에게 허용
        if request.method in permissions.SAFE_METHODS:
            return True

        # 쓰기 권한은 소유자만 (user 필드가 있는 경우)
        return hasattr(obj, "user") and obj.user == request.user


class IsAdminUser(permissions.BasePermission):
    """
    관리자만 접근 가능
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    인증된 사용자는 모든 권한, 비인증 사용자는 읽기만 가능
    """

    def has_permission(self, request, view):
        # 읽기 권한은 모든 사용자에게 허용
        if request.method in permissions.SAFE_METHODS:
            return True

        # 쓰기 권한은 인증된 사용자만
        return request.user and request.user.is_authenticated
