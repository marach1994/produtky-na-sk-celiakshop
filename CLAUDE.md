# CeliakShop CZ → SK feed transformer

Tento projekt transformuje produktový feed z CZ eshopu (celiakshop.cz) do formátu pro import na SK eshop (Shoptet).

## Soubory

- `transform.py` — hlavní transformační skript (na konci nabídne kontrolu kategorií)
- `check_categories.py` — snapshot/diff stromu SK kategorií (kontrola nových kategorií po importu)
- `check_seasonal.py` — kontrola sezónních kategorií v CZ feedu, odesílá alert do Freelo
- `category_mapping_rows.json` — 343 řádků mapování CZ kategorií → SK kategorie (načteno z Mergado projektu 339108)
- `spustit.command` — spouštěč pro macOS (dvojklik)
- `spustit.bat` — spouštěč pro Windows (dvojklik)
- `celiakshop_sk.csv` — výstup (generovaný, není ve verzování)
- `snapshots/` — snapshoty SK kategorií (generované, nejsou ve verzování)
- `zaloha_sk.xlsx` — záloha staženého SK exportu produktů, přepisuje se při každém běhu (generovaná, není ve verzování)
- `check_seasonal.log` — log automatického spouštění (generovaný, není ve verzování)

## Závislosti

```bash
pip install -r requirements.txt
```

`openpyxl` (čtení SK exportu xlsx), `requests` + `lxml` (kontrola kategorií), `colorama` (volitelné barvy).

## Spuštění

```bash
python3 transform.py              # stáhne feed automaticky z URL
python3 transform.py vstup.csv    # zpracuje lokální soubor
```

Průběh (stejný přes `spustit.command` / `spustit.bat`):

1. stažení SK exportu (uloží se záloha `zaloha_sk.xlsx` vedle skriptu), transformace + zápis `celiakshop_sk.csv`,
2. výpis produktů z CZ feedu, které nejsou na SK eshopu (stderr),
3. výpis sezónních kategorií v CZ feedu (Vánoce/Velikonoce/Prázdniny), nebo hláška že žádné nejsou — používá `find_seasonal_products` z `check_seasonal.py`, bez Freelo alertu,
4. automatické uložení snapshotu SK kategorií,
5. výzva „Proveď import produktů na SK eshopu" + prompt `Spustit kontrolu kategorií? [Y/n]` — při potvrzení porovná aktuální kategorie se snapshotem a vypíše nové/smazané.

## Zdroj dat

Skript pracuje se dvěma URL definovanými v `transform.py`:

- `SOURCE_URL` — CZ feed (CSV, středníkový oddělovač):
  ```
  https://www.celiakshop.cz/export/products.csv?patternId=61&partnerId=3&hash=...
  ```
- `SK_EXPORT_URL` — SK export (xlsx přejmenovaný na xls):
  ```
  https://www.celiakshop.sk/export/products.xls?patternId=15&partnerId=3&hash=...
  ```

## Filtrování produktů

Skript stáhne SK export a sestaví sadu existujících kódů (`code`). Do výstupního CSV se zapíší **pouze produkty z CZ feedu, které mají odpovídající kód na SK eshopu**. Produkty bez shody se vypíší na stderr jako přehled chybějících položek.

## Transformační pravidla (Mergado projekt 339108)

Pravidla jsou replikací Mergado projektu **CeliakShop - ceny do EUR** (ID 339108, eshop Mamtex.cz).

| Priorita | Název | Pole | Transformace |
|---|---|---|---|
| 1 | Akční cena EUR | `actionPrice` | ÷ 24,7, 2 des. místa |
| 2 | price EUR | `price` | ÷ 24,5, 2 des. místa |
| 3 | standart price EUR | `standardPrice` | ÷ 24,7, 2 des. místa |
| 4 | nákupní cena EUR | `purchasePrice` | ÷ 24,7, 2 des. místa |
| 5 | Vlastnosti | `filteringProperty:Vlastnosti` | Překlad CZ → SK (19 hodnot) |
| 6 | Bez Lepku příznak | `bez-lepkuFlagActive` | Přejmenování na `custom2FlagActive` |
| 7–18 | >> kategorie | `defaultCategory`, `categoryText1–11` | Regex: odstraní `^>> `, nahradí `>>` za `>` |
| 19–30 | Párování kategorie | `defaultCategory`, `categoryText1–11` | 343 řádků mapování CZ → SK |

Zaokrouhlení cen: matematické (0,5 nahoru), oddělovač desetin: čárka.

## Výstupní formát

Shoptet SK CSV (středníkový oddělovač, UTF-8 BOM), 39 sloupců:

```
code, pairCode, supplier, manufacturer, defaultCategory, categoryText,
price, standardPrice, purchasePrice, actionPrice, actionFrom, actionUntil,
negativeAmount, actionFlagActive, ..., custom2FlagActive,
categoryText2–11
```

## Kontrola kategorií (check_categories.py)

Sleduje strom kategorií SK eshopu (XML feed `https://www.celiakshop.sk/export/categories.xml?partnerId=3&patternId=-31&hash=...`, konstanta `FEED_URL`). Snapshoty se ukládají do `snapshots/` vedle skriptu (`latest.json` + časové zálohy). `transform.py` ho volá automaticky (snapshot před importem, check po potvrzení); lze spustit i samostatně:

```bash
python3 check_categories.py snapshot   # uloží aktuální stav kategorií
python3 check_categories.py check      # porovná feed s posledním snapshotem (--verbose vypíše vše)
```

## Kontrola sezónních kategorií (check_seasonal.py)

Skript stáhne CZ feed a hledá produkty, kde `defaultCategory` obsahuje klíčová slova `Vánoce`, `Velikonoce` nebo `Prázdniny`. Pokud takové produkty nalezne, odešle alert jako komentář do Freelo úkolu [Sezónní kategorie](https://app.freelo.io/task/30581159). Pokud nic nenalezne, tiše skončí.

```bash
python3 check_seasonal.py          # stáhne feed z URL
python3 check_seasonal.py feed.csv # zpracuje lokální soubor
```

Automatické spouštění: **každý den v 8:00** přes `cron` (nastaveno na localním Macu):
```
0 8 * * * python3 /path/to/check_seasonal.py >> check_seasonal.log 2>&1
```

Freelo API: basic auth (`adamkelbl0@gmail.com` + API token), endpoint `POST /v1/task/{id}/comments`.

## Nezmapované kategorie

Kategorie bez záznamu v `category_mapping_rows.json` procházejí beze změny (stejné chování jako Mergado). Při přejmenování kategorií v CZ eshopu je nutné aktualizovat mapovací soubor nebo Mergado pravidla.
