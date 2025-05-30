from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from allauth.socialaccount.models import SocialToken, SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

@receiver(user_logged_in)
def save_github_token_on_login(sender, request, user, **kwargs):
    try:
        # Get user's GitHub social account
        social_account = SocialAccount.objects.get(user=user, provider=GitHubProvider.id)

        # Check if token already exists
        token = SocialToken.objects.filter(account=social_account).first()

        if not token:
            # If token missing, attempt to fetch from request (may not always be possible)
            # This requires you to access the OAuth2 token response which django-allauth doesn't expose here easily
            # So instead, you may want to force re-login or handle token saving elsewhere

            # For demonstration, just log info here:
            print(f"Token missing for user {user.username}. Please reconnect GitHub account.")

        else:
            # Token exists; optionally update timestamps or perform checks
            token.save()  # This is redundant but placeholder if you want to update something
            print(f"GitHub token verified for user {user.username}")

    except SocialAccount.DoesNotExist:
        print(f"No GitHub social account for user {user.username}")
