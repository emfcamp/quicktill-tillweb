from django.contrib import admin
from .models import *

class SessionAdmin(admin.ModelAdmin):
    list_display = ('opening_time', 'closing_time', 'weight', 'comment')
    list_editable = ('weight', 'comment')

admin.site.register(Session, SessionAdmin)

class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'path')

admin.site.register(Page, PageAdmin)

class DisplayPageAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_after', 'display_until', 'title')
    list_filter = ('priority', )

admin.site.register(DisplayPage, DisplayPageAdmin)
