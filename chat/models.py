from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _


class ChatUserManager(BaseUserManager):

    def _create_user(
            self,
            username: str,
            password=None,
            **extra_fields
    ) -> "User":

        if not username:
            raise ValueError('The Username field must be set.')

        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)

        user = self.model(username=username, **extra_fields)
        if password:
            user.password = make_password(password)
            user.save(using=self._db)
            return user

        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, username, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, **extra_fields)


    def create_superuser(
            self,
            username: str,
            password=None,
            **extra_fields
    ) -> "User":
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    objects = ChatUserManager()
    USERNAME_FIELD = "username"

    def __str__(self) -> str:
        return self.username

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")


class Pseudonym(models.Model):
    body = models.CharField(_("pseudonym"), max_length=150)
    user = models.ManyToManyField(User, related_name="pseudonyms")

    def __str__(self) -> str:
        return self.body


class Contact(models.Model):
    user_pseudonym = models.ForeignKey(
        Pseudonym,
        related_name="friends",
        on_delete=models.CASCADE
    )
    friends = models.ManyToManyField('self', blank=True)

    def __str__(self) -> str:
        return self.user_pseudonym.body


class Message(models.Model):
    user_pseudonym = models.ForeignKey(
        Pseudonym,
        related_name="messages",
        on_delete=models.CASCADE
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp", )


class Chat(models.Model):
    participants = models.ManyToManyField(Pseudonym, related_name="chats")
    messages = models.ManyToManyField(Message, blank=True)

    def get_last_10_messages(self) -> QuerySet:
        return self.messages.all()[:10]

    def __str__(self) -> str:
        return str(self.pk)
