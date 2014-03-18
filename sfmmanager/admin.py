from django.contrib import admin

from sfmmanager.models import Video

class VideoAdmin(admin.ModelAdmin):

    fields = ['vname']

admin.site.register(Video, VideoAdmin)
