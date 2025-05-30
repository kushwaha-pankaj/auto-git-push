# 🚀 AutoGitHubPush

AutoGitHubPush is a smart automation tool built to keep your GitHub green — daily and effortlessly. It uses OpenAI to generate code and Celery workers to push it to your selected repository automatically based on your preferences. Ideal for developers who care about consistency, contribution streaks, and automated workflows.

![AutoGitHubPush Banner](https://autogithubpush.kushwahapankaj.com/static/logo-auto.png)

---

## 🌟 Features

- 🔐 GitHub OAuth Login using Django Allauth  
- ⚙️ Set your preferred language, framework, code style & complexity  
- 🧠 AI-powered code generation using OpenAI's GPT-4o  
- 🚀 Auto push to selected GitHub repository daily using Celery  
- 📦 Queue management with batch tracking  
- 📊 Live contribution graph and push history  
- ☕ Integrated Buy Me a Coffee support  
- 🌍 Deployed & tested on cPanel server  

---

## 🧠 Why AutoGitHubPush?

Keeping your GitHub profile active can be challenging. This project was created to:
- Automate the code-pushing workflow
- Improve developer visibility on GitHub
- Encourage daily contribution and consistency
- Showcase auto-generated, quality, and tested code
- Serve as a learning experiment in AI, automation, Celery, and deployment on shared hosting environments like cPanel

---

## 🛠️ Tech Stack

- **Frontend**: HTML, Bootstrap, Custom JavaScript  
- **Backend**: Django, Celery, Redis  
- **Authentication**: GitHub OAuth (via Allauth)  
- **Code Generator**: OpenAI GPT-4o  
- **Task Queue**: Celery  
- **Scheduler**: Celery Beat + Cron jobs  
- **Hosting**: cPanel Deployment  
- **Database**: SQLite (PostgreSQL optional)  
- **Monitoring**: Logging + Admin Panel  

---

## 🔧 Installation Guide

```bash
### 1. Clone the Repo

git clone https://github.com/kushwaha-pankaj/auto-git-push.git
cd auto-git-push

2. Create a Virtual Environment
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root folder:
# SECURITY
SECRET_KEY=your-django-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,autogithubpush.kushwahapankaj.com

# DATABASE
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# REDIS / CELERY
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# GITHUB AUTH
GITHUB_CLIENT_ID=your_client_id
GITHUB_SECRET=your_secret

# OPENAI
OPENAI_API_KEY=your_openai_api_key


5. Run Initial Setup
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput


6. Start the Development Server
python manage.py runserver


🔄 Celery & Redis Integration (For Production)
Start Redis (Make sure it’s running on your server)
Create a cron job on cPanel:
Celery Worker:
* * * * * source /home/youruser/virtualenv/yourdomain.com/3.8/bin/activate && cd /home/youruser/yourdomain.com && celery -A autogitpush worker --loglevel=info >> /home/youruser/logs/celery_worker.log 2>&1

Celery Beat:
* * * * * source /home/youruser/virtualenv/yourdomain.com/3.8/bin/activate && cd /home/youruser/yourdomain.com && celery -A autogitpush beat --loglevel=info >> /home/youruser/logs/celery_beat.log 2>&1


🌐 Live Demo
👉 https://autogithubpush.kushwahapankaj.com


💡 Future Features
GitHub Actions alternative to cron

Custom user-defined prompts

Email summaries / push reports

Bitbucket & GitLab support

Dark mode + more UI customization

☕ Support the Project
If you find this useful, consider buying me a coffee to support further development.
https://buymeacoffee.com/kushwahapankaj

👨‍💻 Author
Pankaj Kushwaha
💼 LinkedIn - https://www.linkedin.com/in/kushwahapankaj/
🌐 Portfolio - https://kushwahapankaj.com/

🧾 License
This project is licensed under the MIT License.
Feel free to use, modify, and contribute.

🤝 Contributing
Fork the repository

Create a new branch (git checkout -b feature/your-feature)

Commit your changes (git commit -am 'Add new feature')

Push to the branch (git push origin feature/your-feature)

Create a new Pull Request


Built with ❤️ and GPT-4o to automate what matters.

Let me know if you'd like it in downloadable form, saved to your project directory, or paired with a `LICENSE.md` or `CONTRIBUTING.md`.
