"""
Services package

Contains all service modules for the application.
"""

# Import key services for easy access
from .email_service import email_service, EmailService
from .verification_service import verification_service, VerificationService

__all__ = [
    'email_service',
    'EmailService',
    'verification_service',
    'VerificationService'
]