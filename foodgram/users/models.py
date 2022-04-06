from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)


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
