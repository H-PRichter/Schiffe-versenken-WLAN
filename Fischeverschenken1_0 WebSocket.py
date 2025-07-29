from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)

socketio = SocketIO(app)

def pruefe_ob_alle_versenkt(feld):
    for zeile in feld:
        if "S" in zeile:
            return False
    return True

def erstelle_leeres_feld():
    return [['' for _ in range(10)] for _ in range(10)]

def maskiere_feld(feld):
    """Nur getroffene oder verfehlte Felder zeigen – Schiffe verbergen."""
    return [['X' if z == 'X' else 'O' if z == 'O' else '' for z in zeile] for zeile in feld]

spieler1_feld = erstelle_leeres_feld()
spieler2_feld = erstelle_leeres_feld()

# Spielstatus-Variablen
spieler1_bereit = False
spieler2_bereit = False

aktueller_spieler = 1  # Spieler 1 beginnt

@app.route("/spieler1")
def spieler1():
    return render_template("spielfeld.html",
                           eigenes_feld=spieler1_feld,
                           gegner_feld=maskiere_feld(spieler2_feld),
                           editormodus=True,
                           spieler_nummer=1)

@app.route("/spieler2")
def spieler2():
    return render_template("spielfeld.html",
                           eigenes_feld=spieler2_feld,
                           gegner_feld=maskiere_feld(spieler1_feld),
                           editormodus=True,
                           spieler_nummer=2)

@app.route("/setze-schiff", methods=["POST"])
def setze_schiff():
    daten = request.get_json()
    x = daten["x"]
    y = daten["y"]
    laenge = daten["laenge"]
    richtung = daten["richtung"]
    spieler = daten["spieler"]

    if spieler == 1:
        feld = spieler1_feld
    else:
        feld = spieler2_feld

    for i in range(laenge):
        nx = x + i if richtung == "horizontal" else x
        ny = y if richtung == "horizontal" else y + i
        if 0 <= nx < 10 and 0 <= ny < 10:
            feld[ny][nx] = "S"

    if spieler1_bereit and spieler2_bereit:
        status = "startbereit"

    return jsonify({"status": status})

@app.route("/bereit", methods=["POST"])
def spieler_bereit():
    global spieler1_bereit, spieler2_bereit
    daten = request.get_json()
    if daten["spieler"] == 1:
        spieler1_bereit = True
    elif daten["spieler"] == 2:
        spieler2_bereit = True    
    spieler = daten.get("spieler")

    status = "wartet"
    if spieler1_bereit and spieler2_bereit:
        status = "startbereit"
        print("🎯 Beide Spieler sind bereit! Los geht’s!")

    return jsonify({"status": status})

@socketio.on("angriff")
def handle_angriff(daten):
    global aktueller_spieler
    x = daten["x"]
    y = daten["y"]
    spieler = daten["spieler"]

    if aktueller_spieler != spieler:
        emit("angriffErgebnis", {"status": "ungueltig"}, to=request.sid)
        return
    
    # Welches Feld ist das Ziel?
    ziel_feld = spieler2_feld if spieler == 1 else spieler1_feld

    zellwert = ziel_feld[y][x]
    if zellwert == "S":
        ziel_feld[y][x] = "X"  # Treffer markieren
        getroffen = True
    elif zellwert == "":
        ziel_feld[y][x] = "O"  # Wasser markieren
        getroffen = False
    else:
        emit("angriffErgebnis", {"status": "ungueltig"}, to=request.sid)
        return

    if not getroffen:
        # Nur wechseln, wenn daneben geschossen wurde
        aktueller_spieler = 2 if spieler == 1 else 1

    gewonnen = pruefe_ob_alle_versenkt(ziel_feld)

    emit("angriffErgebnis", {
        "status": "treffer" if getroffen else "verfehlt",
        "x": x,
        "y": y,
        "schuetze": spieler,
        "ziel": 2 if spieler == 1 else 1,
        "gewonnen": pruefe_ob_alle_versenkt(ziel_feld)
    }, broadcast=True)

@app.route("/eigenes-feld", methods=["GET"])
def eigenes_feld():
    spieler = int(request.args.get("spieler"))
    if spieler == 1:
        feld = spieler1_feld
    else:
        feld = spieler2_feld
    return jsonify(maskiere_feld(feld))

if __name__ == "__main__":
    print("🎯 Kann losgehen! Server läuft, schnallt euch an.")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

# nimm die angezeigte erste Adresse im TERMINAL 127.0.0 und hänge "/spieler1" an am Laptop
# nimm die zweite URL 192.168... und hänge "/spieler2" an am Handy