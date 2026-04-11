import argparse
import time
import random
from playwright.sync_api import sync_playwright
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

INSTAGRAM_USER = "minhautilidadebrasil"
INSTAGRAM_PASS = "Cred@29123"

MENSAGEM = """Oi! Tudo bem?

Estava olhando a loja de vocês e percebi que ainda não têm provador virtual de óculos.

Nós somos um provador virtual que permite o cliente experimentar os óculos pela câmera do celular, direto no site. Nossos clientes estão vendo um aumento de até 13% na conversão.

Posso mandar um teste que fizemos com alguns óculos da loja de vocês?"""


def fazer_login(page):
    """Faz login no Instagram."""
    print("Fazendo login no Instagram...")
    page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
    time.sleep(3)

    # Aceita cookies se aparecer
    try:
        cookie_btn = page.locator("button:has-text('Allow'), button:has-text('Permitir'), button:has-text('Accept')")
        if cookie_btn.count() > 0:
            cookie_btn.first.click()
            time.sleep(1)
    except:
        pass

    # Preenche login
    page.fill('input[name="username"]', INSTAGRAM_USER)
    time.sleep(0.5)
    page.fill('input[name="password"]', INSTAGRAM_PASS)
    time.sleep(0.5)
    page.click('button[type="submit"]')

    # Espera login completar
    time.sleep(6)

    # Dispensa "Salvar informacoes de login"
    try:
        not_now = page.locator("button:has-text('Agora não'), button:has-text('Not Now'), button:has-text('Not now')")
        if not_now.count() > 0:
            not_now.first.click()
            time.sleep(2)
    except:
        pass

    # Dispensa notificacoes
    try:
        not_now = page.locator("button:has-text('Agora não'), button:has-text('Not Now'), button:has-text('Not now')")
        if not_now.count() > 0:
            not_now.first.click()
            time.sleep(2)
    except:
        pass

    print("Login OK!")


def enviar_dm(page, username: str, mensagem: str) -> bool:
    """Envia DM para um usuario."""
    try:
        # Vai para o perfil
        print(f"  Abrindo perfil @{username}...")
        page.goto(f"https://www.instagram.com/{username}/", wait_until="networkidle")
        time.sleep(3)

        # Clica em "Enviar mensagem" / "Message"
        msg_btn = page.locator("div[role='button']:has-text('Enviar mensagem'), div[role='button']:has-text('Message'), button:has-text('Enviar mensagem'), button:has-text('Message')")
        if msg_btn.count() == 0:
            print(f"  Botao de mensagem nao encontrado para @{username}")
            return False

        msg_btn.first.click()
        time.sleep(4)

        # Encontra o campo de texto e digita a mensagem
        textarea = page.locator("div[role='textbox'], textarea[placeholder]")
        if textarea.count() == 0:
            print(f"  Campo de texto nao encontrado para @{username}")
            return False

        textarea.first.click()
        time.sleep(0.5)

        # Digita linha por linha para parecer humano
        for linha in mensagem.split("\n"):
            if linha.strip():
                textarea.first.type(linha, delay=random.randint(20, 50))
            # Shift+Enter para nova linha (nao enviar)
            page.keyboard.press("Shift+Enter")
            time.sleep(0.2)

        time.sleep(1)

        # Envia (Enter)
        page.keyboard.press("Enter")
        time.sleep(3)

        print(f"  DM enviada para @{username}!")
        return True

    except Exception as e:
        print(f"  ERRO ao enviar DM para @{username}: {e}")
        return False


def registrar_no_crm(supabase_client, lead_id: str, username: str):
    """Registra a DM enviada no CRM."""
    # Atualiza status do lead
    supabase_client.table("leads").update({"status": "dm_enviada"}).eq("id", lead_id).execute()

    # Adiciona interacao
    supabase_client.table("interacoes").insert({
        "lead_id": lead_id,
        "tipo": "dm_enviada",
        "conteudo": "DM de prospeccao enviada automaticamente",
    }).execute()


def main():
    parser = argparse.ArgumentParser(description="Envia DMs para leads do pipeline")
    parser.add_argument("--limite", type=int, default=5, help="Quantidade de DMs para enviar (default: 5)")
    parser.add_argument("--intervalo", type=int, default=3, help="Minutos entre cada DM (default: 3)")
    parser.add_argument("--headless", action="store_true", help="Rodar sem abrir navegador visivel")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERRO: SUPABASE_URL e SUPABASE_KEY nao definidos no .env")
        return

    # Busca leads com status "novo" no Supabase
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = sb.table("leads").select("*").eq("status", "novo").order("created_at").limit(args.limite).execute()
    leads = result.data

    if not leads:
        print("Nenhum lead com status 'novo' encontrado.")
        return

    print(f"\n{'='*50}")
    print(f"  ENVIO DE DMs — {len(leads)} leads")
    print(f"  Intervalo: {args.intervalo} min entre cada")
    print(f"  Tempo estimado: ~{len(leads) * args.intervalo} min")
    print(f"{'='*50}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # Login
        fazer_login(page)

        enviados = 0
        falhas = 0

        for i, lead in enumerate(leads):
            username = lead["instagram"]
            print(f"\n[{i+1}/{len(leads)}] @{username} — {lead.get('nome_loja', '')}")

            sucesso = enviar_dm(page, username, MENSAGEM)

            if sucesso:
                registrar_no_crm(sb, lead["id"], username)
                enviados += 1
                print(f"  Status atualizado para 'dm_enviada' no CRM")
            else:
                falhas += 1

            # Intervalo entre DMs (exceto na ultima)
            if i < len(leads) - 1:
                espera = args.intervalo * 60 + random.randint(-30, 30)
                print(f"\n  Aguardando {espera//60}m{espera%60}s ate a proxima...")
                time.sleep(espera)

        browser.close()

    print(f"\n{'='*50}")
    print(f"  RESULTADO: {enviados} enviadas, {falhas} falhas")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
