import base64
import logging
import requests
from datetime import datetime
from celery import shared_task
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken
import openai

from codepush.models import GeneratedCodeHistory
from frontendhome.models import AutoPushSettings, AutoPushToggle, SelectedRepository

logger = logging.getLogger(__name__)

from django.conf import settings


# Initialize OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


@shared_task
def auto_push_code():
    logger.info("🚀 Starting auto-push task")
    summary_errors = []

    users = User.objects.all()

    for user in users:
        logger.info(f"👤 Checking user: {user.username}")
        print(f"👤 Checking user: {user.username}")

        try:
            toggle = AutoPushToggle.objects.get(user=user)
            if not toggle.is_enabled:
                logger.info(f"⚠️ Auto-push disabled for {user.username}")
                continue

            settings = AutoPushSettings.objects.get(user=user)

        except (AutoPushToggle.DoesNotExist, AutoPushSettings.DoesNotExist) as e:
            logger.warning(f"❌ Missing toggle or settings for {user.username}: {str(e)}")
            summary_errors.append(f"{user.username}: {str(e)}")
            continue

        # Time check
        # Parse the CharField to a time object
        
        time_str = settings.push_time.strip()

        # Handle both "HH:MM" and "HH:MM:SS"
        try:
            if len(time_str.split(':')) == 2:
                scheduled_time = datetime.strptime(time_str, "%H:%M").time()
            else:
                scheduled_time = datetime.strptime(time_str, "%H:%M:%S").time()
        except ValueError:
            logger.warning(f"Invalid time format: {time_str}")
            # skip or handle error

        now = datetime.now().time()

        # Compare only hour and minute
        if now.hour != scheduled_time.hour or now.minute != scheduled_time.minute:
            logger.info(f"⏰ Not push time for {user.username}. Now: {now.strftime('%H:%M')}, Scheduled: {scheduled_time.strftime('%H:%M')}")
            continue

        try:
            # GitHub Info
            social_account = SocialAccount.objects.get(user=user, provider='github')
            github_token = SocialToken.objects.get(account=social_account).token
            github_username = social_account.extra_data.get('login')
            selected_repo = SelectedRepository.objects.get(user=user).repo_full_name

        except Exception as e:
            error_msg = f"{user.username}: GitHub setup error — {str(e)}"
            logger.error(error_msg)
            summary_errors.append(error_msg)
            continue

        # Create prompt
        prompt = (
            f"Generate a {settings.code_type} in {settings.preferred_language} using {settings.preferred_framework}.\n"
            f"The code should have {settings.code_complexity}% complexity, follow {settings.code_style} style, "
            f"and only contain code with {settings.comment_style} comments.\n"
            f"Start with a title in the format: Title: ... and include nothing else."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            generated_code = response.choices[0].message.content

        except Exception as e:
            error_msg = f"{user.username}: OpenAI error — {str(e)}"
            logger.error(error_msg)
            summary_errors.append(error_msg)
            continue

        # Title & Filename
        title = generated_code.split('\n')[0].replace("Title:", "").strip()
        file_name = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        commit_message = f"{settings.default_commit_msg} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        encoded_content = base64.b64encode(generated_code.encode("utf-8")).decode("utf-8")

        # Push to GitHub
        github_api_url = f"https://api.github.com/repos/{selected_repo}/contents/{file_name}"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "message": commit_message,
            "content": encoded_content,
            "branch": "main",
        }

        try:
            response = requests.put(github_api_url, headers=headers, json=payload)
            status = 'pushed' if response.status_code in [200, 201] else 'failed'

            GeneratedCodeHistory.objects.create(
                user=user,
                title=title,
                prompt=prompt,
                generated_code=generated_code,
                repo_name=selected_repo,
                branch="main",
                status=status,
                pushed_at=datetime.now()
            )

            logger.info(f"✅ {user.username}: Code {status} successfully.")

        except Exception as e:
            error_msg = f"{user.username}: Push error — {str(e)}"
            logger.error(error_msg)
            summary_errors.append(error_msg)

    logger.info("✅ Auto-push task completed")
    return {"success": True, "errors": summary_errors}
