import os
import difflib
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
# INVIO TELEGRAM
# ==========================================

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Token Telegram o Chat ID mancanti.")
        return

    telegram_url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    )

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

            page.wait_for_timeout(5000)

            content = page.locator("body").inner_text()

        finally:
            browser.close()


    # ======================================
    # CONTROLLO CLOUDFLARE
    # ======================================

    cloudflare_messages = [
        "Sorry, you have been blocked",
        "You are unable to access netwin.it",
        "Why have I been blocked?",
        "This website is using a security service",
        "Cloudflare Ray ID"
    ]

    for message in cloudflare_messages:

        if message in content:

            print(
                "ACCESSO BLOCCATO DA CLOUDFLARE - "
                "Nessuna modifica registrata."
            )

            return None


    # ======================================
    # ESTRAZIONE SOLO "SCOMMESSE SPECIALI"
    # ======================================

    lines = content.splitlines()

    start = None

    for i, line in enumerate(lines):

        if "SCOMMESSE SPECIALI" in line.upper():

            start = i

            break


    if start is None:

        print(
            "ATTENZIONE: sezione Scommesse Speciali "
            "non trovata."
        )

        return None


    # Prendiamo una porzione della pagina
    # successiva alla sezione Scommesse Speciali

    section_lines = lines[start:start + 150]


    # ======================================
    # PULIZIA TESTO
    # ======================================

    cleaned_lines = []

    for line in section_lines:

        line = line.strip()

        if not line:
            continue

        # Eliminiamo elementi tecnici/volatili
        # che possono cambiare senza modificare
        # realmente le scommesse.

        if "Cloudflare Ray ID" in line:
            continue

        if "Your IP:" in line:
            continue

        cleaned_lines.append(line)


    # ======================================
    # NORMALIZZAZIONE
    # ======================================

    result = "\n".join(cleaned_lines)

    return result.strip()


# ==========================================
# LETTURA STATO PRECEDENTE
# ==========================================

def load_previous_state():

    if not os.path.exists(STATE_FILE):
        return None

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read().strip()

    except Exception as e:

        print(f"Errore lettura stato: {e}")

        return None


# ==========================================
# SALVATAGGIO STATO
# ==========================================

def save_state(content):

    try:

        with open(
            STATE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(content)

    except Exception as e:

        print(f"Errore salvataggio stato: {e}")


# ==========================================
# CONFRONTO DELLE MODIFICHE
# ==========================================

def get_changes(old_content, new_content):

    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()

    diff = difflib.ndiff(
        old_lines,
        new_lines
    )

    added = []
    removed = []

    for line in diff:

        if line.startswith("+ "):

            added.append(line[2:])

        elif line.startswith("- "):

            removed.append(line[2:])


    return added, removed


# ==========================================
# PROGRAMMA PRINCIPALE
# ==========================================

def main():

    print("Controllo pagina Netwin...")

    current_content = get_page_content()


    # ======================================
    # PAGINA NON DISPONIBILE / CLOUDFLARE
    # ======================================

    if current_content is None:

        print(
            "Pagina non disponibile o bloccata. "
            "Stato precedente mantenuto."
        )

        return


    # ======================================
    # STATO PRECEDENTE
    # ======================================

    previous_content = load_previous_state()


    # ======================================
    # PRIMA ESECUZIONE
    # ======================================

    if previous_content is None:

        print(
            "Prima esecuzione: salvo lo stato iniziale."
        )

        save_state(current_content)

        send_telegram(
            "✅ MONITOR NETWIN ATTIVO!\n\n"
            "Ho salvato lo stato iniziale delle "
            "Scommesse Speciali.\n\n"
            "Dalle prossime esecuzioni ti dirò "
            "esattamente cosa è cambiato."
        )

        return


    # ======================================
    # CONFRONTO
    # ======================================

    if current_content == previous_content:

        print("Nessuna modifica rilevata.")

        return


    print("MODIFICA RILEVATA!")


    # ======================================
    # CALCOLO MODIFICHE
    # ======================================

    added, removed = get_changes(
        previous_content,
        current_content
    )


    # ======================================
    # CREAZIONE MESSAGGIO
    # ======================================

    message = (
        "🚨 MODIFICA RILEVATA SU NETWIN!\n\n"
        "📍 Sezione: Scommesse Speciali\n\n"
    )


    if added:

        message += "➕ AGGIUNTO:\n"

        for item in added[:20]:

            message += f"• {item}\n"

        message += "\n"


    if removed:

        message += "➖ RIMOSSO:\n"

        for item in removed[:20]:

            message += f"• {item}\n"

        message += "\n"


    if not added and not removed:

        message += (
            "⚠️ È stata rilevata una modifica, "
            "ma non è stato possibile identificarne "
            "il dettaglio.\n\n"
        )


    message += f"🔗 {URL}"


    # ======================================
    # INVIO TELEGRAM
    # ======================================

    send_telegram(message)


    # ======================================
    # AGGIORNA STATO
    # ======================================

    save_state(current_content)

    print("Stato aggiornato correttamente.")


# ==========================================
# AVVIO
# ==========================================

if __name__ == "__main__":

    main()
