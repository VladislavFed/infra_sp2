from django.urls import path, include

from rest_framework.routers import SimpleRouter

from api.views import (
    CategoryViewSet,
    CommentViewSet,
    CustomTokenObtainPairView,
    GenreViewSet,
    ReviewViewSet,
    SignUpAPIView,
    TitleViewSet,
    UsersViewSet,
)

app_name = 'api'

router_v1 = SimpleRouter()

router_v1.register(
    r'users',
    UsersViewSet,
    basename='user'
)
router_v1.register(
    r'titles',
    TitleViewSet,
    basename='title'
)
router_v1.register(
    r'genres',
    GenreViewSet,
    basename='genre'
)
router_v1.register(
    r'categories',
    CategoryViewSet,
    basename='category'
)
router_v1.register(
    r'titles/(?P<title_id>[1-9]\d*)/reviews',
    ReviewViewSet,
    basename='review'
)
router_v1.register(
    r'titles/(?P<title_id>[1-9]\d*)/reviews/(?P<review_id>[1-9]\d*)/comments',
    CommentViewSet,
    basename='comment'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename=r'reviews'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename=r'comments',
)

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path(
        'v1/auth/signup/',
        SignUpAPIView.as_view(),
        name='signup'
    ),
    path(
        'v1/auth/token/',
        CustomTokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
]
