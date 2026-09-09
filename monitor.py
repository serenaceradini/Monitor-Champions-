import requests

URL = "https://www.netwin.it/XSportDatastore/getTorneoCentrale?systemCode=WINBET&lingua=IT&hash=&sportId=1&categoryId=-2&tournamentId=-8261&idAggregata=2376"

KEYWORD = "champions"


def main():
    print("========================================")
    print("TEST ACCESSO DIRETTO NETWIN")
    print("========================================")

    try:
        response = requests.get(
            URL,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        print(f"Status HTTP: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")

        content = response.text

        print(f"Dimensione risposta: {len(content)} caratteri")

        # Controllo Cloudflare
        cloudflare_words = [
            "Sorry, you have been blocked",
            "You are unable to access netwin.it",
            "Why have I been blocked?",
            "Cloudflare Ray ID"
        ]

        content_lower = content.lower()

        for word in cloudflare_words:
            if word.lower() in content_lower:
                print("❌ RISPOSTA BLOCCATA DA CLOUDFLARE")
                return

        print("✅ RISPOSTA RICEVUTA DA NETWIN")

        if KEYWORD in content_lower:
            print("🚨 TROVATA LA PAROLA CHAMPIONS!")
        else:
            print("ℹ️ La parola Champions NON è presente.")

        print("========================================")
        print("TEST TERMINATO")
        print("========================================")

    except Exception as e:
        print(f"❌ ERRORE: {e}")


if __name__ == "__main__":
    main()
