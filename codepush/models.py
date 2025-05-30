from django.db import models
from django.contrib.auth.models import User

class GeneratedCodeHistory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('pushed', 'Pushed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_histories')
    title = models.CharField(max_length=255)
    prompt = models.TextField()
    generated_code = models.TextField()
    files_count = models.PositiveIntegerField(null=True, blank=True)
    repo_name = models.CharField(max_length=255, null=True, blank=True)
    branch = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    pushed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pushed_at']

    def __str__(self):
        return f"{self.title} ({self.status}) - {self.user.username}"


class AutoPushBatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    remaining = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Batch for {self.user.username} | Active: {self.is_active} | Remaining: {self.remaining}"


class CodeQueue(models.Model):
    batch = models.ForeignKey(AutoPushBatch, on_delete=models.CASCADE, related_name='codequeue_set')
    title = models.CharField(max_length=255)
    prompt = models.TextField()
    generated_code = models.TextField()
    pushed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {'✅' if self.pushed else '❌'}"
