from django.contrib import admin
from .models import *

class SessionAdmin(admin.ModelAdmin):
    list_display = ('opening_time', 'closing_time', 'weight', 'comment')
    list_editable = ('weight', 'comment')

admin.site.register(Session, SessionAdmin)
