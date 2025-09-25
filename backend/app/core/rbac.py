"""
Role-Based Access Control for RetailXAI Dashboard
"""

from enum import Enum
from typing import List, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.auth import get_current_user


class Permission(str, Enum):
    """Available permissions in the system."""
    # Draft permissions
    DRAFT_READ = "draft:read"
    DRAFT_CREATE = "draft:create"
    DRAFT_UPDATE = "draft:update"
    DRAFT_DELETE = "draft:delete"
    DRAFT_PUBLISH = "draft:publish"
    
    # Job permissions
    JOB_READ = "job:read"
    JOB_RETRY = "job:retry"
    
    # Health permissions
    HEALTH_READ = "health:read"
    
    # Endpoint permissions
    ENDPOINT_READ = "endpoint:read"
    ENDPOINT_CREATE = "endpoint:create"
    ENDPOINT_UPDATE = "endpoint:update"
    ENDPOINT_DELETE = "endpoint:delete"
    ENDPOINT_TEST = "endpoint:test"
    
    # Settings permissions
    SETTINGS_READ = "settings:read"
    SETTINGS_UPDATE = "settings:update"
    
    # Audit permissions
    AUDIT_READ = "audit:read"
    
    # User management permissions
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"


# Role permissions mapping
ROLE_PERMISSIONS = {
    UserRole.VIEWER: [
        Permission.DRAFT_READ,
        Permission.JOB_READ,
        Permission.HEALTH_READ,
        Permission.ENDPOINT_READ,
        Permission.SETTINGS_READ,
        Permission.AUDIT_READ,
        Permission.USER_READ,
    ],
    UserRole.EDITOR: [
        Permission.DRAFT_READ,
        Permission.DRAFT_CREATE,
        Permission.DRAFT_UPDATE,
        Permission.DRAFT_PUBLISH,
        Permission.JOB_READ,
        Permission.JOB_RETRY,
        Permission.HEALTH_READ,
        Permission.ENDPOINT_READ,
        Permission.ENDPOINT_CREATE,
        Permission.ENDPOINT_UPDATE,
        Permission.ENDPOINT_TEST,
        Permission.SETTINGS_READ,
        Permission.AUDIT_READ,
        Permission.USER_READ,
    ],
    UserRole.ADMIN: [
        # All permissions
        *[permission for permission in Permission],
    ],
}


def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has a specific permission."""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def require_permission(permission: Permission):
    """Decorator to require a specific permission."""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return current_user
    return permission_checker


def require_role(required_role: UserRole):
    """Decorator to require a specific role or higher."""
    def role_checker(current_user: User = Depends(get_current_user)):
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.EDITOR: 2,
            UserRole.ADMIN: 3,
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role.value} or higher"
            )
        return current_user
    return role_checker


def require_admin():
    """Require admin role."""
    return require_role(UserRole.ADMIN)


def require_editor():
    """Require editor role or higher."""
    return require_role(UserRole.EDITOR)


def require_viewer():
    """Require viewer role or higher (any authenticated user)."""
    return require_role(UserRole.VIEWER)


class RBACDependency:
    """Dependency class for RBAC checks."""
    
    def __init__(self, permission: Optional[Permission] = None, role: Optional[UserRole] = None):
        self.permission = permission
        self.role = role
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        if self.permission and not has_permission(current_user, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {self.permission.value}"
            )
        
        if self.role:
            role_hierarchy = {
                UserRole.VIEWER: 1,
                UserRole.EDITOR: 2,
                UserRole.ADMIN: 3,
            }
            
            user_level = role_hierarchy.get(current_user.role, 0)
            required_level = role_hierarchy.get(self.role, 0)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient role. Required: {self.role.value} or higher"
                )
        
        return current_user


# Common permission dependencies
require_draft_read = RBACDependency(permission=Permission.DRAFT_READ)
require_draft_write = RBACDependency(permission=Permission.DRAFT_CREATE)
require_draft_publish = RBACDependency(permission=Permission.DRAFT_PUBLISH)
require_job_management = RBACDependency(permission=Permission.JOB_RETRY)
require_endpoint_management = RBACDependency(permission=Permission.ENDPOINT_CREATE)
require_settings_management = RBACDependency(permission=Permission.SETTINGS_UPDATE)
require_audit_access = RBACDependency(permission=Permission.AUDIT_READ)
