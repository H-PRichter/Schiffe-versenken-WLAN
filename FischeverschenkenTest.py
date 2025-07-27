from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

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

    return jsonify({"status": "ok"})

@app.route("/bereit", methods=["POST"])
def spieler_bereit():
    global spieler1_bereit, spieler2_bereit
    daten = request.get_json()
    spieler = daten.get("spieler")

    if spieler == 1:
        spieler1_bereit = True
        print("👤 Spieler 1 ist bereit.")
    elif spieler == 2:
        spieler2_bereit = True
        print("👤 Spieler 2 ist bereit.")
    if spieler1_bereit and spieler2_bereit:
        print("🎯 Beide Spieler sind bereit! Los geht’s!")

    return jsonify({"status": "ok"})

@app.route("/angriff", methods=["POST"])
def angriff():
    global aktueller_spieler
    daten = request.get_json()
    x = daten["x"]
    y = daten["y"]
    spieler = daten["spieler"]

    # Welches Feld ist das Ziel?
    ziel_feld = spieler2_feld if spieler == 1 else spieler1_feld
    aktuelles_feld = spieler1_feld if spieler == 1 else spieler2_feld

    if aktueller_spieler != spieler:
        return jsonify({"status": "ungueltig"})

    zellwert = ziel_feld[y][x]
    if zellwert == "S":
        ziel_feld[y][x] = "X"  # Treffer markieren
        getroffen = True
    elif zellwert == "":
        ziel_feld[y][x] = "O"  # Wasser markieren
        getroffen = False
    else:
        return jsonify({"status": "ungueltig"})  # Feld war schon beschossen

    if not getroffen:
        # Nur wechseln, wenn daneben geschossen wurde
        aktueller_spieler = 2 if spieler == 1 else 1

    gewonnen = pruefe_ob_alle_versenkt(ziel_feld)

    return jsonify({
        "status": "treffer" if getroffen else "verfehlt",
        "x": x,
        "y": y,
        "gewonnen": gewonnen if getroffen else False
    })

@app.route("/eigenes-feld", methods=["GET"])
def eigenes_feld():
    spieler = int(request.args.get("spieler"))
    if spieler == 1:
        feld = spieler1_feld
    else:
        feld = spieler2_feld
    return jsonify(maskiere_feld(feld))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

# nimm die angezeigte erste Adresse im TERMINAL 127.0.0 und hänge "/spieler1" an am Laptop
# nimm die zweite URL 192.168... und hänge "/spieler2" an am Handy