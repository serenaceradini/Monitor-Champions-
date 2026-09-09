import requests

URL = "https://prenotatore.betaland.it/sport/calcio/u/o-giornata_1_-2_-8261"

print("========================================")
print("TEST BETALAND")
print("========================================")

try:
    r = requests.get(
        URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    print("Status HTTP:", r.status_code)
    print("Dimensione risposta:", len(r.text))

    testo = r.text.lower()

    if "usa mls u/o giornata" in testo:
        print("✅ EVENTO TROVATO!")
        print("Betaland è leggibile automaticamente.")
    elif "autenticazione fallita" in testo or "username" in testo:
        print("🔒 BETALAND CHIEDE IL LOGIN")
        print("La pagina automatica non vede gli eventi.")
    else:
        print("⚠️ RISPOSTA RICEVUTA, MA EVENTO NON TROVATO")

    print("========================================")

except Exception as e:
    print("❌ ERRORE:", e)
