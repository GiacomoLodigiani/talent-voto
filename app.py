from flask import Flask, render_template_string, request, jsonify
import csv
import os

app = Flask(__name__)

with open("partecipanti.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    codici_validi = {row["codice"].strip() for row in reader if row.get("codice")}

voti = []

@app.route("/")
def index():
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
      max-width: 600px;
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
        <div class="candidate"><label><input type="radio" name="voto" value="1" required /> 1 - Primo Finalista</label></div>
        <div class="candidate"><label><input type="radio" name="voto" value="2" required /> 2 - Secondo Finalista</label></div>
        <div class="candidate"><label><input type="radio" name="voto" value="3" required /> 3 - Terzo Finalista</label></div>
        <div class="candidate"><label><input type="radio" name="voto" value="4" required /> 4 - Quarto Finalista</label></div>
        <div class="candidate"><label><input type="radio" name="voto" value="5" required /> 5 - Quinto Finalista</label></div>
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
          errore.textContent = "Codice non valido.";
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
""")

@app.route("/check", methods=["POST"])
def check():
    dati = request.get_json()
    codice = dati.get("codice", "").strip()

    if codice in codici_validi:
        return jsonify({"allowed": True})
    return jsonify({"allowed": False})

@app.route("/vota", methods=["POST"])
def vota():
    dati = request.get_json()
    codice = dati.get("codice", "").strip()
    voto = dati.get("voto", "").strip()

    if codice not in codici_validi:
        return jsonify({"success": False, "message": "Codice non valido."})

    voti.append({"codice": codice, "voto": voto})
    return jsonify({"success": True, "message": "Voto registrato con successo!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
