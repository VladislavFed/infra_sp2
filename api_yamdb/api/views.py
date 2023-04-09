from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rest_framework_simplejwt.views import TokenObtainPairView

from django_filters import rest_framework as filters

from api_yamdb.settings import DEFAULT_FROM_EMAIL

from api.filters import TitleFilterSet
from api.permissions import (
    CommentViewSetPermission,
    ReviewViewSetPermission,
)
from api.serializers import (
    CategorySerializer,
    CommentSerializer,
    CustomTokenObtainPairSerializer,
    GenreSerializer,
    GetSelfDataSerializer,
    PatchSelfDataSerializer,
    ReviewSerializer,
    SignUpExistingUserSerializer,
    SignUpNewUserSerializer,
    TitleCreateSerializer,
    TitleSerializer,
    UserSerializer,
)

from reviews.models import Category, Genre, Review, Title

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Переопределенный вью-класс из rest_framework-simplejwt.

    Используем свой кастомный сериализатор.

    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (AllowAny,)


class UsersViewSet(ModelViewSet):
    """Вьюсет для работы с пользователями.

    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    @action(methods=['get', 'patch'], url_path='me', url_name='me',
            permission_classes=[IsAuthenticated],
            detail=False)
    def get_self_data(self, request, *args, **kwargs):
        if request.method == 'GET':
            serializer = GetSelfDataSerializer(request.user)
            return Response(serializer.data, status.HTTP_200_OK)

        serializer = PatchSelfDataSerializer(
            request.user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class SignUpAPIView(CreateAPIView):
    """Вью-класс отправки письма с кодом подтверждения.

    """
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():

            if isinstance(serializer, SignUpExistingUserSerializer):
                user = User.objects.get(
                    username=serializer.validated_data['username']
                )
                confirmation_code = default_token_generator.make_token(
                    user=user
                )
                self._send_msg(user, confirmation_code)
                return Response(serializer.data, status.HTTP_200_OK)

            serializer.save()
            confirmation_code = default_token_generator.make_token(
                user=serializer.instance
            )
            self._send_msg(serializer.instance, confirmation_code)
            return Response(serializer.data, status.HTTP_200_OK)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        try:
            User.objects.get(username=self.request.data.get('username'))

        except User.DoesNotExist:
            return SignUpNewUserSerializer

        return SignUpExistingUserSerializer

    def _send_msg(self, user, confirmation_code):
        """Вспомогательный метод для отправки письма с виртуального сервера.

        Args:
            user: объект пользователя.
            confirmation_code: код подтверждения.

        """
        subject = 'Email Confirmation'
        body = (f'Код подтверждения для пользователя {user.username}: '
                f'{confirmation_code}')

        send_mail(
            subject=subject,
            message=body,
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=(user.email,),
        )


class GenreViewSet(ModelViewSet):
    """Вьюсет жанров.

    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('name',)

    @action(detail=False,
            methods=['delete'],
            url_path=r'(?P<slug>\w+)',
            lookup_field='slug'
            )
    def delete_genre(self, request, slug):
        genre: Genre = self.get_object()
        serializer = CategorySerializer(genre)
        genre.delete()

        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'list':
            return (AllowAny(),)

        return super().get_permissions()


class CategoryViewSet(ModelViewSet):
    """Вьюсет категорий.

    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (SearchFilter,)
    search_fields = ('name',)

    @action(detail=False,
            methods=['delete'],
            url_path=r'(?P<slug>\w+)',
            lookup_field='slug'
            )
    def delete_category(self, request, slug):
        category: Category = self.get_object()
        serializer = CategorySerializer(category)
        category.delete()

        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'list':
            return (AllowAny(),)

        return super().get_permissions()


class TitleViewSet(ModelViewSet):
    """Вьюсет произведений.

    """
    queryset = Title.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TitleFilterSet

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return TitleSerializer
        return TitleCreateSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return (AllowAny(),)

        return super().get_permissions()


class ReviewViewSet(ModelViewSet):
    """ViewSet для отзывов.

    """
    serializer_class = ReviewSerializer
    permission_classes = (ReviewViewSetPermission,)

    def get_queryset(self):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id')
        )
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id')
        )
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(ModelViewSet):
    """ViewSet для комментария.

    """
    serializer_class = CommentSerializer
    permission_classes = (CommentViewSetPermission,)

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id')
        )
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id')
        )
        serializer.save(author=self.request.user, review=review)
