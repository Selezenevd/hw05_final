from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"
    
admin.site.register(Post, PostAdmin)


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'slug', 'description')
    ordering = ['title']
    prepopulated_fields = {"slug": ("title",)}

admin.site.register(Group, GroupAdmin)


class CommentAdmin(admin.ModelAdmin):  
    list_display = ('post', 'author', 'text', 'created')  
    list_filter = ('created',)  
    search_fields = ('author', 'text')

admin.site.register(Comment, CommentAdmin)

class FollowAdmin(admin.ModelAdmin):  
    list_display = ('user', 'author')  

admin.site.register(Follow, FollowAdmin)
