import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://prenotatore.betaland.it/sport/calcio/u/o-giornata_1_-2_-8261"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

STATE_FILE = "last_state.txt"


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Token o Chat ID mancanti")
        return

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    print(response.text)


def get_page_content():
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto(
            URL,
            wait_until="networkidle",
            timeout=60000
        )

        page.wait_for_timeout(5000)

        content = page.locator("body").inner_text()

        browser.close()

        return content


def main():

    print("Controllo della pagina Betaland...")

    current_content = get_page_content()

    current_hash = hashlib.sha256(
        current_content.encode("utf-8")
    ).hexdigest()

    if os.path.exists(STATE_FILE):

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            previous_hash = file.read().strip()

        if current_hash != previous_hash:

            send_telegram(
                "🚨 MODIFICA RILEVATA SU BETALAND!\n\n"
                "La pagina delle giocate è cambiata.\n\n"
                f"🔗 {URL}"
            )

            print("Modifica rilevata!")

        else:

            print("Nessuna modifica.")

    else:

        send_telegram(
            "✅ MONITOR BETALAND ATTIVO!\n\n"
            "Da questo momento controllerò la pagina "
            "e ti avviserò quando rileverò una modifica."
        )

        print("Prima esecuzione.")

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(current_hash)


if __name__ == "__main__":
    main()
