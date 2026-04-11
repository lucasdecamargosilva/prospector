import argparse
import json
import os
from apify_client import ApifyClient
from config import APIFY_TOKEN, DATA_DIR, LEADS_BRUTOS_PATH

SEARCH_QUERIES = [
    "loja de oculos",
    "otica online",
    "oculos de sol loja",
    "eyewear brasil",
    "otica oculos grau",
]


def buscar_perfis(client: ApifyClient, query: str, limit: int) -> list[dict]:
    """Busca perfis de lojas no Instagram via Apify Search Scraper."""
    print(f"  Buscando: '{query}' (limite: {limit})...")

    run_input = {
        "search": query,
        "searchType": "user",
        "resultsLimit": limit,
    }

    run = client.actor("apify/instagram-search-scraper").call(run_input=run_input)

    if run["status"] != "SUCCEEDED":
        print(f"  ERRO: Actor terminou com status {run['status']}")
        return []

    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"  {len(items)} perfis encontrados")
    return items


def extrair_lead(item: dict) -> dict:
    """Extrai dados relevantes de um resultado do Apify."""
    # Pega o primeiro URL externo como site
    site = ""
    external_urls = item.get("externalUrls") or []
    if external_urls:
        site = external_urls[0].get("url", "")
    if not site:
        site = item.get("externalUrl", "")

    return {
        "instagram": item.get("username", ""),
        "nome_loja": item.get("fullName", ""),
        "site": site,
        "seguidores": item.get("followersCount", 0) or item.get("followers", 0),
        "bio": item.get("biography", ""),
        "is_business": item.get("isBusinessAccount", False),
    }


def main():
    parser = argparse.ArgumentParser(description="Coleta perfis de lojas de oculos no Instagram via Apify")
    parser.add_argument("--query", type=str, default=None, help="Query especifica para buscar")
    parser.add_argument("--limit", type=int, default=20, help="Limite de perfis por query")
    parser.add_argument("--min-seg", type=int, default=5000, help="Minimo de seguidores (default: 5000)")
    args = parser.parse_args()

    if not APIFY_TOKEN:
        print("ERRO: APIFY_TOKEN nao definido no .env")
        return

    client = ApifyClient(APIFY_TOKEN)
    queries = [args.query] if args.query else SEARCH_QUERIES

    all_leads: list[dict] = []
    seen_usernames: set[str] = set()

    print(f"\nBuscando lojas de oculos no Instagram ({len(queries)} queries)\n")

    for query in queries:
        items = buscar_perfis(client, query, args.limit)

        for item in items:
            lead = extrair_lead(item)
            username = lead["instagram"]

            if not username or username in seen_usernames:
                continue

            if lead["seguidores"] < args.min_seg:
                print(f"    - @{username} — {lead['seguidores']} seg. (abaixo de {args.min_seg}, pulando)")
                continue

            seen_usernames.add(username)
            all_leads.append(lead)
            print(f"    + @{username} — {lead['nome_loja']} ({lead['seguidores']} seg.)")

    # Salva resultado
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LEADS_BRUTOS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_leads, f, ensure_ascii=False, indent=2)

    print(f"\n{len(all_leads)} leads brutos salvos em {LEADS_BRUTOS_PATH}")


if __name__ == "__main__":
    main()
