from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.validators import UniqueValidator

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from reviews.models import (
    Category,
    Comment,
    Genre,
    Review,
    Title,
)

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для получения jwt-токена.

    Attributes:
        user_obj: объект пользователя.

    """
    def __init__(self, *args, **kwargs):
        """Инициализатор класса."""
        super().__init__(*args, **kwargs)

        # поле username.
        self.fields[self.username_field] = serializers.RegexField(
            regex=r'^[\w.@+-]+$',
            max_length=150,
        )

        # поле confirmation_code.
        self.fields['confirmation_code'] = serializers.CharField(
            write_only=True
        )

        # встроенное поле password нам не требуется.
        self.fields['password'].required = False
        self.user_obj = None

    def _validate_fields(self, attrs):
        """Вспомогательный метод для проверки полей.

        Используется в методе validate.

        Raises:
            ValidationError: если пользователь не найден или неверный
                confirmation_code.

        """
        try:
            self.user_obj = User.objects.get(username=attrs['username'])

        except User.DoesNotExist as e:
            raise NotFound('Пользователь не найден.') from e

        if not default_token_generator.check_token(
                self.user_obj, attrs['confirmation_code']):
            raise ValidationError('Неверный confirmation code.')

        return {}

    def validate(self, attrs):
        """Переопределенный метод родительского класса.

        Часть кода взята из метода validate родительского класса.

        При успешной валидации полей методом _validate_fields, переменная
        data принимает пустой словарь и далее туда записываем токен.

        """
        data = self._validate_fields(attrs)

        refresh = self.get_token(self.user_obj)

        data["token"] = str(refresh.access_token)

        return data


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели User.

    """
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=150,
        validators=(
            UniqueValidator(
                queryset=User.objects.all(),
                message='Данное имя пользователя уже занято.'
            ),
        ),
    )
    email = serializers.EmailField(max_length=254)
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    bio = serializers.CharField(required=False)
    role = serializers.ChoiceField(
        required=False,
        choices=User.ROLE_CHOICES,
        default=User.USER,
    )

    class Meta:
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )
        model = User

    def validate_username(self, value):
        if value == 'me':
            raise ValidationError('Значение username не может быть "me".')

        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError(
                'Пользователь с таким email уже существует.'
            )

        return value


class SignUpNewUserSerializer(UserSerializer):
    """Сериализатор для создания нового пользователя.

    """
    class Meta(UserSerializer.Meta):
        fields = ('email', 'username')


class SignUpExistingUserSerializer(SignUpNewUserSerializer):
    """Сериализатор для работы с существующими пользователями.

    """
    username = serializers.RegexField(regex=r'^[\w.@+-]+$', max_length=150)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise ValidationError(
                'Пользователь с таким email не существует.'
            )

        return value

    def validate_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise ValidationError(
                'Пользователь не найден.'
            )

        return super().validate_username(value)


class GetSelfDataSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        read_only_fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )


class PatchSelfDataSerializer(SignUpExistingUserSerializer):

    class Meta(UserSerializer.Meta):
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
        )


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор модели категории.

    """
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор модели жанра.

    """
    class Meta:
        model = Genre
        fields = ('name', 'slug',)


class TitleSerializer(serializers.ModelSerializer):
    """Сериализатор модели произведения.

    """
    rating = serializers.SerializerMethodField()
    category = CategorySerializer()
    genre = GenreSerializer(many=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'description',
            'year',
            'genre',
            'category',
            'rating'
        )

    def get_rating(self, obj) -> int:
        """Возвращает значение рейтинга произведения как среднее всех обзоров.

        """
        rating = obj.reviews.aggregate(Avg('score')).get('score__avg')

        if not rating:
            return rating

        return round(rating, 1)


class TitleCreateSerializer(serializers.ModelSerializer):
    """Сериализатор модели произведения (Создание и изменение).

    """
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all(),
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug', queryset=Genre.objects.all(), many=True
    )

    class Meta:
        model = Title
        fields = '__all__'

    def validate_year(self, value) -> int:
        if not 0 <= value <= timezone.now().year:
            raise serializers.ValidationError(
                'Год создания должен быть между 0 и текущим годом.'
            )

        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор модели отзыва.

    """
    MIN_LIMIT_VALUE = 1
    MAX_LIMIT_VALUE = 10

    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    score = serializers.IntegerField(
        validators=[
            MinValueValidator(
                limit_value=MIN_LIMIT_VALUE,
                message='Минимальное значение рейтинга - 1'
            ),
            MaxValueValidator(
                limit_value=MAX_LIMIT_VALUE,
                message='Максимальное значение рейтинга - 10'
            )
        ],
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'pub_date', 'score')
        read_only_fields = ('pub_date',)

    def validate(self, data):
        if self.context['request'].method == 'POST':
            user = self.context['request'].user
            title_id = self.context['view'].kwargs.get('title_id')
            title = get_object_or_404(Title, pk=title_id)

            if title.reviews.filter(author=user):
                raise ValidationError(
                    'К одному произведению можно оставить один отзыв.'
                )

        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор модели комментария.

    """
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('pub_date',)
