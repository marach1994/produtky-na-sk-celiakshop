# CeliakShop CZ → SK feed transformer

Tento projekt transformuje produktový feed z CZ eshopu (celiakshop.cz) do formátu pro import na SK eshop (Shoptet).

## Soubory

- `transform.py` — hlavní skript
- `category_mapping_rows.json` — 343 řádků mapování CZ kategorií → SK kategorie (načteno z Mergado projektu 339108)
- `spustit.command` — spouštěč pro macOS (dvojklik)
- `spustit.bat` — spouštěč pro Windows (dvojklik)
- `celiakshop_sk.csv` — výstup (generovaný, není ve verzování)

## Závislosti

```bash
pip install openpyxl
```

Potřebné pro čtení SK exportu (xlsx).

## Spuštění

```bash
python3 transform.py              # stáhne feed automaticky z URL
python3 transform.py vstup.csv    # zpracuje lokální soubor
```

Výstup se zapíše jako `celiakshop_sk.csv` vedle skriptu.

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

## Nezmapované kategorie

Kategorie bez záznamu v `category_mapping_rows.json` procházejí beze změny (stejné chování jako Mergado). Při přejmenování kategorií v CZ eshopu je nutné aktualizovat mapovací soubor nebo Mergado pravidla.
