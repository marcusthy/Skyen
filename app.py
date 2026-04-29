from flask import Flask, render_template, redirect, session, url_for, request, flash, send_file, make_response, abort
from forms import RegisterForm, LoginForm
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "zip", "docx", "mp4", "mkv", "mp3"}
UPLOAD_DIR = "/var/www/marcus_files"

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = "hemmelig-nok"

def get_conn():
    return mysql.connector.connect(
        host="localhost",
        user="marcus",
        password="123AKA",
        database="marcus_db"
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        navn = form.name.data
        brukernavn = form.username.data
        passord_hash = generate_password_hash(form.password.data)
        adresse = form.address.data

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO brukere (navn, brukernavn, passord, adresse) VALUES (%s, %s, %s, %s)",
                (navn, brukernavn, passord_hash, adresse)
            )
            conn.commit()
            return redirect("/login")
        except mysql.connector.IntegrityError:
            form.username.errors.append("Brukernavnet er allerede i bruk")
        finally:
            cur.close()
            conn.close()

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        brukernavn = form.username.data
        passord = form.password.data

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT bruker_id, navn, passord FROM brukere WHERE brukernavn=%s",
            (brukernavn,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            passord_db = user[2]
            if check_password_hash(passord_db, passord):
                session["bruker_id"] = user[0]
                session["navn"] = user[1]
                session["brukernavn"] = brukernavn
                return redirect("/welcome")
        form.username.errors.append("Feil brukernavn eller passord")

    return render_template("login.html", form=form)

@app.route("/welcome")
def welcome():
    navn = session.get("navn")
    if not navn:
        return redirect("/login")
    bruker_id = session.get("bruker_id")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT fil_id, filnavn, lastet_opp FROM filer WHERE bruker_id=%s ORDER BY lastet_opp DESC",
        (bruker_id,)
    )
    filer = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("welcome.html", name=navn, filer=filer)

@app.route("/upload", methods=["POST"])
def upload():
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")

    fil = request.files.get("fil")
    if not fil or fil.filename == "":
        flash("Ingen fil valgt.", "error")
        return redirect("/welcome")
    if not allowed_file(fil.filename):
        flash("Filtype ikke tillatt.", "error")
        return redirect("/welcome")

    original_filnavn = secure_filename(fil.filename)
    ext = original_filnavn.rsplit(".", 1)[1].lower() if "." in original_filnavn else ""
    unik_filnavn = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    filsti = os.path.join(UPLOAD_DIR, unik_filnavn)
    filtype = fil.content_type or "application/octet-stream"

    fil.save(filsti)
    filstorrelse = os.path.getsize(filsti)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO filer (bruker_id, filnavn, filtype, filsti, filstorrelse) VALUES (%s, %s, %s, %s, %s)",
        (bruker_id, original_filnavn, filtype, filsti, filstorrelse)
    )
    conn.commit()
    cur.close()
    conn.close()

    flash(f"{original_filnavn} ble lastet opp!", "success")
    return redirect("/welcome")

@app.route("/download/<int:fil_id>")
def download(fil_id):
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT filnavn, filtype, filsti FROM filer WHERE fil_id=%s AND bruker_id=%s",
        (fil_id, bruker_id)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[2] or not os.path.isfile(row[2]):
        flash("Filen ble ikke funnet.", "error")
        return redirect("/welcome")

    filnavn, filtype, filsti = row
    response = make_response()
    response.headers["Content-Type"] = filtype
    response.headers["Content-Disposition"] = f'attachment; filename="{filnavn}"'
    response.headers["X-Sendfile"] = filsti
    return response

IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}

@app.route("/bilder")
def bilder():
    if not session.get("bruker_id"):
        return redirect("/login")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT fil_id, filnavn, lastet_opp FROM filer WHERE bruker_id=%s AND filtype IN ('image/png','image/jpeg','image/gif','image/webp') ORDER BY lastet_opp DESC",
        (session["bruker_id"],)
    )
    bilder = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("gallery.html", bilder=bilder)

@app.route("/bilde/<int:fil_id>")
def vis_bilde(fil_id):
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT filnavn, filtype, filsti FROM filer WHERE fil_id=%s AND bruker_id=%s AND filtype IN ('image/png','image/jpeg','image/gif','image/webp')",
        (fil_id, bruker_id)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row or not row[2] or not os.path.isfile(row[2]):
        return redirect("/bilder")
    filnavn, filtype, filsti = row
    response = make_response()
    response.headers["Content-Type"] = filtype
    response.headers["X-Sendfile"] = filsti
    return response

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run()
