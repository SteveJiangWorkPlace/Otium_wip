"""
Services package

Contains all service modules for the application.
"""

# Import key services for easy access
from .email_service import EmailService, email_service
from .verification_service import VerificationService, verification_service

__all__ = ["email_service", "EmailService", "verification_service", "VerificationService"]
