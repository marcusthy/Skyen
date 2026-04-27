from flask import Flask, render_template, redirect, session, url_for
from forms import RegisterForm, LoginForm
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

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
            "SELECT navn, passord FROM brukere WHERE brukernavn=%s",
            (brukernavn,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            passord_db = user[1]
            if check_password_hash(passord_db, passord):
                session["navn"] = user[0]
                return redirect("/welcome")
        form.username.errors.append("Feil brukernavn eller passord")

    return render_template("login.html", form=form)

@app.route("/welcome")
def welcome():
    navn = session.get("navn")
    if not navn:
        return redirect("/login")
    return render_template("welcome.html", name=navn)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run()
