from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Exists, OuterRef


class UserQueryset(models.QuerySet):
    def user_annotations_add(self, user_id):
        return self.annotate(
            is_subscribed=Exists(
                Follow.objects.filter(
                    user_id=user_id, author__pk=OuterRef('pk')
                )
            )
        )


class CustomUserManager(BaseUserManager):
    objects = UserQueryset.as_manager()

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("Вы не ввели Email")
        if not username:
            raise ValueError("Вы не ввели Логин")
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password, **extra_fields):
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password, **extra_fields):
        return self._create_user(email, username, password,
                                 is_staff=True, is_superuser=True,
                                 **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    ROLES = (
        (USER, 'user'),
        (MODERATOR, 'moderator'),
        (ADMIN, 'admin')
    )
    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default='user',
        verbose_name='user role')
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        verbose_name='username',
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer.',
        validators=[username_validator],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    first_name = models.CharField(verbose_name='first name',
                                  max_length=150,
                                  blank=True)
    last_name = models.CharField(verbose_name='last name',
                                 max_length=150,
                                 blank=True)
    is_staff = models.BooleanField(
        verbose_name='staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    bio = models.TextField(verbose_name='biography',
                           blank=True)
    email = models.EmailField(verbose_name='email address',
                              unique=True)
    is_active = models.BooleanField(default=True,
                                    verbose_name='user is active')
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    objects = CustomUserManager()

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_moderator(self):
        return self.role == 'moderator'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return '%s (%s)' % (self.get_full_name(), self.email)


class ConfirmCodes(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='ConfirmCodes',
        verbose_name='owner of code')
    reg_code = models.CharField(max_length=6,
                                default=None,
                                null=True,
                                blank=True,
                                verbose_name='registratoin code')
    code_date = models.DateTimeField(auto_now_add=True,
                                     verbose_name='Дата создания кода')

    class Meta:
        verbose_name = 'Код подтверждения'
        verbose_name_plural = 'Коды подтверждения'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Фоловер - тот, кто подписывается',
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор - на кого подписываются',
        related_name='following'
    )

    def __str__(self):
        return f'Результат: {self.user}  подписался на {self.author}'

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="prevent_self_follow",
                check=~models.Q(user=models.F("author")),
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
