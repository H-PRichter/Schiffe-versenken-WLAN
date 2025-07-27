// Editor-Modus: Schiffe setzen
console.log("JS ist aktiv"); // Debugging Satz z Überprüfen
const socket = io(); 

let aktuelleLaengen = [2, 3, 3, 4, 5];  // Schiffe, die gesetzt werden sollen
let aktuellesSchiff = 0;
let richtung = "horizontal";  // oder "vertical"

const laengeAnzeige = document.getElementById("laenge");
const richtungAnzeige = document.getElementById("richtung");
const statusText = document.getElementById("editor-status");
const button = document.getElementById("schiffdrehen");
const grid = document.getElementById("eigenes-feld");
const gegnerGrid = document.getElementById("gegner-feld");
const statusAnzeige = document.getElementById("spielstatus");

const soundExplosion = new Audio("/static/sounds/explosion.wav");
const soundWasser = new Audio("/static/sounds/wasser.wav");
const soundNope = new Audio("/static/sounds/nope.wav");

function setzeStatus(text) {
  statusAnzeige.textContent = text;
}

function aktualisiereStatus() {
  laengeAnzeige.textContent = aktuelleLaengen[aktuellesSchiff] || "-";
  richtungAnzeige.textContent = richtung;
}

function feldKoordinaten(div) {
  const felder = Array.from(grid.children);
  const index = felder.indexOf(div);
  const x = index % 10;
  const y = Math.floor(index / 10);
  return [x, y];
}

function kannSetzen(x, y, laenge, richtung) {
  for (let i = 0; i < laenge; i++) {
    const nx = richtung === "horizontal" ? x + i : x;
    const ny = richtung === "vertical" ? y + i : y;
    if (nx > 9 || ny > 9) return false;
    const feld = grid.children[ny * 10 + nx];
    if (feld.classList.contains("schiff")) return false;
  }
  return true;
}

function setzeSchiff(x, y, laenge, richtung) {
  for (let i = 0; i < laenge; i++) {
    const nx = richtung === "horizontal" ? x + i : x;
    const ny = richtung === "vertical" ? y + i : y;
    const feld = grid.children[ny * 10 + nx];
    feld.classList.add("schiff");
  }
  schiffAnServerSenden(x, y, laenge, richtung);
}

function schiffAnServerSenden(x, y, laenge, richtung) {
  fetch("/setze-schiff", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ x, y, laenge, richtung, spieler })
  }).then(response => {
    if (!response.ok) {
      console.error("Fehler beim Speichern des Schiffs 😭");
      return;
    }

    if (aktuellesSchiff >= aktuelleLaengen.length) {
      fetch("/bereit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ spieler })
      })
      .then(res => res.json())
      .then((daten) => {
        if (daten.status === "startbereit") {
          setzeStatus("🚀 Beide Spieler sind bereit! Das Spiel beginnt.");
        }
      }
  )}
  });
}

function handleFeldClick(e) {
  if (aktuellesSchiff >= aktuelleLaengen.length) return;

  const ziel = e.target;
  if (!ziel.classList.contains("feld")) return;

  const [x, y] = feldKoordinaten(ziel);
  const laenge = aktuelleLaengen[aktuellesSchiff];

  if (kannSetzen(x, y, laenge, richtung)) {
    setzeSchiff(x, y, laenge, richtung);
    aktuellesSchiff++;
    aktualisiereStatus();
    if (aktuellesSchiff >= aktuelleLaengen.length) {
      statusText.textContent = "Alle Schiffe gesetzt ✅";
      button.disabled = true;
    }
  } else {
    alert("Ungültige Position! 😕");
  }

  e.preventDefault();
}

function updateEigenesFeld() {
  fetch("/eigenes-feld?spieler=" + spieler)
    .then(res => res.json())
    .then((feld) => {
      const felder = Array.from(grid.children);
      for (let y = 0; y < 10; y++) {
        for (let x = 0; x < 10; x++) {
          const index = y * 10 + x;
          const feldDiv = felder[index];
          const inhalt = feld[y][x];
          if (inhalt === "X") {
            feldDiv.classList.add("treffer");
          } else if (inhalt === "O") {
            feldDiv.classList.add("verfehlt");
          }
        }
      }
    });
}

grid.addEventListener("contextmenu", (e) => {
  e.preventDefault();
  richtung = richtung === "horizontal" ? "vertical" : "horizontal";
  aktualisiereStatus();
});

button.addEventListener("click", () => {
  richtung = richtung === "horizontal" ? "vertical" : "horizontal";
  aktualisiereStatus();
});

// 🎧 Sound-Freischaltung für Mobile-Geräte
grid.addEventListener("click", () => {
  [soundExplosion, soundWasser, soundNope].forEach((snd) => {
    snd.play().catch(() => {});
    snd.pause();
    snd.currentTime = 0;
  });
}, { once: true });

grid.addEventListener("click", handleFeldClick);
grid.addEventListener("touchstart", handleFeldClick);

if (gegnerGrid) {
  gegnerGrid.addEventListener("click", (e) => {
    const ziel = e.target;
    if (!ziel.classList.contains("feld")) return;

    const felder = Array.from(gegnerGrid.children);
    const index = felder.indexOf(ziel);
    const x = index % 10;
    const y = Math.floor(index / 10);
socket.emit("angriff", { x, y, spieler });
  }); // <-- schließt addEventListener
} // <-- schließt if (gegnerGrid)

socket.on("angriffErgebnis", (daten) => {
    if (daten.status === "ungueltig") {
      soundNope.play();
      alert("Nicht Dein Zug! 😬");
      return;
    }
  if (daten.schuetze === spieler) {
    const felder = Array.from(gegnerGrid.children);
    const index = daten.y * 10 + daten.x;  
    const ziel = felder[index];

    if (daten.status === "treffer") {
      ziel.classList.add("treffer");
      soundExplosion.play();
      setzeStatus("Treffer! Du darfst nochmal! 🌟");
    } else if (daten.status === "verfehlt") {
      ziel.classList.add("verfehlt");
      soundWasser.play();
      setzeStatus("Daneben! Gegner ist dran.");

    }

    if (daten.gewonnen) {
      setzeStatus("🎉 Du hast gewonnen!");
    }
  } else if (daten.ziel === spieler) {
    // Wir wurden getroffen
    updateEigenesFeld();
    setzeStatus("💥 Treffer auf dein Schiff!");

    if (daten.gewonnen) {
      setzeStatus("💀 Du hast verloren. Deine Flotte ist versenkt.");
      gegnerGrid.removeEventListener("click", handleAngriff);
    }
  }
});

aktualisiereStatus();
