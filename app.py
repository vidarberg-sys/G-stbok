from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "guestbook-development-key"

DATA_FILE = Path(__file__).with_name("guestbook.json")
MAX_COMMENT_LENGTH = 500


def normalize_url(value):
    value = value.strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return "https://" + value


def get_domain_name(url):
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname.split(":")[0]
    except ValueError:
        return ""


def is_valid_url(value):
    if not value:
        return True
    parsed = urlparse(value)
    return bool(parsed.scheme in {"http", "https"} and parsed.netloc)


def load_entries():
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            entries = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    return entries if isinstance(entries, list) else []


def save_entries(entries):
    temporary_file = DATA_FILE.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(entries, file, ensure_ascii=False, indent=2)
        file.write("\n")
    temporary_file.replace(DATA_FILE)


@app.route("/", methods=["GET", "POST"])
def guestbook():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        website = normalize_url(request.form.get("website", "").strip())
        comment = request.form.get("comment", "").strip()

        errors = []
        if not name:
            errors.append("Skriv ditt namn.")
        if not comment:
            errors.append("Skriv ett meddelande.")
        elif len(comment) > MAX_COMMENT_LENGTH:
            errors.append(f"Meddelandet får vara högst {MAX_COMMENT_LENGTH} tecken.")
        if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
            errors.append("Skriv en giltig e-postadress eller lämna fältet tomt.")
        if website and not is_valid_url(website):
            errors.append("Skriv en giltig webbplatsadress eller lämna fältet tomt.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("home.html", entries=load_entries(), form_data=request.form)

        entry = {
            "name": name,
            "email": email,
            "website": website,
            "comment": comment,
            "time": datetime.now(timezone.utc).astimezone().isoformat(timespec="minutes"),
        }
        entries = load_entries()
        entries.insert(0, entry)
        save_entries(entries)
        flash("Ditt inlägg har sparats.", "success")
        return redirect(url_for("guestbook"))

    return render_template("home.html", entries=load_entries(), form_data={})


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
