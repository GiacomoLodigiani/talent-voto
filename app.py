from flask import Flask, render_template_string, request, jsonify, Response, abort
import csv
import os
import io
from datetime import datetime
from collections import Counter

app = Flask(__name__)

CODICI_FILE = "codici_autorizzati.csv"
PARTECIPANTI_FILE = "partecipanti.csv"
ADMIN_KEY = os.environ.get("ADMIN_KEY", "cambia-questa-chiave")

voti_memoria = []

def load_codici():
    if not os.path.exists(CODICI_FILE):
        return set()
    with open(CODICI_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["codice"].strip() for row in reader if row.get("codice")}

def load_partecipanti():
    if not os.path.exists(PARTECIPANTI_FILE):
        return []
    with open(PARTECIPANTI_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row["nome"].strip() for row in reader if row.get("nome")]

def has_voted(codice):
    codice = codice.strip()
    return any(voto["codice"] == codice for voto in voti_memoria)

def save_vote(codice, voto):
    voti_memoria.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "codice": codice,
        "voto": voto
    })

def votes_to_csv():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["timestamp", "codice", "voto"])
    writer.writeheader()
    writer.writerows(voti_memoria)
    return output.getvalue()

def leaderboard_top5():
    partecipanti = load_partecipanti()
    counter = Counter()
    for voto in voti_memoria:
        try:
            idx = int(voto["voto"]) - 1
            if 0 <= idx < len(partecipanti):
                counter[partecipanti[idx]] += 1
        except:
            pass
    return counter.most_common(5)

@app.route("/")
def index():
    partecipanti = load_partecipanti()
    cards_html = ""
    for i, nome in enumerate(partecipanti, start=1):
        cards_html += f"""
        <label class="vote-card">
          <div class="candidate-name">{nome}</div>
          <input type="radio" name="voto" value="{i}" required />
        </label>
        """

    return render_template_string("""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>Talent Voting</title>
  <style>
    * {
      box-sizing: border-box;
    }

    body {
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
      background: #f4f6fb;
      color: #111;
    }

    .container {
      max-width: 700px;
      margin: 0 auto;
      padding: 20px;
    }

    .box {
      background: white;
      border-radius: 18px;
      box-shadow: 0 4px 18px rgba(0,0,0,0.08);
      padding: 22px;
    }

    h1 {
      text-align: center;
      margin: 0 0 22px 0;
      font-size: 28px;
    }

    .subtitle {
      text-align: center;
      margin: 0 0 18px 0;
      color: #555;
      font-size: 16px;
    }

    label {
      display: block;
    }

    input[type="text"] {
      width: 100%;
      padding: 14px 14px;
      border: 1px solid #cfd6e4;
      border-radius: 12px;
      font-size: 18px;
      outline: none;
    }

    .btn {
      width: 100%;
      margin-top: 14px;
      padding: 14px 16px;
      border: none;
      border-radius: 12px;
      background: #355cff;
      color: white;
      font-size: 17px;
      font-weight: 600;
      cursor: pointer;
    }

    .btn:active {
      transform: scale(0.99);
    }

    #voto-sezione {
      display: none;
      margin-top: 18px;
    }

    .options {
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
      margin-top: 16px;
    }

    .vote-card {
      background: #f8f9fc;
      border: 1px solid #dde3ef;
      border-radius: 18px;
      padding: 18px 14px 16px 14px;
      text-align: center;
      cursor: pointer;
      transition: 0.15s ease;
    }

    .vote-card:hover {
      border-color: #b8c4df;
      background: #f1f4fb;
    }

    .candidate-name {
      font-size: 22px;
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 14px;
      text-align: center;
      word-break: break-word;
    }

    .vote-card input[type="radio"] {
      width: 26px;
      height: 26px;
      margin: 0 auto;
      display: block;
      accent-color: #355cff;
    }

    #errore {
      color: #c00;
      margin-top: 12px;
      display: none;
      text-align: center;
      font-weight: 600;
    }

    #feedback {
      margin-top: 14px;
      text-align: center;
      font-weight: 600;
    }

    .links {
      margin-top: 18px;
      text-align: center;
      font-size: 14px;
      color: #666;
    }

    .links a {
      color: #355cff;
      text-decoration: none;
      font-weight: 600;
    }

    .links a + a {
      margin-left: 14px;
    }

    @media (min-width: 700px) {
      .options {
        grid-template-columns: 1fr 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="box">
      <h1>Talent Show - Vota</h1>
      <p class="subtitle">Inserisci il codice, poi scegli il tuo preferito.</p>

      <div id="login">
        <input type="text" id="codice" placeholder="Inserisci il tuo codice" autocomplete="off" autofocus />
        <button class="btn" onclick="login()">Accedi</button>
        <p id="errore"></p>
      </div>

      <div id="voto-sezione">
        <h2 style="text-align:center; margin: 8px 0 0 0;">Codice valido. Scegli il tuo preferito:</h2>
        <form id="form-voto">
          <div class="options">
            {{ cards_html|safe }}
          </div>
          <button class="btn" type="submit" style="margin-top:18px;">Vota</button>
        </form>
        <p id="feedback"></p>
      </div>
    </div>
  </div>

  <script>
    let codiceValido = null;

    function login() {
      const codice = document.getElementById("codice").value.trim();
      const errore = document.getElementById("errore");
      errore.style.display = "none";
      errore.textContent = "";

      if (!codice) {
        errore.textContent = "Inserisci un codice.";
        errore.style.display = "block";
        return;
      }

      fetch("/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codice })
      })
      .then(r => r.json())
      .then(data => {
        if (data.allowed) {
          codiceValido = codice;
          document.getElementById("login").style.display = "none";
          document.getElementById("voto-sezione").style.display = "block";
        } else {
          errore.textContent = "Codice non valido o già usato.";
          errore.style.display = "block";
        }
      })
      .catch(() => {
        errore.textContent = "Errore di rete.";
        errore.style.display = "block";
      });
    }

    document.getElementById("form-voto").addEventListener("submit", function(e) {
      e.preventDefault();
      const scelta = document.querySelector('input[name="voto"]:checked');
      if (!scelta) return;

      fetch("/vota", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codice: codiceValido, voto: scelta.value })
      })
      .then(r => r.json())
      .then(data => {
        const feedback = document.getElementById("feedback");
        feedback.textContent = data.message;
        feedback.style.color = data.success ? "green" : "red";
        if (data.success) {
          document.getElementById("form-voto").reset();
        }
      })
      .catch(() => {
        const feedback = document.getElementById("feedback");
        feedback.textContent = "Errore di rete.";
        feedback.style.color = "red";
      });
    });
  </script>
</body>
</html>
""", cards_html=cards_html)

@app.route("/check", methods=["POST"])
def check():
    dati = request.get_json()
    codice = dati.get("codice", "").strip()
    codici_validi = load_codici()
    if codice in codici_validi and not has_voted(codice):
        return jsonify({"allowed": True})
    return jsonify({"allowed": False})

@app.route("/vota", methods=["POST"])
def vota():
    dati = request.get_json()
    codice = dati.get("codice", "").strip()
    voto = dati.get("voto", "").strip()
    codici_validi = load_codici()

    if codice not in codici_validi:
        return jsonify({"success": False, "message": "Codice non valido."})

    if has_voted(codice):
        return jsonify({"success": False, "message": "Hai già votato con questo codice."})

    save_vote(codice, voto)
    return jsonify({"success": True, "message": "Voto registrato con successo!"})

@app.route("/voti")
def voti():
    return jsonify(voti_memoria)

@app.route("/voti.csv")
def voti_csv():
    csv_data = votes_to_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=voti.csv"}
    )

@app.route("/admin/risultati")
def admin_risultati():
    key = request.args.get("key", "")
    if key != ADMIN_KEY:
        abort(403)

    top5 = leaderboard_top5()
    rows = "".join([f"<tr><td>{i+1}</td><td>{nome}</td><td>{voti}</td></tr>" for i, (nome, voti) in enumerate(top5)])

    return f"""
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Classifica</title>
      <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; padding: 20px; }}
        h1 {{ text-align:center; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 12px; text-align: left; }}
        th {{ background: #f0f3ff; }}
      </style>
    </head>
    <body>
      <h1>Classifica Top 5</h1>
      <table>
        <tr><th>Posizione</th><th>Partecipante</th><th>Voti</th></tr>
        {rows if rows else '<tr><td colspan="3">Nessun voto ancora</td></tr>'}
      </table>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
