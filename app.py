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
    opzioni_html = ""
    for i, nome in enumerate(partecipanti, start=1):
        opzioni_html += f'<div class="candidate"><label><input type="radio" name="voto" value="{i}" required /> {i} - {nome}</label></div>'

    return render_template_string("""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Talent Voting</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 650px;
      margin: 40px auto;
      padding: 20px;
      background: #f7f7f7;
    }
    .box {
      background: white;
      padding: 24px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    label {
      display: block;
      margin: 12px 0 6px;
      font-weight: bold;
    }
    input {
      width: 100%;
      padding: 10px;
      box-sizing: border-box;
      border: 1px solid #ccc;
      border-radius: 8px;
      font-size: 16px;
    }
    button {
      margin-top: 16px;
      padding: 10px 18px;
      border: none;
      border-radius: 8px;
      background: #4a67ff;
      color: white;
      font-size: 16px;
      cursor: pointer;
    }
    button:hover {
      background: #3a55e0;
    }
    #voto-sezione {
      display: none;
      margin-top: 20px;
    }
    .candidate {
      margin: 8px 0;
      padding: 8px 0;
    }
    #errore {
      color: #c00;
      margin-top: 12px;
      display: none;
    }
    #feedback {
      margin-top: 12px;
    }
  </style>
</head>
<body>
  <div class="box">
    <h1>Talent Show - Vota</h1>

    <div id="login">
      <label for="codice">Inserisci il tuo codice</label>
      <input type="text" id="codice" autocomplete="off" autofocus />
      <button onclick="login()">Accedi</button>
      <p id="errore"></p>
    </div>

    <div id="voto-sezione">
      <h2>Codice valido. Scegli il tuo preferito:</h2>
      <form id="form-voto">
        {{ opzioni_html|safe }}
        <button type="submit">Vota</button>
      </form>
      <p id="feedback"></p>
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
      const voto = document.querySelector('input[name="voto"]:checked').value;

      fetch("/vota", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codice: codiceValido, voto })
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
""", opzioni_html=opzioni_html)

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
      <title>Classifica</title>
      <style>
        body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; }}
        th {{ background: #f0f0f0; }}
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
