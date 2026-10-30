![Dynamic Portfolio with Django: home page in a dark theme, with a name, statistics and a code block](assets/portfolio-django-home-desktop.png)

# 🌊 Dynamic Portfolio with Django | Educational Portfolio Template

[Português (Brasil)](README.md) · **English**

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)
![deps](https://img.shields.io/badge/deps-uv-DE5FE9)
[![CI](https://github.com/ryanvmorais/django-fullstack-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/ryanvmorais/django-fullstack-portfolio/actions/workflows/ci.yml)
![Lint](https://img.shields.io/badge/lint-ruff-261230)
![Format](https://img.shields.io/badge/style-black-000000)
![Types](https://img.shields.io/badge/types-mypy%20strict-2A6DB2)
![License](https://img.shields.io/badge/license-MIT-green)

🔗 **[See the live demo](https://djangofullstackportfolio.pythonanywhere.com/)** (the site itself is in Portuguese)

This repository holds a **Dynamic Portfolio with Django**, a professional portfolio built as an educational template. Although it looks like a *SPA* (Single Page Application), the project was built as a robust system, focused on **advanced security**, **database optimization** and **clean architecture**.

### 🎯 Project Goal:

To show **professional good practices** in web development, going beyond the "basic CRUD". The focus here is a real example of an application ready for the internet, teaching how to protect against bots, avoid common attacks and optimize database performance in a simple, didactic way.

---

### 📚 What will you learn from this project?

This project was structured to consolidate core pillars of software engineering:

- **Offensive and Defensive Security:** a *Honeypot* (a trap for bots), a *Rate Limit* (a cap on submissions per IP) and `bleach` to sanitize HTML.
- **Performance & Scale:** `select_related` and `prefetch_related` to avoid the N+1 query problem, so pages load instantly.
- **DevOps Mindset:** dependencies locked in a `uv.lock` (runtime, `dev` group and `prod` extra) with a 7-day quarantine against freshly published versions, `pip-audit` in CI and every Monday, Dependabot, plus strict CSP (Content Security Policy) and HSTS settings.
- **Audited Interface:** the home page was checked in a real Chrome (10 phone sizes, axe-core, keyboard, form) and fixed with one test per requirement: a hero that fits the first phone screen, a form that tells the visitor about any server response, an accessible menu, contrast, "reduce motion", fonts hosted in the project and custom error pages (spec 004).
- **Code Quality:** an automated `pytest` suite covering success flows and attack attempts.

---

### 🧠 Implementation Guide (The Logic behind the Code):

For beginners, the biggest challenge is not memorizing Django commands, but understanding how the **reasoning** of a professional application is put together. Here are the pillars of this project:

1. **Relational Data Architecture:** instead of loose text, we use the **Django ORM** to build smart relationships. For example, a `Projeto` (project) is linked to a `Categoria` (category) and to several `Tecnologias` (technologies). That lets the database work for you, making filters and searches easier.
2. **Query Optimization (Performance):** to keep the site from slowing down, we use a "senior trick": `select_related` and `prefetch_related`. They cut the number of trips to the database by fetching everything needed in a single one, which is crucial for **High Performance**.
3. **Defensive Security (Honeypot):** to protect the contact form without annoying CAPTCHAs, we set an "invisible trap". It is a hidden field that humans never see but bots fill in automatically. If the field is filled, the system spots the bot and silently drops the submission.
4. **Flow Control (Rate Limiting):** to stop spam attacks (thousands of e-mails per second), we put a lock in the cache. The system watches the user's IP and, after a successful submission, blocks new attempts for 10 minutes, protecting the integrity of your mail server.
5. **Content Sanitization:** we never trust what the user types. We use the `bleach` library to "clean" incoming messages, so any attempt to inject malicious scripts (XSS attacks) is neutralized before it even reaches the database.
6. **Browser Shielding (CSP):** we set up the *Content Security Policy*. It works like a guard at the site's door telling the browser: "only run scripts that come from this very server". That stops attackers from injecting external code into your front-end.
7. **Dynamic Skills:** the system gives you full control over the skills progress bar. In the Admin Panel, you set the percentage (0 to 100) for each technology. If you prefer not to show the progress bar, just untick the `Exibir barras de progresso` option ("Show progress bars") in your Profile in the Admin Panel and save.
8. **Slugs in Categories:** each `CategoriaProjeto` (project category) has a unique *Slug* (e.g. `web`, `api`), a short, readable identifier. The projects section filter uses that value to show and hide the cards without reloading the page.
9. **Real Production Environment:** the project does not only run on your computer. It was structured with environment variables (`.env`) and server-specific settings (such as `WhiteNoise` for static files), so deploying to platforms like **PythonAnywhere** is smooth and safe.

---

### 🛠️ Technologies and Tools:

To give you the best learning experience, the project uses the following technologies:

| Tool | Description |
| :--- | :--- |
| **Python 3.12+** | The base language, focused on readability and efficiency on the back end. |
| **Django 6.1** | The "batteries included" web framework, used for all the logic, the ORM and the admin panel. |
| **SQLite / PostgreSQL** | Relational database for safe persistence of the data. |
| **uv** | Dependency and virtual environment manager (replaces `pip`), with a reproducible lockfile. |
| **bleach** | Cleans the HTML of incoming messages, neutralizing script injection attempts (XSS). |
| **django-csp** | Applies the Content Security Policy, which tells the browser where scripts and styles may come from. |
| **Pillow** | Image library that converts the photos uploaded in the Admin to WebP, which loads faster. |
| **WhiteNoise** | Serves static files in production without needing Nginx or a CDN. |
| **Vanilla JS** | Plain JavaScript (ES6+) for light interactions, without the weight of heavy frameworks. |
| **HTML5/CSS3** | Semantic structure and modern styling based on Flexbox and Grid. |

The quality tools (Ruff, Black, Mypy and Pytest) are in [Quality and tests](#quality-and-tests). For the reasoning behind each choice, see [docs/stack.md](docs/stack.md) (in Portuguese).

---

### ⚙️ How to run the project locally:

**Prerequisites:** [Python 3.12+](https://www.python.org/downloads/) and [uv](https://docs.astral.sh/uv/getting-started/installation/), which creates and manages the virtual environment for you. To check, run `python --version` and `uv --version`.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ryanvmorais/django-fullstack-portfolio.git
    cd django-fullstack-portfolio
    ```
2.  **Set up the environment variables:** copy the `.env.example` file to `.env` and fill in your keys (`SECRET_KEY`, `EMAIL_USER`, etc.).
    ```bash
    # Linux and macOS
    cp .env.example .env

    # Windows (PowerShell)
    Copy-Item .env.example .env
    ```
3.  **Install the dependencies:**
    ```bash
    uv sync
    ```
4.  **Create the database tables:**
    ```bash
    uv run python manage.py migrate
    ```
5.  **Create the Admin superuser:**
    ```bash
    uv run python manage.py createsuperuser
    ```
6.  **Start the server:**
    ```bash
    uv run python manage.py runserver
    ```
7.  **Add the content in the Admin:** profile, projects, skills and statistics are added at `/admin/` (or the path set in `ADMIN_URL` in `.env`) with the superuser created above. Without that, the home page opens empty. Just want to see the home page filled in? With `DEBUG=True` in `.env`, `uv run python manage.py semear_dados_demo` creates a fictional profile, projects, skills and statistics (without duplicates if you run it again).

> ⚠️ **Note on the Contact Form:** for e-mail sending to work, you will need a Google **"App Password"** (if you use Gmail). Do not use your regular login password; Google blocks that connection for security. Set it up in *Security > 2-Step Verification > App passwords*.

---

### Quality and tests

The project runs an automated test suite (`pytest`) and a quality gate before any commit:

```bash
# Lint and import order
uv run ruff check .

# Check the formatting, without rewriting files
uv run black --check .

# Type checking
uv run mypy app_portfolio portfolio

# Tests
uv run pytest
```

The same gate runs automatically in CI (`.github/workflows/ci.yml`) on every push and every PR, together with a security check (`pip-audit` + `manage.py check --deploy`). `pip-audit` also runs every Monday (`.github/workflows/pip-audit.yml`), CodeQL (`.github/workflows/codeql.yml`) scans the code for security flaws and Lighthouse CI (`.github/workflows/lighthouse.yml`) audits the home page on mobile and desktop. To see the test coverage, run `uv run pytest --cov=app_portfolio --cov-report=term-missing`. For the map of each technology in the stack (what it is, why it was chosen, what to study), see [docs/stack.md](docs/stack.md). For the specification of each feature, see [specs/](specs/). For the exhaustive detail on architecture and conventions, see [CLAUDE.md](CLAUDE.md). These three are in Portuguese.

---

### 📋 Activities to practice (Evolution Challenges):

To exercise what you learned and master Django, try to build these new features:

1. **📊 Statistics Dashboard (Custom Admin):** in the Django Admin, build a view that shows how many e-mails were received per day.
   - **What you learn:** you will learn to work with `admin.ModelAdmin` and with database aggregations (`Count`, `Sum`).
2. **🌓 Theme Switcher (Dark/Light Mode):** add a front-end button that switches between the current theme and a light version of the site, saving the preference in the browser's `localStorage`.
   - **What you learn:** strengthens your command of **DOM manipulation with Vanilla JS** and of CSS variables (*Design Tokens*).
3. **✉️ Push or Telegram Notifications:** change the contact function so that, besides sending an e-mail, it sends a notification to a Telegram bot or a Discord message whenever someone fills in the form.
   - **What you learn:** you will learn to integrate Django with **external APIs** using the `requests` library.
4. **📂 Server-side Project Search:** the category filter in the projects section runs only in the browser. Build a text search box that queries the server (using AJAX) and returns only the projects that match the title, the description or the technology.
   - **What you learn:** command of complex **Querysets** (`Q`, `icontains`) and of asynchronous communication between the front end and the back end.

---

### 🧭 Keep practicing:

This project is part of a Python study path. After this one, try:

- **[Culinary Blog in Django](https://github.com/ryanvmorais/django-blog-culinario):** domain modeling, authentication, a custom admin and security.
- **[webvigil](https://github.com/ryanvmorais/webvigil):** a web vulnerability scanner (DAST) in Python, to see security from the other side.

See all the projects and videos of the channel in [aprenda-com-ryan-morais](https://github.com/ryanvmorais/aprenda-com-ryan-morais).

---

### 💡 Any questions or suggestions?

Building robust, secure systems with Django involves many technical details, but I am here to help! If you found unexpected behavior in the code, had trouble with the environment settings or thought of an architectural improvement that would make this project even more didactic:

- **Open an [Issue](https://github.com/ryanvmorais/django-fullstack-portfolio/issues):** describe your question or suggestion. It is the best way to build a solid reference for the community and to help other developers who may have the same question.
- **Contribute code:** want to propose an improvement? See the step-by-step in [CONTRIBUTING.md](CONTRIBUTING.md).
- **Send me an e-mail:** if you prefer something more private, write to [**contato@ryanmorais.com.br**](mailto:contato@ryanmorais.com.br).

I will be very happy to follow your progress with the Django framework and to get your feedback to keep improving the quality of this study material! 🤝

---

### ⚖️ License

This project is under the **MIT License**. That means you can use, copy and modify the code freely, including in your own projects. For more details, see the [LICENSE](LICENSE) file.
