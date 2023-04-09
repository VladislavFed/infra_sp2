from django.contrib import admin

from reviews.models import (
    Category,
    Comment,
    Genre,
    Review,
    Title,
    TitleGenre,
    User,
)


class TitleGenreInline(admin.TabularInline):
    model = TitleGenre


class ReviewInline(admin.TabularInline):
    model = Review


class CommentInline(admin.TabularInline):
    model = Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    inlines = (TitleGenreInline,)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'score', 'title', 'author', 'pub_date', )
    search_fields = ('text', 'author', )
    list_filter = ('pub_date', 'score', 'author', 'title', )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'review', 'author', 'pub_date', )
    search_fields = ('text', 'author', )
    list_filter = ('pub_date', 'author', )
