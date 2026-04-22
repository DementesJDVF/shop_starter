import base64
from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    @staticmethod
    def get_fernet():
        key = getattr(settings, "ENCRYPTION_KEY", None)
        if not key:
            # Fallback for development if key is missing, BUT should be avoided in prod
            logger.warning("ENCRYPTION_KEY not found in settings. Data will NOT be encrypted correctly!")
            return None
        try:
            return Fernet(key.encode())
        except Exception as e:
            logger.error(f"Error initializing Fernet: {e}")
            return None

    @classmethod
    def encrypt(cls, value):
        if value is None or value == "":
            return value
        f = cls.get_fernet()
        if not f:
            return value
        return f.encrypt(str(value).encode()).decode()

    @classmethod
    def decrypt(cls, value):
        if value is None or value == "":
            return value
        f = cls.get_fernet()
        if not f:
            return value
        try:
            return f.decrypt(value.encode()).decode()
        except Exception:
            # If decryption fails, it might be clear text (initial state)
            return value

class EncryptedCharField(models.CharField):
    """
    Transparently encrypts/decrypts data when saving/reading from DB.
    """
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return EncryptionService.encrypt(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return EncryptionService.decrypt(value)

    def to_python(self, value):
        if value is None:
            return value
        return EncryptionService.decrypt(value)
