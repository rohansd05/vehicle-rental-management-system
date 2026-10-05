"""Accounts models.

Phase 0 holds only the minimal custom user, created before the first migrate
so AUTH_USER_MODEL never has to change. It carries the attributes of the
Exp 3 «interface» User (name, address, mobile_no, email, password). The
role-specific classes (Customer, BranchStaff, MaintenanceTechnician,
Administrator, BranchManager) are added in Phase 1.

Owner: Rohan (WBS 1.4.1). Only the owner edits this file or its migrations.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields) -> "User":
        if not email:
            raise ValueError("An e-mail address is required.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("role", User.Role.ADMINISTRATOR)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """A person who signs in to VRMS. Guests are never persisted."""

    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        BRANCH_STAFF = "BRANCH_STAFF", "Branch Staff"
        MAINTENANCE_TECHNICIAN = "MAINTENANCE_TECHNICIAN", "Maintenance Technician"
        ADMINISTRATOR = "ADMINISTRATOR", "Administrator"
        BRANCH_MANAGER = "BRANCH_MANAGER", "Branch Manager"

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    mobile_no = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.CUSTOMER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name", "mobile_no"]

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email
