# Bot de Mineração Diária de Nutracêuticos

Minera diariamente 5-6 produtos validados no nicho de encapsulados/suplementos no Brasil,
cruzando **Meta Ad Library, Mercado Livre, Shopee, Amazon e Google**, deduplicando contra
os últimos 15 dias e entregando os melhores via **Telegram** (ou Discord).

## Como funciona

```
config.yaml (keywords + fontes)
        │
        ▼
  Apify actors  ──►  coleta por fonte (miner/sources/*)
        │
        ▼
  normalização → Product (nome, imagem, url, vendas/tração, loja)
        │
        ▼
  dedup SQLite (janela 15d, mineracao.db)
        │
        ▼
  scoring + ranking (miner/scoring.py)  ──►  top 5-6 do dia
        │
        ▼
  entrega Telegram/Discord (cards com imagem + link + tração)
```

## Coleta via Apify (decisão de arquitetura)

Meta, Shopee e Mercado Livre têm anti-scraping forte (Cloudflare, CAPTCHA, bloqueio de IP).
Em vez de manter browser automation + proxies residenciais (frágil, quebra direto), este
projeto usa **actors prontos da [Apify](https://apify.com/store)** — uma API paga de scraping
que já resolve os bloqueios. Custo típico: **US$30-100/mês** conforme volume.

> ⚠️ **Confirme os actor_id antes do primeiro uso.** Os IDs em `config.yaml` são sugestões da
> store. Donos e schemas de input mudam. Abra cada actor em apify.com/store, confirme o
> `actor_id` e, se o formato de input for diferente, ajuste o `run_input` no módulo
> correspondente em `miner/sources/`. O mapeamento de saída usa `_first(...)` testando vários
> nomes de campo, então tolera variação de schema — mas vale revisar com um `--dry-run`.
>
> O único actor oficial e estável usado é `apify/google-search-scraper`.

## Setup

```bash
cd "/Volumes/DANSSD 480G/Mineracao"
python3 -m venv .venv && source .venv/bin/activate   # veja nota abaixo se estiver no SSD externo
pip install -r requirements.txt

cp .env.example .env       # preencha APIFY_TOKEN + TELEGRAM_BOT_TOKEN/CHAT_ID
```

> **SSD externo:** o filesystem deste drive corrompe venvs (erro de encoding em `.pth`).
> Crie o venv num caminho local, ex: `python3 -m venv ~/venvs/mineracao`, e rode com
> `PYTHONPATH="/Volumes/DANSSD 480G/Mineracao" ~/venvs/mineracao/bin/python run_daily.py`.

### Telegram em 2 minutos
1. Fale com [@BotFather](https://t.me/BotFather) → `/newbot` → copie o token → `TELEGRAM_BOT_TOKEN`.
2. Mande qualquer mensagem ao seu bot, abra
   `https://api.telegram.org/bot<TOKEN>/getUpdates` e copie o `chat.id` → `TELEGRAM_CHAT_ID`.

## Uso

```bash
python run_daily.py --dry-run     # coleta + pontua + imprime, SEM enviar (use p/ calibrar)
python run_daily.py               # roda tudo e ENVIA os 5-6 cards
python run_daily.py -v            # logs detalhados
```

## Cron diário (ex: 8h)

```cron
0 8 * * * cd "/Volumes/DANSSD 480G/Mineracao" && /caminho/do/venv/bin/python run_daily.py >> mineracao.log 2>&1
```

## Configuração (`config.yaml`)

- `keywords`: termos do nicho que alimentam as buscas.
- `daily_count`: quantos produtos entregar (padrão 6).
- `dedup_window_days`: janela anti-repetição (padrão 15).
- `delivery`: `telegram` ou `discord`.
- `sources.<fonte>`: `enabled`, `actor_id` e limiares de validação por canal
  (`min_active_days`, `min_sales`, etc.).

## Critérios de validação por fonte

| Fonte          | Métrica de tração                                  | Campo no `Product` |
|----------------|----------------------------------------------------|--------------------|
| Meta Ad Library| anúncio ativo > N dias + nº de anúncios idênticos  | `active_days`, `ad_count` |
| Mercado Livre  | nº de vendas declaradas                            | `sales`            |
| Shopee         | volume de vendas da listagem                       | `sales`            |
| Amazon         | Best Sellers Rank (BSR)                            | `bsr`              |
| Google         | LP patrocinada / domínio de produtor direto        | `ad_count`         |

O `scoring.py` normaliza essas métricas num score 0-100 comparável entre canais.

## Estrutura

```
config.yaml          # keywords, fontes, limiares
.env                 # segredos (Apify, Telegram, Discord)
run_daily.py         # entrypoint do cron
mineracao.db         # SQLite de deduplicação (criado no 1º run)
miner/
  config.py          # carrega yaml + .env
  models.py          # dataclass Product + fingerprint
  db.py              # dedup SQLite
  scoring.py         # score + ranking
  pipeline.py        # orquestra coleta → dedup → score → entrega
  sources/           # meta_ads, mercado_livre, shopee, amazon, google
  delivery/          # telegram, discord
```
