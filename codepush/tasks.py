import base64
import random
import requests
from datetime import datetime
from celery import shared_task
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken
import openai

from codepush.models import GeneratedCodeHistory, AutoPushBatch, CodeQueue
from frontendhome.models import AutoPushSettings, AutoPushToggle, SelectedRepository
from django.conf import settings


# Initialize OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

@shared_task
def auto_push_code():
    print("🚀 Auto-push task started")

    for user in User.objects.filter(auto_push_toggle__is_enabled=True):
        try:
            print(f"\n👤 Checking user: {user.username}")
            settings = AutoPushSettings.objects.get(user=user)
            repo = SelectedRepository.objects.get(user=user)
            push_time = parse_time(settings.push_time)
            now = datetime.now().time()
            today = datetime.now().date()
            now_datetime = datetime.now()

            # Find latest batch
            latest_batch = AutoPushBatch.objects.filter(user=user).order_by('-created_at').first()

            # 🚨 If settings were updated AFTER last batch → reset everything
            if latest_batch and settings.updated_at > latest_batch.created_at:
                print(f"🔄 Detected settings update after batch. Resetting batches for {user.username}")
                AutoPushBatch.objects.filter(user=user).delete()
                CodeQueue.objects.filter(batch__user=user).delete()
                latest_batch = None  # clear reference

            # 🚫 Deactivate expired batches
            active_batches = AutoPushBatch.objects.filter(user=user, is_active=True)
            for batch in active_batches:
                if (today - batch.created_at.date()).days >= settings.auto_push_duration:
                    batch.is_active = False
                    batch.save()
                    print(f"🛑 Batch expired for {user.username}")

            # ⏰ Time check to create new batch
            batch_today_exists = AutoPushBatch.objects.filter(user=user, created_at__date=today).exists()
            time_diff = abs((datetime.combine(today, now) - datetime.combine(today, push_time)).total_seconds()) / 60

            if not batch_today_exists and time_diff <= 1:
                print(f"🆕 Creating today's batch for {user.username}")
                batch = AutoPushBatch.objects.create(user=user, is_active=True, remaining=settings.codes_per_day)

                for i in range(settings.codes_per_day):
                    prompt = build_unique_prompt(settings)
                    try:
                        code = call_openai(prompt)
                        title = extract_title(code)
                        CodeQueue.objects.create(
                            batch=batch,
                            title=title,
                            prompt=prompt,
                            generated_code=code
                        )
                        print(f"✅ Queued [{i+1}/{settings.codes_per_day}] for {user.username}")
                    except Exception as e:
                        print(f"❌ OpenAI error for {user.username}: {str(e)}")

            # 🚀 Push one code if any remain
            batch = AutoPushBatch.objects.filter(user=user, is_active=True).first()
            if batch and batch.remaining > 0:
                code_obj = batch.codequeue_set.filter(pushed=False).first()
                if code_obj:
                    push_to_github(user, code_obj.title, code_obj.prompt, code_obj.generated_code, repo.repo_full_name)
                    code_obj.pushed = True
                    code_obj.save()
                    batch.remaining -= 1
                    batch.save()
                    print(f"📤 Pushed: {code_obj.title} | Remaining: {batch.remaining}")

        except Exception as e:
            print(f"❌ General error for {user.username}: {str(e)}")

    print("✅ Auto-push task completed\n")

# --------------------------
# 🔧 Helper Functions
# --------------------------

def parse_time(time_str):
    time_str = time_str.strip()
    if len(time_str.split(':')) == 2:
        return datetime.strptime(time_str, "%H:%M").time()
    elif len(time_str.split(':')) == 3:
        return datetime.strptime(time_str, "%H:%M:%S").time()
    else:
        raise ValueError(f"Invalid push_time format: {time_str}")

def build_unique_prompt(settings):
    tasks = [
        "build a currency converter", "create a to-do list app with database support",
        "simulate a dice rolling game", "develop a weather API scraper",
        "construct a file compression tool", "generate and scan QR codes",
        "build a RESTful API", "merge multiple PDF files",
        "simulate a text-based RPG", "write a test coverage analyzer"
    ]
    constraints = [
        "write unit tests", "use modular design", "optimize for performance",
        "write type-annotated code", "add input validation",
        "follow MVC", "add logging", "handle errors gracefully",
        "support mobile-first", "include docstring comments"
    ]
    task = random.choice(tasks)
    constraint = random.choice(constraints)

    prompt_intro = f"Generate a {settings.code_type} in {settings.preferred_language} using {settings.preferred_framework}."

    return (
        f"{prompt_intro}\n"
        f"Task: {task}.\n"
        f"Additional constraint: {constraint}.\n"
        f"Complexity: {settings.code_complexity}%.\n"
        f"Style: {settings.code_style}. Comments: {settings.comment_style}.\n"
        f"Start with: Title: ... followed by only code and comments."
    )

def call_openai(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI API Error: {str(e)}")

def extract_title(code):
    return code.split('\n')[0].replace("Title:", "").strip()

def push_to_github(user, title, prompt, code, repo_name):
    try:
        social_account = SocialAccount.objects.get(user=user, provider='github')
        token = SocialToken.objects.get(account=social_account).token
        file_name = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        encoded = base64.b64encode(code.encode()).decode()
        url = f"https://api.github.com/repos/{repo_name}/contents/{file_name}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        payload = {
            "message": f"Auto-pushed: {title}",
            "content": encoded,
            "branch": "main"
        }

        response = requests.put(url, json=payload, headers=headers)
        status = 'pushed' if response.status_code in [200, 201] else 'failed'

        GeneratedCodeHistory.objects.create(
            user=user,
            title=title,
            prompt=prompt,
            generated_code=code,
            repo_name=repo_name,
            branch="main",
            status=status,
            files_count=GeneratedCodeHistory.objects.filter(user=user).count() + 1,
            pushed_at=datetime.now()
        )

        print(f"✅ GitHub push {status.upper()} → {file_name}")

    except Exception as e:
        raise Exception(f"GitHub Push Error: {str(e)}")
