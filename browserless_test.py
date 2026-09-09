import os
from playwright.sync_api import sync_playwright

URL = "https://www.netwin.it/scommesse/calcio/scommesse-speciali/u-o-giornata"

def main():
    token = os.environ["BROWSERLESS_TOKEN"]

    print("========================================")
    print("TEST BROWSERLESS → NETWIN")
    print("========================================")

    ws_endpoint = f"wss://production-sfo.browserless.io?token={token}"

    try:
        with sync_playwright() as p:
            print("Connessione a Browserless...")
            
            browser = p.chromium.connect_over_cdp(ws_endpoint)

            context = browser.contexts[0]
            page = context.new_page()

            print("Apro Netwin...")
            
            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(8000)

            print(f"URL finale: {page.url}")
            print(f"Titolo: {page.title()}")

            text = page.locator("body").inner_text()

            print(f"Dimensione testo: {len(text)} caratteri")

            lower_text = text.lower()

            if "sorry, you have been blocked" in lower_text:
                print("❌ NETWIN HA MOSTRATO UNA PAGINA DI BLOCCO")

            elif "cloudflare" in lower_text:
                print("⚠️ È presente Cloudflare nella pagina")

            else:
                print("✅ PAGINA NETWIN CARICATA")

            if "champions" in lower_text:
                print("🚨 TROVATA LA PAROLA CHAMPIONS!")
            else:
                print("ℹ️ Champions NON presente")

            print("========================================")
            print("TEST TERMINATO")
            print("========================================")

            browser.close()

    except Exception as e:
        print("❌ ERRORE:")
        print(e)


if __name__ == "__main__":
    main()
