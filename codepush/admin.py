from django.contrib import admin
from .models import GeneratedCodeHistory, AutoPushBatch, CodeQueue

admin.site.register(GeneratedCodeHistory)
admin.site.register(AutoPushBatch)
admin.site.register(CodeQueue)