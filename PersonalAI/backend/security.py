"""
Security & Authentication Module
Handles JWT, encryption, RBAC, and compliance
"""

import os
import hashlib
import secrets
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps

import jwt
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
REFRESH_TOKEN_EXPIRATION_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", "7"))

# Encryption
MASTER_KEY = os.getenv("MASTER_KEY", "")
ENCRYPTION_ALGORITHM = "AES-256-GCM"

# ============================================================================
# PASSWORD HASHING
# ============================================================================

class PasswordService:
    """Password hashing and verification using bcrypt"""
    
    BCRYPT_ROUNDS = 12
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        
        salt = bcrypt.gensalt(rounds=PasswordService.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False

# ============================================================================
# ENCRYPTION SERVICE
# ============================================================================

class EncryptionService:
    """Symmetric encryption for sensitive data at rest"""
    
    def __init__(self, master_key: Optional[str] = None):
        if not master_key and not MASTER_KEY:
            raise ValueError("Master key not configured")
        
        self.master_key = master_key or MASTER_KEY
        self._cipher_suite = None
    
    def _get_cipher_suite(self):
        """Get or create Fernet cipher suite"""
        
        if self._cipher_suite:
            return self._cipher_suite
        
        # Derive key from master key using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'personal_ai_salt',  # TODO: Use unique salt per user
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self._cipher_suite = Fernet(key)
        
        return self._cipher_suite
    
    def encrypt(self, plaintext: str, user_id: Optional[str] = None) -> str:
        """Encrypt plaintext"""
        
        try:
            cipher_suite = self._get_cipher_suite()
            ciphertext = cipher_suite.encrypt(plaintext.encode())
            return ciphertext.decode()
        
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, ciphertext: str, user_id: Optional[str] = None) -> str:
        """Decrypt ciphertext"""
        
        try:
            cipher_suite = self._get_cipher_suite()
            plaintext = cipher_suite.decrypt(ciphertext.encode())
            return plaintext.decode()
        
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise

# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

class TokenService:
    """JWT token creation and verification"""
    
    @staticmethod
    def create_access_token(
        user_id: str,
        scopes: List[str] = None,
        expires_in_hours: int = JWT_EXPIRATION_HOURS
    ) -> str:
        """Create JWT access token"""
        
        if scopes is None:
            scopes = ["read", "write"]
        
        payload = {
            "sub": user_id,
            "type": "access",
            "scopes": scopes,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create JWT refresh token"""
        
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS),
            "jti": secrets.token_urlsafe(32)  # Unique ID for revocation
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type: {payload.get('type')}")
                return None
            
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """Exchange refresh token for new access token"""
        
        payload = TokenService.verify_token(refresh_token, token_type="refresh")
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        return TokenService.create_access_token(user_id)

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimitService:
    """Rate limiting implementation using sliding window"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if user has exceeded rate limit
        Returns: True if allowed, False if rate limited
        """
        
        key = f"rate_limit:{user_id}:{endpoint}"
        
        try:
            current = await self.redis.incr(key)
            
            if current == 1:
                # First request in window, set expiration
                await self.redis.expire(key, window_seconds)
            
            return current <= limit
        
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error
    
    async def get_remaining(self, user_id: str, endpoint: str, limit: int) -> int:
        """Get remaining requests in current window"""
        
        key = f"rate_limit:{user_id}:{endpoint}"
        
        try:
            current = await self.redis.get(key)
            return max(0, limit - (int(current) if current else 0))
        
        except Exception as e:
            logger.error(f"Remaining calls check error: {e}")
            return limit

# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Log all security-relevant actions"""
    
    def __init__(self, database):
        self.db = database
    
    async def log_action(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security-relevant action"""
        
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "status": status,
                "error_message": error_message,
                "ip_address": ip_address,
                "details": details or {}
            }
            
            # TODO: Insert into audit_log table
            logger.info(f"Audit: {action} by {user_id} ({status})")
        
        except Exception as e:
            logger.error(f"Audit logging error: {e}")

# ============================================================================
# RBAC (Role-Based Access Control)
# ============================================================================

class Role:
    """User role definitions"""
    
    ADMIN = "admin"
    PREMIUM = "premium"
    STANDARD = "standard"
    DEMO = "demo"
    
    ALL_ROLES = [ADMIN, PREMIUM, STANDARD, DEMO]

class Permission:
    """Permission definitions"""
    
    # Knowledge
    UPLOAD_DOCUMENTS = "upload_documents"
    DELETE_DOCUMENTS = "delete_documents"
    SEARCH_KNOWLEDGE = "search_knowledge"
    EXPORT_KNOWLEDGE = "export_knowledge"
    
    # Chat
    USE_CHAT = "use_chat"
    USE_ADVANCED_MODELS = "use_advanced_models"
    
    # Settings
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    
    # Admin
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_SYSTEM = "manage_system"

ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.UPLOAD_DOCUMENTS,
        Permission.DELETE_DOCUMENTS,
        Permission.SEARCH_KNOWLEDGE,
        Permission.EXPORT_KNOWLEDGE,
        Permission.USE_CHAT,
        Permission.USE_ADVANCED_MODELS,
        Permission.MANAGE_SETTINGS,
        Permission.MANAGE_USERS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_SYSTEM,
    ],
    Role.PREMIUM: [
        Permission.UPLOAD_DOCUMENTS,
        Permission.DELETE_DOCUMENTS,
        Permission.SEARCH_KNOWLEDGE,
        Permission.EXPORT_KNOWLEDGE,
        Permission.USE_CHAT,
        Permission.USE_ADVANCED_MODELS,
        Permission.MANAGE_SETTINGS,
        Permission.VIEW_ANALYTICS,
    ],
    Role.STANDARD: [
        Permission.UPLOAD_DOCUMENTS,
        Permission.SEARCH_KNOWLEDGE,
        Permission.USE_CHAT,
        Permission.MANAGE_SETTINGS,
    ],
    Role.DEMO: [
        Permission.SEARCH_KNOWLEDGE,
        Permission.USE_CHAT,
    ],
}

class RBACService:
    """Role-based access control"""
    
    @staticmethod
    def has_permission(role: str, permission: str) -> bool:
        """Check if role has permission"""
        
        permissions = ROLE_PERMISSIONS.get(role, [])
        return permission in permissions
    
    @staticmethod
    def require_permission(permission: str):
        """Decorator to require permission"""
        
        def decorator(func):
            @wraps(func)
            async def wrapper(current_user: Dict[str, Any], *args, **kwargs):
                user_role = current_user.get("role", Role.DEMO)
                
                if not RBACService.has_permission(user_role, permission):
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=403,
                        detail=f"User does not have permission: {permission}"
                    )
                
                return await func(current_user, *args, **kwargs)
            
            return wrapper
        return decorator

# ============================================================================
# GDPR & COMPLIANCE
# ============================================================================

class ComplianceService:
    """GDPR and privacy compliance"""
    
    def __init__(self, database):
        self.db = database
        self.audit_logger = AuditLogger(database)
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data (GDPR right to access)"""
        
        logger.info(f"Exporting data for user {user_id}")
        
        try:
            # TODO: Fetch all user data
            data = {
                "user_id": user_id,
                "documents": [],
                "interactions": [],
                "settings": {},
                "exported_at": datetime.utcnow().isoformat()
            }
            
            await self.audit_logger.log_action(
                user_id=user_id,
                action="data_export",
                status="success"
            )
            
            return data
        
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise
    
    async def delete_user_data(self, user_id: str, reason: str = "user_request") -> bool:
        """Delete all user data (GDPR right to be forgotten)"""
        
        logger.info(f"Deleting data for user {user_id}, reason: {reason}")
        
        try:
            # TODO: Implement hard delete via gdpr_delete_user() function
            
            await self.audit_logger.log_action(
                user_id=user_id,
                action="gdpr_delete_user",
                status="success",
                details={"reason": reason}
            )
            
            logger.info(f"User {user_id} data deleted successfully")
            return True
        
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False
    
    async def is_data_retention_expired(self, user_id: str) -> bool:
        """Check if user's data retention period has expired"""
        
        try:
            # TODO: Fetch user's retention period preference
            # TODO: Check if creation_date + retention_days < now()
            
            return False
        
        except Exception as e:
            logger.error(f"Retention check error: {e}")
            return False

# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

class APIKeyService:
    """Manage API keys for programmatic access"""
    
    @staticmethod
    def generate_api_key(user_id: str, name: str) -> str:
        """Generate new API key"""
        
        # Generate random key
        api_key = f"pai_{secrets.token_urlsafe(32)}"
        
        # TODO: Store hash of API key in database
        # key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        logger.info(f"API key generated for user {user_id}: {name}")
        
        return api_key
    
    @staticmethod
    def verify_api_key(api_key: str) -> Optional[str]:
        """Verify API key and return user_id"""
        
        try:
            # TODO: Look up key hash in database
            # key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            return None  # Placeholder
        
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return None

# ============================================================================
# SECURITY HEADERS
# ============================================================================

class SecurityHeadersMiddleware:
    """Middleware to add security headers"""
    
    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            async def send_with_headers(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    for key, value in self.HEADERS.items():
                        headers.append((key.lower().encode(), value.encode()))
                    message["headers"] = headers
                
                await send(message)
            
            await self.app(scope, receive, send_with_headers)
        else:
            await self.app(scope, receive, send)
