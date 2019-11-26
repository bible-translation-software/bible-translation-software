from .models import Book, Verse, UserProfile, Comment
from django.contrib import admin

class BookAdmin(admin.ModelAdmin):
    list_display = ('book_code', 'book_number', 'book_name', 'chapters')

admin.site.register(Book, BookAdmin)

class VerseAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'book', 'chapter_number', 'verse_number', 'translation_code')

admin.site.register(Verse, VerseAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'admin_image_tag')
    fields = ('user', 'profile_pic_url', 'admin_image_tag')
    readonly_fields = ('user', 'admin_image_tag', )

admin.site.register(UserProfile, UserProfileAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'comment_text', 'date_created', 'content_object')

admin.site.register(Comment, CommentAdmin)
