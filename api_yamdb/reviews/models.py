from django.contrib.auth.models import AbstractUser
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from reviews.validators import title_year_validator


class User(AbstractUser):
    """Модель представления пользователя.

    """
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'

    ROLE_CHOICES = (
        (ADMIN, 'admin'),
        (MODERATOR, 'moderator'),
        (USER, 'user'),
    )

    role = models.CharField(
        choices=ROLE_CHOICES,
        default=USER,
        max_length=10,
        verbose_name='Роль'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='О себе'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def save(self, *args, **kwargs):
        User._meta.get_field('username').db_index = True

        if self.role == self.ADMIN:
            self.is_staff = True

        super().save(*args, **kwargs)

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    def __str__(self) -> str:
        return f'{self.username} [{self.role}]'


class Title(models.Model):
    """Модель представления произведения.

    """
    name = models.CharField(
        'Название',
        null=False,
        max_length=256
    )
    description = models.TextField(
        'Описание',
        blank=True
    )
    year = models.PositiveSmallIntegerField(
        'Год написания',
        default=0,
        validators=[
            title_year_validator
        ]
    )
    genre = models.ManyToManyField(
        'Genre',
        through='TitleGenre',
        verbose_name='Жанры',
    )
    category = models.ForeignKey(
        'Category',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    """Модель представления категории.

    """
    name = models.CharField(
        'Название',
        max_length=256,
        db_index=True,
    )
    slug = models.SlugField(
        'Слаг',
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(r'^[-a-zA-Z0-9_]+$')
        ]
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self) -> str:
        return self.slug


class Genre(models.Model):
    """Модель представления жанра.

    """
    name = models.CharField(
        'Название',
        max_length=256,
        db_index=True,
    )
    slug = models.SlugField(
        'Слаг',
        max_length=50,
        validators=[
            RegexValidator(r'^[-a-zA-Z0-9_]+$')
        ],
        unique=True
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.slug


class TitleGenre(models.Model):
    title = models.ForeignKey(
        'Title',
        verbose_name='Произведение',
        on_delete=models.CASCADE
    )
    genre = models.ForeignKey(
        'Genre',
        verbose_name='Жанр',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Произведение-Жанр'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'genre'],
                name='unique_title_AK'
            ),
        ]


class Review(models.Model):
    """Модель представления отзыва.

    """
    title = models.ForeignKey(
        'Title',
        verbose_name='Произведение',
        on_delete=models.CASCADE
    )
    text = models.CharField(
        verbose_name='Текст отзыва',
        max_length=200
    )
    author = models.ForeignKey(
        'User',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        verbose_name='Оценка'
    )

    class Meta:
        default_related_name = 'reviews'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = (
            models.UniqueConstraint(
                fields=['author', 'title'],
                name='unique_author_title'
            ),
        )

    def __str__(self):
        return self.text


class Comment(models.Model):
    """Модель представления комментария к отзыву.

    """
    review = models.ForeignKey(
        'Review',
        verbose_name='Отзыв',
        on_delete=models.CASCADE
    )
    text = models.TextField(
        max_length=200
    )
    author = models.ForeignKey(
        'User',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'

    def __str__(self):
        return self.text
