from datetime import datetime, timezone
import json
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "guestbook-development-key"

DATA_FILE = Path(__file__).with_name("guestbook.json")
MAX_COMMENT_LENGTH = 500


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
    """Write valid JSON without leaving a half-written data file."""
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

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("home.html", entries=load_entries(), form_data=request.form)

        entry = {
            "name": name,
            "email": email,
            "comment": comment,
            "time": datetime.now(timezone.utc).astimezone().isoformat(timespec="minutes"),
        }
        entries = load_entries()
        entries.insert(0, entry)
        save_entries(entries)
        flash("Ditt inlägg har sparats.", "success")
        return redirect(url_for("guestbook"))

    return render_template("home.html", entries=load_entries(), form_data={})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
