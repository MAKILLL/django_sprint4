from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'text',
        'pub_date',
        'is_published',
        'created_at',
        'author_id',
        'category_id',
        'location_id'
    )
    search_fields = (
        'title',
        'id'
    )
    list_editable = (
        'is_published',
    )
    list_filter = (
        'pub_date',
        'is_published',
        'created_at',
        'author_id',
        'category_id',
        'location_id'
    )
    list_display_links = (
        'title',
    )


class PostInLine(admin.TabularInline):
    model = Post
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [PostInLine]
    list_display = (
        'id',
        'title',
        'description',
        'slug',
        'is_published',
        'created_at'
    )
    search_fields = (
        'title',
        'id'
    )
    list_editable = (
        'is_published',
    )
    list_filter = (
        'is_published',
        'created_at'
    )
    list_display_links = (
        'title',
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_published',
        'created_at'
    )
    search_fields = (
        'name',
        'id'
    )
    list_editable = (
        'is_published',
    )
    list_filter = (
        'is_published',
        'created_at'
    )
    list_display_links = (
        'name',
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'text',
        'is_published',
        'created_at',
        'post',
        'author',
    )
    search_fields = (
        'id',
        'created_at',
        'text',
        'post__title',
        'author__username',
    )
    list_editable = (
        'is_published',
    )
    list_filter = (
        'is_published',
        'author__username',
        'created_at',
    )
    list_display_links = (
        'text',
    )


admin.site.empty_value_display = 'Не задано'
