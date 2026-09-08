import os
import re
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
# INVIO TELEGRAM
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

            page.wait_for_timeout(5000)

            content = page.locator("body").inner_text()

            return content

        finally:

            browser.close()


# ==========================================
# ESTRAE SOLO LA PARTE UTILE
# ==========================================

def extract_special_bets(content):

    lines = content.splitlines()

    start = None

    for i, line in enumerate(lines):

        if "SCOMMESSE SPECIALI" in line.upper():

            start = i
            break


    if start is None:

        print("ATTENZIONE: Scommesse Speciali non trovate")

        return ""


    # Prendiamo una porzione della pagina dopo il titolo
    section = lines[start:start + 150]

    cleaned_lines = []

    for line in section:

        line = line.strip()

        if line:
            cleaned_lines.append(line)


    return "\n".join(cleaned_lines)


# ==========================================
# PULIZIA DATI DINAMICI
# ==========================================

def normalize_content(content):

    lines = content.splitlines()

    normalized_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            continue


        # ------------------------------------------
        # IGNORA QUOTE
        # Esempi: 1.80 - 2.05 - 10.50
        # ------------------------------------------

        if re.fullmatch(r"\d+[.,]\d+", line):
            continue


        # ------------------------------------------
        # IGNORA ORARI
        # Esempi: 04:30 - 20:45
        # ------------------------------------------

        if re.fullmatch(r"\d{1,2}:\d{2}", line):
            continue


        # ------------------------------------------
        # IGNORA CODICI SOLO NUMERICI
        # ------------------------------------------

        if re.fullmatch(r"\d+", line):
            continue


        # ------------------------------------------
        # IGNORA DATE
        # ------------------------------------------

        if re.search(
            r"\b(LUNEDÌ|MARTEDÌ|MERCOLEDÌ|GIOVEDÌ|VENERDÌ|SABATO|DOMENICA)\b",
            line.upper()
        ):
            continue


        # ------------------------------------------
        # IGNORA DATE NUMERICHE
        # Esempio: 10.09.2026
        # ------------------------------------------

        if re.fullmatch(
            r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}.*",
            line
        ):
            continue


        # ------------------------------------------
        # NORMALIZZA SPAZI
        # ------------------------------------------

        line = re.sub(
            r"\s+",
            " ",
            line
        )


        normalized_lines.append(line.upper())


    # Elimina eventuali duplicati consecutivi
    final_lines = []

    for line in normalized_lines:

        if not final_lines or line != final_lines[-1]:

            final_lines.append(line)


    return "\n".join(final_lines)


# ==========================================
# PROGRAMMA PRINCIPALE
# ==========================================

def main():

    print("Controllo pagina Netwin...")

    # Legge la pagina
    page_content = get_page_content()

    # Estrae Scommesse Speciali
    special_content = extract_special_bets(
        page_content
    )

    # Pulisce quote e dati dinamici
    current_content = normalize_content(
        special_content
    )


    # Controllo di sicurezza
    if not current_content:

        print(
            "Nessun contenuto utile trovato. "
            "Non aggiorno lo stato."
        )

        return


    print("\nCONTENUTO MONITORATO:\n")

    print(current_content)

    print("\n----------------------------\n")


    # Crea hash del contenuto pulito
    current_hash = hashlib.sha256(
        current_content.encode("utf-8")
    ).hexdigest()


    # ==========================================
    # STATO PRECEDENTE
    # ==========================================

    if os.path.exists(STATE_FILE):

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            previous_hash = file.read().strip()


        # ------------------------------------------
        # Il vecchio codice usava un hash diverso.
        # Se trova un vecchio stato, aggiorna
        # silenziosamente senza inviare un falso alert.
        # ------------------------------------------

        if (
            len(previous_hash) == 64
            and re.fullmatch(
                r"[a-fA-F0-9]{64}",
                previous_hash
            )
        ):

            print(
                "Aggiornamento del vecchio stato "
                "al nuovo sistema di controllo."
            )


        # ------------------------------------------
        # CONFRONTO
        # ------------------------------------------

        elif current_hash != previous_hash:

            print("MODIFICA IMPORTANTE RILEVATA!")

            send_telegram(
                "🚨 MODIFICA RILEVATA SU NETWIN!\n\n"
                "È cambiato il contenuto monitorato "
                "nelle Scommesse Speciali.\n\n"
                f"🔗 {URL}"
            )


        else:

            print(
                "Nessuna modifica importante rilevata."
            )


    # ==========================================
    # PRIMA ESECUZIONE
    # ==========================================

    else:

        print("Prima esecuzione del nuovo monitor.")

        send_telegram(
            "✅ MONITOR NETWIN ATTIVO!\n\n"
            "Ora controllerò principalmente le modifiche "
            "alle scommesse, ignorando quote e altri "
            "dati dinamici."
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


    print("Stato aggiornato correttamente.")


# ==========================================
# AVVIO
# ==========================================

if __name__ == "__main__":

    main()
