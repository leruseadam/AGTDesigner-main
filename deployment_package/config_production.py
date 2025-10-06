import os

class Config:
    # Production settings
    DEVELOPMENT_MODE = False  # Disable development mode for production
    DEBUG = False  # Disable debug mode
    TEMPLATES_AUTO_RELOAD = False  # Disable auto-reload in production
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # Cache static files for 1 year
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'label-maker-secret-key-2024-production')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB max file size
    
    # Session settings
    SESSION_REFRESH_EACH_REQUEST = False
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    SESSION_COOKIE_SECURE = True  # Require HTTPS in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_MAX_SIZE = 8192
    
    # Caching
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Compression
    COMPRESS_ALGORITHM = 'gzip'
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 1024
    COMPRESS_MIMETYPES = [
        'application/json',
        'text/html',
        'text/css',
        'application/javascript',
        'text/javascript',
        'text/plain'
    ]
