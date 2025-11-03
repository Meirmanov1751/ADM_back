from django.contrib import admin
from .models import Request, ASCCover, ASCFiles, City, Region, RequestCategory, UserGroup

class ASCCoverInline(admin.StackedInline):
    model = ASCCover
    extra = 1


class ASCFilesInline(admin.StackedInline):
    model = ASCFiles
    extra = 1

admin.site.register(Region)
admin.site.register(City)
admin.site.register(RequestCategory)

# Register your models here.
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    inlines = [ASCCoverInline, ASCFilesInline]

@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ['regions', 'cities', 'categories', 'users']
    list_display = ['name']