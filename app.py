from flask import Flask, render_template_string, request, jsonify
import csv

app = Flask(__name__)

# Carica lista partecipanti
with open("partecipanti.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    partecipanti = [row for row in reader]

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <title>Talent Voting</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; }
    label { display: block; margin: 10px 0 5px; }
    input { width: 100%; padding: 8px; margin-bottom: 10px; box-sizing: border-box; }
    button { padding: 10px 20px; }
    #voto-sezione { display: none; margin-top: 20px; }
  </style>
</head>
<body>
  <h1>Talent Show – Vota il vincitore</h1>
  <div id="login">
    <label>Nome</label>
    <input type="text" id="nome" autofocus />
    <label>Cognome</label>
    <input type="text" id="cognome" />
    <button onclick="login()">Accedi</button>
    <p id="errore" style="color: red; display: none;"></p>
  </div>

  <div id="voto-sezione">
    <h2>Ciao <span id="benvenuto"></span>, scegli il tuo preferito:</h2>
    <form id="form-voto">
      <label><input type="radio" name="voto" value="1" required /> 1 – Primo Finalista</label><br/>
      <label><input type="radio" name="voto" value="2" required /> 2 – Secondo Finalista</label><br/>
      <label><input type="radio" name="voto" value="3" required /> 3 – Terzo Finalista</label><br/>
      <label><input type="radio" name="voto" value="4" required /> 4 – Quarto Finalista</label><br/>
      <label><input type="radio" name="voto" value="5" required /> 5 – Quinto Finalista</label><br/>
      <button type="submit">Vota</button>
    </form>
    <p id="feedback"></p>
  </div>

  <script>
    let nomeInLista = null;

    function login() {
      const nome = document.getElementById("nome").value.trim();
      const cognome = document.getElementById("cognome").value.trim();
      document.getElementById("errore").style.display = "none";

      if (!nome || !cognome) {
        document.getElementById("errore").textContent = "Scrivi nome e cognome.";
        document.getElementById("errore").style.display = "block";
        return;
      }

      fetch("/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, cognome })
      })
      .then(r => r.json())
      .then(data => {
        if (data.allowed) {
          nomeInLista = data.nome;
          document.getElementById("login").style.display = "none";
          document.getElementById("benvenuto").textContent = nomeInLista;
          document.getElementById("voto-sezione").style.display = "block";
        } else {
          document.getElementById("errore").textContent = "Errore: non sei nella lista o hai sbagliato nome/cognome.";
          document.getElementById("errore").style.display = "block";
        }
      })
      .catch(() => {
        document.getElementById("errore").textContent = "Errore di rete.";
        document.getElementById("errore").style.display = "block";
      });
    }

    document.getElementById("form-voto").addEventListener("submit", function(e) {
      e.preventDefault();
      const voto = document.querySelector('input[name="voto"]:checked').value;

      fetch("/vota", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome: nomeInLista, voto })
      })
      .then(r => r.json())
      .then(data => {
        document.getElementById("feedback").textContent = data.message;
        document.getElementById("feedback").style.color = data.success ? "green" : "red";
      });
    });
  </script>
</body>
</html>
""")

@app.route("/check", methods=["POST"])
def check():
    dati = request.get_json()
    nome = dati.get("nome", "").strip()
    cognome = dati.get("cognome", "").strip()

    for p in partecipanti:
        if p["nome"].strip().lower() == nome.lower() and p["cognome"].strip().lower() == cognome.lower():
            return jsonify({"allowed": True, "nome": p["nome"] + " " + p["cognome"]})

    return jsonify({"allowed": False})

# Qui puoi salvare i voti in un file CSV (es. voti.csv)
voti = []

@app.route("/vota", methods=["POST"])
def vota():
    dati = request.get_json()
    nome = dati.get("voto", "")
    voto = dati.get("voto", "")

    # salva il voto (da migliorare con logica contro doppi voti, se vuoi)
    voti.append({"nome": nome, "voto": voto})
    return jsonify({"success": True, "message": "Voto registrato! Grazie!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
