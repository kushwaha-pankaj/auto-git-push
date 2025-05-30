from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.http import JsonResponse
import json
import requests
from django.contrib import messages

from codepush.models import AutoPushBatch, GeneratedCodeHistory
from .models import SelectedRepository

from django.utils.dateparse import parse_time
from django.views.decorators.http import require_http_methods

from .models import AutoPushSettings
from datetime import datetime, timedelta

from .models import AutoPushToggle

from django.core.paginator import Paginator
from django.http import JsonResponse


# Create your views here.
def home(request):
    return render(request, "frontend/index.html")

@login_required
def load_push_history(request):
    try:
        page = int(request.GET.get('page', 1))
        items_per_page = 7

        push_history_qs = GeneratedCodeHistory.objects.filter(user=request.user).order_by('-pushed_at')
        paginator = Paginator(push_history_qs, items_per_page)
        push_history = paginator.get_page(page)

        data = [
            {
                'title': history.title,
                'files_count': history.files_count,
                'branch': history.branch,
                'repo_name': history.repo_name,
                'status': history.status,
                'pushed_at': history.pushed_at.strftime("%Y-%m-%d %H:%M:%S"),  # precise & comparable
            }
            for history in push_history
        ]

        return JsonResponse({
            'success': True,
            'push_history': data,
            'has_next': push_history.has_next()
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def profile(request):
    try:
        # Get GitHub social account data
        social_account = SocialAccount.objects.get(user=request.user, provider='github')
        github_data = social_account.extra_data
        
        # Initialize total_repos fallback with public_repos count only
        total_repos = github_data.get('public_repos', 0)
        
        # Attempt to get GitHub OAuth token to fetch private repos count
        try:
            token = SocialToken.objects.get(account=social_account).token
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            # Fetch authenticated user's info to get private repo count
            response = requests.get("https://api.github.com/user", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                public_repos = user_data.get('public_repos', 0)
                private_repos = user_data.get('total_private_repos', 0)
                total_repos = public_repos + private_repos
        except SocialToken.DoesNotExist:
            # No token available, fallback to public repos only
            pass
        except Exception as e:
            # Optional: Log error, fallback to public repos only
            pass

        # Get the selected repository for the user
        selected_repo = SelectedRepository.objects.filter(user=request.user).first()
        selected_repo_name = selected_repo.repo_full_name if selected_repo else None
        # Remove username from the selected repository name if present
        if selected_repo_name and '/' in selected_repo_name:
            selected_repo_name = selected_repo_name.split('/', 1)[1]

        # Fetch push settings for the user, or provide defaults if none
        push_settings_obj = AutoPushSettings.objects.filter(user=request.user).first()
        if push_settings_obj:
            push_settings = {
                'frequency': push_settings_obj.frequency,
                'codes_per_day': push_settings_obj.codes_per_day,
                'time': push_settings_obj.push_time,
                'auto_push_duration': push_settings_obj.auto_push_duration,
                'code_type': push_settings_obj.code_type,
                'complexity': push_settings_obj.code_complexity,
                'code_style': push_settings_obj.code_style,
                'default_commit_msg': push_settings_obj.default_commit_msg,
                'preferred_language': push_settings_obj.preferred_language,
                'preferred_framework': push_settings_obj.preferred_framework,
                'comment_style': push_settings_obj.comment_style,
                'created_at': push_settings_obj.created_at.strftime("%d %b %Y, %H:%M"),
                'updated_at': push_settings_obj.updated_at.strftime("%d %b %Y, %H:%M"),
            }
        else:
            push_settings = {
                'frequency': 'not set',
                'codes_per_day': 'not set',
                'time': 'not set',
                'auto_push_duration': 'not set',
                'code_type': 'not set',
                'complexity': 'not set',
                'code_style': 'not set',
                'default_commit_msg': 'not set',
                'preferred_language': 'not set',
                'preferred_framework': 'not set',
                'comment_style': 'not set',
                'created_at': 'not set',
                'updated_at': 'not set',
            }


        # Calculate next push time (example: tomorrow at push_time)
        if push_settings_obj and push_settings_obj.push_time:
            try:
                push_time_obj = datetime.strptime(push_settings_obj.push_time, "%H:%M").time()
                now = datetime.now()
                push_time_today = now.replace(hour=push_time_obj.hour, minute=push_time_obj.minute, second=0, microsecond=0)
                if push_time_today > now:
                    next_push = push_time_today.strftime("Today at %H:%M")
                else:
                    next_push = (push_time_today + timedelta(days=1)).strftime("Tomorrow at %H:%M")
            except ValueError:
                next_push = f"Tomorrow at {push_settings_obj.push_time}"
        else:
            next_push = "Tomorrow at 09:00"
        
        context = {
            'username': request.user.username,
            'email': request.user.email,
            'avatar_url': github_data.get('avatar_url'),
            'profile_url': github_data.get('html_url'),
            'name': github_data.get('name'),
            'location': github_data.get('location'),
            'public_repos': github_data.get('public_repos'),
            'total_repos': total_repos,
            'push_settings': push_settings_obj,
            'next_push': next_push,
            'selected_repo': selected_repo_name,
        }

    except SocialAccount.DoesNotExist:
        # Defaults when no social account
        context = {
            'username': None,
            'email': None,
            'avatar_url': None,
            'profile_url': None,
            'name': None,
            'location': None,
            'public_repos': None,
            'total_repos': None,
            'push_settings': {
                'frequency': 'daily',
                'time': '09:00',
                'code_type': 'feature',
                'complexity': 50,
            },
            'next_push': "Tomorrow at 09:00",
            'selected_repo': None,
        }

    return render(request, 'frontend/dashboard.html', context)

# API endpoint to get user info as JSON
@login_required
def user_info(request):
    try:
        social_account = SocialAccount.objects.get(user=request.user, provider='github')
        github_data = social_account.extra_data

        response_data = {
            'username': request.user.username,
            'email': request.user.email,
            'avatar_url': github_data.get('avatar_url'),
            'profile_url': github_data.get('html_url'),
            'name': github_data.get('name'),
            'location': github_data.get('location'),
            'public_repos': github_data.get('public_repos'),
        }
    except SocialAccount.DoesNotExist:
        response_data = {
            'username': None,
            'email': None,
            'avatar_url': None,
            'profile_url': None,
            'name': None,
            'location': None,
            'public_repos': None,
        }

    return JsonResponse(response_data)


@login_required
def repository_select_view(request):
    social_account = request.user.socialaccount_set.filter(provider='github').first()
    token = None
    if social_account:
        token_obj = social_account.socialtoken_set.first()
        token = token_obj.token if token_obj else None

    repos = []

    if token:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        # Fetch first 100 repos to include recent repos
        url = "https://api.github.com/user/repos?per_page=100"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos = response.json()
        else:
            repos = []
    else:
        github_username = request.user.username
        url = f"https://api.github.com/users/{github_username}/repos?per_page=100"
        response = requests.get(url)
        if response.status_code == 200:
            repos = response.json()
        else:
            repos = []

    context = {
        'repos': json.dumps(repos)
    }
    return render(request, 'frontend/repository.html', context)


@login_required
def save_selected_repo(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            repo_full_name = data.get("repo_full_name")

            if not repo_full_name:
                return JsonResponse({"success": False, "error": "No repository selected."})

            # Delete any existing selected repo for the user
            SelectedRepository.objects.filter(user=request.user).delete()

            # Save the new selected repo for the user
            SelectedRepository.objects.create(
                user=request.user,
                repo_full_name=repo_full_name
            )
            return JsonResponse({"success": True, "redirect_url": "/dashboard/"})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})


@login_required
def auto_settings_view(request):
    """
    Render the automatic push settings page with user's current settings pre-filled if any.
    """
    try:
        user_settings = AutoPushSettings.objects.filter(user=request.user).first()
    except AutoPushSettings.DoesNotExist:
        user_settings = None

    context = {
        'settings': user_settings,
    }
    return render(request, 'frontend/settings.html', context)


@login_required
@require_http_methods(["POST"])
def save_auto_settings(request):
    """
    Handle AJAX POST request to save automatic push settings.
    """
    try:
        data = json.loads(request.body)

        # Extract fields from JSON data
        frequency = data.get("frequency")
        codes_per_day = data.get("codes_per_day")
        push_time = data.get("push_time")
        auto_push_duration = data.get("auto_push_duration")
        code_type = data.get("code_type")
        code_complexity = data.get("code_complexity")
        code_style = data.get("code_style")
        default_commit_msg = data.get("default_commit_msg")
        preferred_language = data.get("preferred_language")
        preferred_framework = data.get("preferred_framework")
        comment_style = data.get("comment_style")

        errors = {}

        # Validate frequency (must be daily)
        if frequency != "daily":
            errors["frequency"] = "Frequency must be 'daily'."

        # Validate codes_per_day (integer 1-7)
        try:
            codes_per_day_int = int(codes_per_day)
            if not (1 <= codes_per_day_int <= 7):
                errors["codes_per_day"] = "Codes per day must be between 1 and 7."
        except (TypeError, ValueError):
            errors["codes_per_day"] = "Invalid number for codes per day."

        # Validate push_time
        if not isinstance(push_time, str) or not push_time:
            errors["push_time"] = "Push time must be a non-empty string."
        else:
            parsed_push_time = parse_time(push_time)
            if parsed_push_time is None:
                errors["push_time"] = "Invalid push time format."

        # Validate auto_push_duration (integer 3-7)
        try:
            auto_push_duration_int = int(auto_push_duration)
            if not (3 <= auto_push_duration_int <= 7):
                errors["auto_push_duration"] = "Auto-push duration must be between 3 and 7 days."
        except (TypeError, ValueError):
            errors["auto_push_duration"] = "Invalid auto-push duration."

        # Validate code_type
        allowed_code_types = {"practice", "leetcode", "feature", "daily-challenges"}
        if code_type not in allowed_code_types:
            errors["code_type"] = "Invalid code type."

        # Validate code_complexity (integer 1-100)
        try:
            code_complexity_int = int(code_complexity)
            if not (1 <= code_complexity_int <= 100):
                errors["code_complexity"] = "Code complexity must be between 1 and 100."
        except (TypeError, ValueError):
            errors["code_complexity"] = "Invalid code complexity."

        # Validate code_style
        allowed_code_styles = {"clean-simple", "performance-optimized", "creative-innovative"}
        if code_style not in allowed_code_styles:
            errors["code_style"] = "Invalid code style."

        # Validate default_commit_msg
        if not default_commit_msg or not default_commit_msg.strip():
            errors["default_commit_msg"] = "Default commit message cannot be empty."

        # Validate preferred_language
        allowed_languages = {"javascript", "typescript", "python", "java", "csharp"}
        if preferred_language not in allowed_languages:
            errors["preferred_language"] = "Invalid preferred language."

        # Validate preferred_framework
        allowed_frameworks = {"react", "vue", "angular", "nextjs", "express", "django"}
        if preferred_framework not in allowed_frameworks:
            errors["preferred_framework"] = "Invalid preferred framework."

        # Validate comment_style
        allowed_comment_styles = {"minimal", "standard", "detailed"}
        if comment_style not in allowed_comment_styles:
            errors["comment_style"] = "Invalid comment style."

        # Return validation errors if any
        if errors:
            print("Validation errors:", errors)  # Debug print
            return JsonResponse({"success": False, "error": "Validation failed.", "details": errors}, status=400)

        # Save or update user's settings
        obj, created = AutoPushSettings.objects.update_or_create(
            user=request.user,
            defaults={
                "frequency": frequency,
                "codes_per_day": codes_per_day_int,
                "push_time": parsed_push_time,
                "auto_push_duration": auto_push_duration_int,
                "code_type": code_type,
                "code_complexity": code_complexity_int,
                "code_style": code_style,
                "default_commit_msg": default_commit_msg.strip(),
                "preferred_language": preferred_language,
                "preferred_framework": preferred_framework,
                "comment_style": comment_style,
            },
        )

        return JsonResponse({"success": True, "redirect_url": "/dashboard/"})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON."}, status=400)
    except Exception as e:
        print(f"Unexpected error: {e}")  # Debug print
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    

@login_required
def get_auto_push_state(request):
    try:
        toggle, created = AutoPushToggle.objects.get_or_create(user=request.user)
        return JsonResponse({"success": True, "is_enabled": toggle.is_enabled})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
def update_auto_push_state(request):
    try:
        data = json.loads(request.body)
        is_enabled = data.get("is_enabled", False)

        toggle, created = AutoPushToggle.objects.get_or_create(user=request.user)
        toggle.is_enabled = is_enabled
        toggle.save()

        return JsonResponse({"success": True, "message": f"Auto Push {'Enabled' if is_enabled else 'Disabled'}."})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def get_push_progress(request):
    user = request.user
    batch = AutoPushBatch.objects.filter(user=user, is_active=True).order_by('-created_at').first()

    if not batch:
        return JsonResponse({'success': False, 'message': 'No active batch'})

    total = batch.remaining + batch.codequeue_set.filter(pushed=True).count()
    pushed = total - batch.remaining

    return JsonResponse({
        'success': True,
        'total': total,
        'pushed': pushed,
        'remaining': batch.remaining
    })