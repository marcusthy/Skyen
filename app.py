# --- Imports ---
from flask import Flask, render_template, redirect, session, url_for, request, flash, make_response
from forms import RegisterForm, LoginForm
from collections import OrderedDict
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mimetypes
import os
import uuid
import subprocess
import json
from datetime import datetime

# Pillow leser EXIF-data fra bilder – appen kjører uten EXIF-støtte hvis biblioteket mangler
try:
    from PIL import Image, ExifTags
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False


# --- Konstanter ---

# Tillatte filendelser ved opplasting
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "zip", "docx", "mp4", "mkv", "mov", "webm", "mp3"}

# Mappe på serveren der opplastede filer lagres
UPLOAD_DIR = "/var/www/marcus_files"

# MIME-typer som regnes som bilder og videoer (brukes i galleriet)
IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
VIDEO_TYPES = {"video/mp4", "video/x-matroska", "video/quicktime", "video/mpeg", "video/webm"}


# --- Hjelpefunksjoner ---

# Sjekker at et filnavn har en tillatt endelse
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Returnerer en ny tilkobling til MySQL-databasen
def get_conn():
    return mysql.connector.connect(
        host="localhost",
        user="marcus",
        password="123AKA",
        database="marcus_db"
    )


# --- App-oppsett ---

# Oppretter selve Flask-appen og setter hemmelig nøkkel for sesjons-/CSRF-håndtering
app = Flask(__name__)
app.secret_key = "hemmelig-nok"


# --- Ruter ---

# Forsiden – viser velkomstkortet med lenker til registrering/innlogging
@app.route("/")
def index():
    return render_template("index.html")


# Registrering av ny bruker (viser skjema på GET, lagrer i database på POST)
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    # Kjører kun når skjemaet er sendt inn og består validering (inkl. CSRF)
    if form.validate_on_submit():

        # Henter data fra skjemaet og hasher passordet før lagring
        navn = form.name.data
        brukernavn = form.username.data
        passord_hash = generate_password_hash(form.password.data)
        adresse = form.address.data

        # Setter inn brukeren i databasen med parameteriserte spørringer (unngår SQL-injection)
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
            # Slår til hvis brukernavnet allerede finnes (UNIQUE-felt i databasen)
            form.username.errors.append("Brukernavnet er allerede i bruk")
        finally:
            # Sørger for at databaseressurser alltid frigjøres
            cur.close()
            conn.close()

    # Viser skjemaet på nytt (med eventuelle feilmeldinger) på GET eller ugyldig POST
    return render_template("register.html", form=form)


# Innlogging – sjekker brukernavn/passord og oppretter sesjon
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        brukernavn = form.username.data
        passord = form.password.data

        # Henter brukeren fra databasen basert på brukernavn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT bruker_id, navn, passord FROM brukere WHERE brukernavn=%s",
            (brukernavn,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        # Sammenligner skrevet passord mot hashen i databasen
        if user:
            passord_db = user[2]
            if check_password_hash(passord_db, passord):
                # Lagrer bruker-info i sesjonen – brukes for å sjekke innlogging i andre ruter
                session["bruker_id"] = user[0]
                session["navn"] = user[1]
                session["brukernavn"] = brukernavn
                return redirect("/welcome")

        # Generisk feilmelding (avslører ikke om brukernavnet finnes eller ikke)
        form.username.errors.append("Feil brukernavn eller passord")

    return render_template("login.html", form=form)


# "Min side" – viser brukerens filer og opplastingsskjema
@app.route("/welcome")
def welcome():
    # Krever innlogging – sender ellers tilbake til login-siden
    navn = session.get("navn")
    if not navn:
        return redirect("/login")

    # Henter alle filer som tilhører den innloggede brukeren, nyeste først
    bruker_id = session.get("bruker_id")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT fil_id, filnavn, lastet_opp, filtype FROM filer WHERE bruker_id=%s ORDER BY lastet_opp DESC",
        (bruker_id,)
    )
    filer = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("welcome.html", name=navn, filer=filer)


# Tar imot opplastede filer, lagrer dem på disk og registrerer i databasen
@app.route("/upload", methods=["POST"])
def upload():
    # Krever innlogging
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")

    # Henter alle filer som ble sendt inn (støtter flere samtidig via multiple-attributtet)
    filer = request.files.getlist("fil")
    filer = [f for f in filer if f and f.filename]
    if not filer:
        flash("Ingen fil valgt.", "error")
        return redirect("/welcome")

    # Teller resultater så vi kan gi en samlet melding til brukeren
    opplastet = []
    avvist = []

    for fil in filer:
        if not allowed_file(fil.filename):
            avvist.append(fil.filename)
            continue

        # Genererer et unikt filnavn (UUID) på disk – beholder originalnavnet i databasen
        original_filnavn = secure_filename(fil.filename)
        ext = original_filnavn.rsplit(".", 1)[1].lower() if "." in original_filnavn else ""
        unik_filnavn = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
        filsti = os.path.join(UPLOAD_DIR, unik_filnavn)

        # Bruker mimetypes for pålitelig filtype-deteksjon – stoler ikke på nettleseren
        filtype, _ = mimetypes.guess_type(original_filnavn)
        filtype = filtype or "application/octet-stream"

        # Lagrer fila på disk og henter størrelsen
        fil.save(filsti)
        filstorrelse = os.path.getsize(filsti)

        # Forsøker å hente opprettet-dato fra metadata så galleriet kan sortere etter når bildet/videoen ble tatt
        exif_dato = None

        # Les EXIF-dato fra bilde hvis mulig
        if PILLOW_OK and filtype in IMAGE_TYPES:
            try:
                with Image.open(filsti) as img:
                    exif = img.getexif()
                    tag_navn = {v: k for k, v in ExifTags.TAGS.items()}
                    # Prioriter DateTimeOriginal (når bildet ble tatt), deretter DateTime
                    for felt in ("DateTimeOriginal", "DateTime"):
                        tag_id = tag_navn.get(felt)
                        if tag_id and tag_id in exif:
                            exif_dato = datetime.strptime(exif[tag_id], "%Y:%m:%d %H:%M:%S").date()
                            break
            except Exception:
                exif_dato = None

        # For videoer: bruker ffprobe til å lese ut creation_time fra container-metadata
        elif filtype in VIDEO_TYPES:
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", filsti],
                    capture_output=True, text=True, timeout=15
                )
                meta = json.loads(result.stdout)
                creation_time = meta.get("format", {}).get("tags", {}).get("creation_time")
                if creation_time:
                    # Format: "2024-03-15T14:22:00.000000Z" eller "2024-03-15 14:22:00"
                    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
                        try:
                            exif_dato = datetime.strptime(creation_time, fmt).date()
                            break
                        except ValueError:
                            continue
            except Exception:
                exif_dato = None

        # Lagrer metadata om fila i databasen
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO filer (bruker_id, filnavn, filtype, filsti, filstorrelse, exif_dato) VALUES (%s, %s, %s, %s, %s, %s)",
            (bruker_id, original_filnavn, filtype, filsti, filstorrelse, exif_dato)
        )
        conn.commit()
        cur.close()
        conn.close()

        opplastet.append(original_filnavn)

    # Bygger en samlet tilbakemelding til brukeren
    if opplastet:
        if len(opplastet) == 1:
            flash(f"{opplastet[0]} ble lastet opp!", "success")
        else:
            flash(f"{len(opplastet)} filer ble lastet opp.", "success")
    if avvist:
        flash(f"Avvist (filtype ikke tillatt): {', '.join(avvist)}", "error")

    return redirect("/welcome")


# Viser PDF inline i nettleseren (brukes av PDF-modalen)
# Bruker X-Sendfile slik at Apache leverer fila direkte
@app.route("/vis_pdf/<int:fil_id>")
def vis_pdf(fil_id):
    # Krever innlogging
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")

    # Henter PDF-fila kun hvis den tilhører den innloggede brukeren (hindrer at andre kan se den)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT filnavn, filtype, filsti FROM filer WHERE fil_id=%s AND bruker_id=%s AND filtype='application/pdf'",
        (fil_id, bruker_id)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    # Hvis fila ikke finnes (eller bruker ikke eier den) – gå tilbake til Min side
    if not row or not row[2] or not os.path.isfile(row[2]):
        return redirect("/welcome")

    # Bygger inline-respons. X-Sendfile lar Apache levere fila uten at Flask streamer den
    filnavn, filtype, filsti = row
    response = make_response()
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename="{filnavn}"'
    response.headers["X-Sendfile"] = filsti
    return response


# Nedlasting av en fil brukeren eier (sender Content-Disposition: attachment)
@app.route("/download/<int:fil_id>")
def download(fil_id):
    # Krever innlogging
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")

    # Slår opp fila og sjekker eierskap (forhindrer at en bruker laster ned andres filer)
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

    # Returnerer fila som vedlegg slik at nettleseren laster den ned
    filnavn, filtype, filsti = row
    response = make_response()
    response.headers["Content-Type"] = filtype
    response.headers["Content-Disposition"] = f'attachment; filename="{filnavn}"'
    response.headers["X-Sendfile"] = filsti
    return response


# Bildegalleri – henter alle bilder/videoer og grupperer dem etter måned
@app.route("/bilder")
def bilder():
    # Krever innlogging
    if not session.get("bruker_id"):
        return redirect("/login")

    # Henter alle bilder og videoer brukeren har lastet opp, sortert etter dato (EXIF hvis det finnes)
    conn = get_conn()
    cur = conn.cursor()
    media_types = tuple(IMAGE_TYPES | VIDEO_TYPES)
    params = (session["bruker_id"],) + media_types
    cur.execute(
        "SELECT fil_id, filnavn, lastet_opp, exif_dato, filtype FROM filer WHERE bruker_id=%s AND filtype IN ({}) ORDER BY COALESCE(exif_dato, DATE(lastet_opp)) DESC, lastet_opp DESC".format(",".join(["%s"] * len(media_types))),
        params
    )
    rader = cur.fetchall()
    cur.close()
    conn.close()

    # Grupperer etter måned – bruker EXIF-dato hvis den finnes, ellers opplastingsdato
    tidslinje = OrderedDict()
    for fil_id, filnavn, lastet_opp, exif_dato, filtype in rader:
        dato = exif_dato if exif_dato else lastet_opp.date()
        maaned_key = dato.strftime("%B %Y")
        if maaned_key not in tidslinje:
            tidslinje[maaned_key] = []
        er_video = filtype.startswith("video/")
        tidslinje[maaned_key].append((fil_id, filnavn, dato, exif_dato is not None, er_video))

    return render_template("gallery.html", tidslinje=tidslinje, total=sum(len(v) for v in tidslinje.values()))


# Streamer et enkelt bilde/video til galleriet (brukes av <img src> og lightbox)
@app.route("/bilde/<int:fil_id>")
def vis_bilde(fil_id):
    # Krever innlogging
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")

    # Henter bare media-filer (bilde/video) som tilhører brukeren
    conn = get_conn()
    cur = conn.cursor()
    media_types = tuple(IMAGE_TYPES | VIDEO_TYPES)
    params = (fil_id, bruker_id) + media_types
    cur.execute(
        "SELECT filnavn, filtype, filsti FROM filer WHERE fil_id=%s AND bruker_id=%s AND filtype IN ({})".format(",".join(["%s"] * len(media_types))),
        params
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[2] or not os.path.isfile(row[2]):
        return redirect("/bilder")

    # Sender mediefila inline med riktig Content-Type
    filnavn, filtype, filsti = row
    response = make_response()
    response.headers["Content-Type"] = filtype
    response.headers["X-Sendfile"] = filsti
    return response


# Sletter en fil – både rad i databasen og selve fila på disk
@app.route("/slett/<int:fil_id>", methods=["POST"])
def slett(fil_id):
    # Krever innlogging
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")

    # Slår opp filstien for fila brukeren eier
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT filsti FROM filer WHERE fil_id=%s AND bruker_id=%s",
        (fil_id, bruker_id)
    )
    row = cur.fetchone()
    if row:
        # Sletter raden først, deretter selve fila fra disk
        filsti = row[0]
        cur.execute("DELETE FROM filer WHERE fil_id=%s AND bruker_id=%s", (fil_id, bruker_id))
        conn.commit()
        if filsti and os.path.isfile(filsti):
            os.remove(filsti)
    cur.close()
    conn.close()

    return redirect("/bilder")


# Alle filer – viser liste over alle opplastede filer med tidsstempel
@app.route("/filer")
def alle_filer():
    bruker_id = session.get("bruker_id")
    if not bruker_id:
        return redirect("/login")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT fil_id, filnavn, filtype, filstorrelse, lastet_opp FROM filer WHERE bruker_id=%s ORDER BY lastet_opp DESC",
        (bruker_id,)
    )
    filer = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("filer.html", filer=filer)


# Logger ut brukeren ved å tømme sesjonen
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run()
