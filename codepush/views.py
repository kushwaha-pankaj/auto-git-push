import json
import openai
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialToken, SocialAccount
from django.conf import settings

from frontendhome.models import SelectedRepository
from .models import GeneratedCodeHistory
from datetime import datetime
import base64
from .tasks import auto_push_code
from django.conf import settings


# Initialize OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


@login_required
@require_POST
def generate_code(request):
    try:
        data = json.loads(request.body)
        prompt = data.get("prompt", "").strip()
        prompt = f"{prompt}\n\n# No explanations or additional text. Write the title of the code in the first line as Title: and then write the code. Just title in first line and then code\n\n"
        if not prompt:
            return JsonResponse({"success": False, "error": "Prompt is required."}, status=400)

        # Call OpenAI GPT-4o model
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        generated_code = completion.choices[0].message.content

        return JsonResponse({
            "success": True,
            "generated_code": generated_code,
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    
def determine_file_extension(generated_code):
    if "python" in generated_code.lower() or "def " in generated_code:
        return ".py"
    elif "javascript" in generated_code.lower() or "function " in generated_code:
        return ".js"
    elif "html" in generated_code.lower() or "<!DOCTYPE html>" in generated_code:
        return ".html"
    elif "css" in generated_code.lower() or "{ " in generated_code:
        return ".css"
    elif "java" in generated_code.lower() or "public class" in generated_code:
        return ".java"
    elif "c++" in generated_code.lower() or "#include" in generated_code:
        return ".cpp"
    elif "csharp" in generated_code.lower() or "namespace" in generated_code:
        return ".cs"
    elif "sql" in generated_code.lower() or "SELECT " in generated_code:
        return ".sql"
    elif "php" in generated_code.lower() or "<?php" in generated_code:
        return ".php"
    elif "json" in generated_code.lower() or "{" in generated_code and ":" in generated_code:
        return ".json"
    elif "yaml" in generated_code.lower() or "version: " in generated_code:
        return ".yaml"
    else:
        return ".txt"  # Default extension for unrecognized code

@login_required
@require_POST
def push_code_to_github(request):
    try:
        print("Start: push_code_to_github")

        # Extract data from the request
        data = json.loads(request.body)
        print(f"Data received from request: {data}")

        prompt = data.get("prompt", "")
        generated_code = data.get("generated_code", "")

        if not generated_code:
            print("Error: Generated code is missing")
            return JsonResponse({"success": False, "error": "Generated code is missing."}, status=400)

        # Extract the title from the first line of the generated code
        title = generated_code.split('\n')[0].strip("# ").strip()
        print(f"Extracted title: {title}")

        # Get the repository and branch information from user settings
        try:
            social_account = SocialAccount.objects.get(user=request.user, provider='github')
            print(f"Social account found: {social_account}")

            github_token = SocialToken.objects.get(account=social_account).token
            github_username = social_account.extra_data.get('login')
            print(f"GitHub username: {github_username}, Token: {github_token}")

            # Retrieve selected repository and branch from user settings
            selected_repo = SelectedRepository.objects.filter(user=request.user).first()
            if not selected_repo:
                print("Error: No repository selected by the user")
                return JsonResponse({"success": False, "error": "No repository selected."}, status=400)

            repo_name = selected_repo.repo_full_name.split('/', 1)[-1]
            print(f"Selected repository: {repo_name}")
            branch = "main"
            print(f"Repository name: {repo_name}, Branch: {branch}")

            # Increment file count
            files_count = GeneratedCodeHistory.objects.filter(user=request.user).count() + 1
            print(f"Files count for user: {files_count}")

            def determine_file_extension(generated_code):
                if "python" in generated_code.lower() or "def " in generated_code:
                    return ".py"
                elif "javascript" in generated_code.lower() or "function " in generated_code:
                    return ".js"
                elif "html" in generated_code.lower() or "<!DOCTYPE html>" in generated_code:
                    return ".html"
                elif "css" in generated_code.lower() or "{ " in generated_code:
                    return ".css"
                elif "java" in generated_code.lower() or "public class" in generated_code:
                    return ".java"
                elif "c++" in generated_code.lower() or "#include" in generated_code:
                    return ".cpp"
                elif "csharp" in generated_code.lower() or "namespace" in generated_code:
                    return ".cs"
                elif "sql" in generated_code.lower() or "SELECT " in generated_code:
                    return ".sql"
                elif "php" in generated_code.lower() or "<?php" in generated_code:
                    return ".php"
                elif "json" in generated_code.lower() or "{" in generated_code and ":" in generated_code:
                    return ".json"
                elif "yaml" in generated_code.lower() or "version: " in generated_code:
                    return ".yaml"
                else:
                    return ".txt"  # Default extension for unrecognized code

            file_extension = determine_file_extension(generated_code)
            print(f"Determined file extension: {file_extension}")

            # Construct file name
            file_name = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            commit_message = f"Add code: {title}"
            print(f"File name: {file_name}, Commit message: {commit_message}")

            # GitHub API URL to create/update a file
            github_api_url = f"https://api.github.com/repos/{github_username}/{repo_name}/contents/{file_name}"
            print(f"GitHub API URL: {github_api_url}")

            headers = {
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Encode the generated code as base64
            encoded_content = base64.b64encode(generated_code.encode('utf-8')).decode('utf-8')
            print(f"Encoded content length: {len(encoded_content)}")

            # Data for creating/updating the file
            data = {
                "message": commit_message,
                "content": encoded_content,
                "branch": branch,
            }
            print(f"Data for GitHub API: {data}")

            # Push the code to GitHub
            response = requests.put(github_api_url, headers=headers, json=data)
            print(f"GitHub API Response Status: {response.status_code}, Response Text: {response.text}")

            if response.status_code in [200, 201]:
                # Save to database after successful push
                generated_code_instance = GeneratedCodeHistory.objects.create(
                    user=request.user,
                    title=title,
                    prompt=prompt,
                    generated_code=generated_code,
                    files_count=files_count,
                    repo_name=repo_name,
                    branch=branch,
                    status='pushed',
                    pushed_at=datetime.now()
                )
                print(f"Code successfully pushed to GitHub. Saved to DB: {generated_code_instance}")
                return JsonResponse({"success": True, "message": "Code pushed to GitHub successfully."})
            else:
                # Log failure if push failed
                error_message = response.json().get("message", "Failed to push code")
                print(f"Error during GitHub push: {error_message}")
                GeneratedCodeHistory.objects.create(
                    user=request.user,
                    title=title,
                    prompt=prompt,
                    generated_code=generated_code,
                    files_count=files_count,
                    repo_name=repo_name,
                    branch=branch,
                    status='failed',
                    pushed_at=datetime.now()
                )
                return JsonResponse({"success": False, "error": f"GitHub Push Failed: {error_message}"})

        except SocialAccount.DoesNotExist:
            print("Error: GitHub account not linked")
            return JsonResponse({"success": False, "error": "GitHub account not linked."})

    except json.JSONDecodeError:
        print("Error: Invalid JSON received")
        return JsonResponse({"success": False, "error": "Invalid JSON."}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    
