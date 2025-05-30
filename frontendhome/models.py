from django.db import models
from django.contrib.auth.models import User

class SelectedRepository(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='selected_repo')
    repo_full_name = models.CharField(max_length=255)  # e.g. "username/reponame"
    saved_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.repo_full_name}"

# model for auto settings page
class AutoPushSettings(models.Model):
    # Each user has one settings record
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='auto_push_settings')

    # Schedule tab
    frequency = models.CharField(max_length=20, default='daily')  # fixed daily
    codes_per_day = models.PositiveSmallIntegerField()
    push_time = models.CharField(max_length=5, help_text="HH:MM format")
    auto_push_duration = models.PositiveSmallIntegerField(help_text="Duration in days (3 to 7)")

    # Code type tab
    code_type = models.CharField(max_length=50)

    code_complexity = models.PositiveSmallIntegerField(help_text="1 (simple) to 100 (complex)")

    code_style = models.CharField(max_length=50)

    # Preferences tab
    default_commit_msg = models.CharField(max_length=255)
    preferred_language = models.CharField(max_length=50)
    preferred_framework = models.CharField(max_length=50)
    comment_style = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AutoPushSettings for {self.user.username}"
    
# model for auto push toggle
class AutoPushToggle(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='auto_push_toggle')
    is_enabled = models.BooleanField(default=False)  # Toggle state: on (True) / off (False)
    updated_at = models.DateTimeField(auto_now=True)  # Track when the toggle state was last changed

    def __str__(self):
        return f"Auto Push {'Enabled' if self.is_enabled else 'Disabled'} for {self.user.username}"

