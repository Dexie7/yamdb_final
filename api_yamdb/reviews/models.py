from django.contrib.auth.models import AbstractUser
from django.core.validators import (MaxValueValidator,
                                    MinValueValidator
                                    )
from django.db import models

from collections import namedtuple

from api_yamdb.settings import (EMAIL_LENGTH,
                                USERNAME_LENGTH,
                                FIRST_NAME_LENGTH,
                                LAST_NAME_LENGTH,
                                PASSWORD_LENGTH
                                )
from .validators import (
    username_validator, year_validator)


ROLES = namedtuple('ROLES_NAME', 'user moderator admin')(
    'user', 'moderator', 'admin')
ROLE_CHOICES = (
    ('user', ROLES.user),
    ('moderator', ROLES.moderator),
    ('admin', ROLES.admin),
)


class User(AbstractUser):
    """Модель пользователей."""
    username = models.CharField(
        'Имя пользователя',
        unique=True,
        max_length=USERNAME_LENGTH,
        validators=[username_validator]
    )
    email = models.EmailField(
        'Email пользователя',
        blank=False,
        unique=True,
        max_length=EMAIL_LENGTH,
    )
    first_name = models.CharField(
        'Имя',
        max_length=FIRST_NAME_LENGTH,
        blank=True
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LAST_NAME_LENGTH,
        blank=True
    )
    bio = models.TextField(
        'Биография',
        blank=True,
    )
    role = models.CharField(
        'Роль пользователя',
        max_length=max(len(role) for _, role in ROLE_CHOICES),
        choices=ROLE_CHOICES,
        default=ROLES.user,
    )
    password = models.CharField(
        max_length=PASSWORD_LENGTH,
        blank=True,
        default='')

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def is_moderator(self):
        return self.role == ROLES.moderator

    def is_admin(self):
        return (
            self.role == ROLES.admin
            or self.is_staff
        )

    def __str__(self):
        return self.username


class BaseCategoryGenre(models.Model):
    """Базовый класс для категорий и жанров."""
    name = models.CharField(
        max_length=256,
        db_index=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        unique=True,
        max_length=50,
        verbose_name='Удобочитаемая метка URL',
    )

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(BaseCategoryGenre):
    """Категории произведений."""

    class Meta(BaseCategoryGenre.Meta):
        verbose_name = 'Категорию'
        verbose_name_plural = 'Категории'


class Genre(BaseCategoryGenre):
    """Жанры произведений."""

    class Meta(BaseCategoryGenre.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    """Произведения, к которым пишут отзывы (Review)."""
    name = models.TextField()
    year = models.IntegerField(verbose_name="Год",
                               validators=[year_validator],)
    genre = models.ManyToManyField(
        Genre,
        related_name='titles',
        verbose_name='Жанр произведения',
    )
    category = models.ForeignKey(
        Category,
        null=True,
        on_delete=models.SET_NULL,
        related_name='titles',
        db_column='category'
    )
    description = models.TextField(
        verbose_name='Описание', blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'


class BaseReviewComment(models.Model):
    """Базовая модель ревью и комментариев."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='author'
    )
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата',
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.pub_date} | {self.author} | {self.text[:15]}'


class Review(BaseReviewComment):
    """Отзывы на произведения."""
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
    )
    score = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(10),
            MinValueValidator(1)
        ],
        verbose_name='Рейтинг произведения'
    )

    class Meta(BaseReviewComment.Meta):
        default_related_name = 'reviews'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            )
        ]
        verbose_name = 'Ревью'
        verbose_name_plural = 'Ревью'


class Comment(BaseReviewComment):
    """Комментарии к отзыву."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
    )

    class Meta(BaseReviewComment.Meta):
        default_related_name = 'comments'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
