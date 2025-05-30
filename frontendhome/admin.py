from django.contrib import admin
from .models import SelectedRepository, AutoPushSettings, AutoPushToggle


admin.site.register(SelectedRepository)
admin.site.register(AutoPushSettings)
admin.site.register(AutoPushToggle)
