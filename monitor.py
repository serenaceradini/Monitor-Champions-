import os
import hashlib
import requests
from playwright.sync_api import sync_playwright


# ==========================================
# CONFIGURAZIONE
# ==========================================

URL = "https://www.netwin.it/scommesse/calcio/scommesse-speciali/u-o-giornata"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

STATE_FILE = "last_state.txt"


# ==========================================
# INVIO MESSAGGIO TELEGRAM
# ==========================================

def send_telegram(message):

    if not BOT_TOKEN or not CHAT_ID:
        print("Token Telegram o Chat ID mancanti")
        return

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            telegram_url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=30
        )

        print(response.text)

    except Exception as e:
        print(f"Errore Telegram: {e}")


# ==========================================
# LETTURA PAGINA NETWIN
# ==========================================

def get_page_content():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        try:

            page = browser.new_page()

            page.goto(
                URL,
                wait_until="networkidle",
                timeout=60000
            )

            # Aspetta che la pagina finisca di caricare
            page.wait_for_timeout(5000)

            # Prende tutto il testo visibile della pagina
            content = page.locator("body").inner_text()

            # ==========================================
            # ESTRAZIONE SEZIONE SCOMMESSE SPECIALI
            # ==========================================

            lines = content.splitlines()

            start = None

            for i, line in enumerate(lines):

                if "SCOMMESSE SPECIALI" in line.upper():

                    start = i
                    break

            # Se trova la sezione, prende le 120 righe successive
            if start is not None:

                content = "\n".join(
                    lines[start:start + 120]
                )

            else:

                print(
                    "ATTENZIONE: sezione Scommesse Speciali non trovata"
                )

            # ==========================================
            # PULIZIA DEL TESTO
            # ==========================================

            cleaned_lines = []

            for line in content.splitlines():

                line = line.strip()

                if line:
                    cleaned_lines.append(line)

            content = "\n".join(cleaned_lines)

            return content

        finally:

            browser.close()


# ==========================================
# PROGRAMMA PRINCIPALE
# ==========================================

def main():

    print("Controllo della pagina Netwin...")

    current_content = get_page_content()

    current_hash = hashlib.sha256(
        current_content.encode("utf-8")
    ).hexdigest()


    # ==========================================
    # SE ESISTE UNO STATO PRECEDENTE
    # ==========================================

    if os.path.exists(STATE_FILE):

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            previous_hash = file.read().strip()


        # ==========================================
        # MODIFICA RILEVATA
        # ==========================================

        if current_hash != previous_hash:

            print("MODIFICA RILEVATA!")

            send_telegram(
                "🚨 MODIFICA RILEVATA SU NETWIN!\n\n"
                "La pagina delle Scommesse Speciali è cambiata.\n\n"
                f"🔗 {URL}"
            )


        else:

            print("Nessuna modifica rilevata.")


    # ==========================================
    # PRIMA ESECUZIONE
    # ==========================================

    else:

        print("Prima esecuzione.")

        send_telegram(
            "✅ MONITOR NETWIN ATTIVO!\n\n"
            "Da questo momento controllerò la pagina "
            "e ti avviserò quando rileverò una modifica."
        )


    # ==========================================
    # SALVA NUOVO STATO
    # ==========================================

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(current_hash)


# ==========================================
# AVVIO
# ==========================================

if __name__ == "__main__":
    main()
