#!/usr/bin/env python3
"""Wires the company-logo cache into the twelve race pages and the help files.

The race badges now wear company logos (`Render/CompanyLogoCache.cs`): the renderer
grew a `Faces` property and the export path a warm-up, so each page needs two
mechanical insertions — `Faces = CompanyLogoCache.Shared` in the renderer's object
initialiser, and the shared cache's marshal/invalidation wiring in the constructor —
and every help file one sentence about where the logos come from.

Idempotent like its siblings: a file already carrying the insertion is left alone.
BOM and line endings preserved per file.
"""

import importlib.util
import pathlib
import sys

_path = pathlib.Path(__file__).resolve().parent / "port-race-styles-help.py"
_spec = importlib.util.spec_from_file_location("port_race_styles_help", _path)
_race_help = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_race_help)  # reuses its BULLETS as this round's anchors

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "src" / "MarketMotionStudio" / "Pages"
HELP = ROOT / "src" / "MarketMotionStudio" / "Assets" / "Help"

STYLE_LINE = "Style = RaceStyleCombo.ChosenStyle,"
FACES_LINE = "Faces = CompanyLogoCache.Shared,"
CTOR_LINE = "InitializeComponent();"
WIRING = (
    "\n\n"
    "        // Late-landing logos repaint the preview; the marshal keeps the hop on\n"
    "        // the UI thread, the way the cache's contract asks for.\n"
    "        CompanyLogoCache.Shared.Marshal = a => DispatcherQueue.TryEnqueue(() => a());\n"
    "        CompanyLogoCache.Shared.Invalidated = () => Preview.Redraw();"
)

PAGES_12 = [
    "AhPremiumPage", "AssetRacePage", "BondRacePage", "ExtremeDaysPage",
    "CryptoComparePage", "CryptoMarketCapPage", "CryptoMoversPage", "CryptoDominancePage",
    "MarketCapPage", "SectorRacePage", "IndexRacePage", "HoldOddsPage",
]

# The logo sentence, per language — anchored after the display-style bullet the
# previous port left behind (its BULLETS, imported above).
LOGOS = {
    "help-cs.md": "- Odznaky závodů, jejichž účastník je kotovaná společnost, nosí **logo firmy**: "
                  "stáhne se jednou podle kódu a dál se drží v místní mezipaměti; indexy, data a měny "
                  "si ponechají odznak s prvním písmenem.",
    "help-de.md": "- Abzeichen von Entries, die ein börsennotiertes Unternehmen sind, tragen das "
                  "**Firmenlogo**: einmal per Code geladen, danach aus dem lokalen Bestand; Indizes, "
                  "Daten und Münzen behalten das Abzeichen mit dem Anfangsbuchstaben.",
    "help-en-US.md": "- Badges of listed companies wear the **company's logo**: fetched once by code, "
                     "then kept from the local cache; indexes, dates and coins — anything without a "
                     "corporate mark — keep the first-character badge.",
    "help-es.md": "- Las insignias de sociedades cotizadas llevan el **logo de la empresa**: se "
                  "descarga una vez por código y queda en la caché local; índices, fechas y monedas "
                  "conservan la insignia con la inicial.",
    "help-fr.md": "- Les badges des sociétés cotées portent le **logo de l'entreprise** : récupéré "
                  "une fois par code, ensuite servi par le cache local ; indices, dates et monnaies "
                  "gardent le badge à l'initiale.",
    "help-it.md": "- I badge delle società quotate portano il **logo dell'azienda**: scaricato una "
                  "volta per codice, poi servito dalla cache locale; indici, date e monete mantengono "
                  "il badge con l'iniziale.",
    "help-ja.md": "- 上場企業のエントリーのバッジには**企業ロゴ**が入ります。コードを key に一度だけ取得し、"
                  "以後はローカルのキャッシュを使います。指数・日付・通貨など企業ロゴのないものは"
                  "頭文字のバッジのままです。",
    "help-ko.md": "- 상장 기업 항목의 배지에는 **회사 로고**가 들어갑니다. 코드로 한 번만 내려받아 로컬 "
                  "캐시로 계속 쓰며, 지수·날짜·코인처럼 로고가 없는 항목은 첫 글자 배지를 유지합니다.",
    "help-pl.md": "- Odznaki spółek notowanych noszą **logo firmy**: pobierane raz wg kodu, potem z "
                  "lokalnej pamięci; indeksy, daty i monety zachowują odznakę z pierwszą literą.",
    "help-pt-BR.md": "- Os emblemas de companhias listadas exibem o **logo da empresa**: buscado uma "
                     "vez por código e depois mantido no cache local; índices, datas e moedas "
                     "mantêm o emblema com a inicial.",
    "help-ru.md": "- У значков эмитентов, чьи акции котируются, — **логотип компании**: один раз "
                  "скачивается по коду, дальше берётся из локального кэша; у индексов, дат и монет "
                  "остаётся значок с первой буквой.",
    "help-tr.md": "- Halka açık şirketlerin nişanları **şirket logosunu** taşır: kodla bir kez "
                  "indirilir, sonra yerel önbellekten sunulur; endeksler, tarihler ve coinler ilk "
                  "harf nişanını korur.",
    "help-zh-Hans.md": "- 上市公司条目的徽章显示**公司 Logo**：按代码联网获取一次，之后一直用本地缓存；"
                       "指数、日期、币种等没有公司标志的条目仍显示名称首字徽章。",
    "help-zh-Hant.md": "- 上市公司條目的徽章顯示**公司 Logo**：按代碼連網獲取一次，之後一直用本地快取；"
                       "指數、日期、幣種等沒有公司標誌的條目仍顯示名稱首字徽章。",
}


def edit(path: pathlib.Path, apply, marker: str) -> str:
    """Applies one idempotent insertion, preserving BOM and line endings."""
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"

    if marker in text:
        return "skipped"

    changed = apply(text)

    # The BOM rides along: the pages carry one, and an insertion that drops it
    # is a diff the next build did not ask for.
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + changed.replace("\n", newline).encode("utf-8"))
    return "changed"


def add_faces(text: str) -> str:
    lines = text.split("\n")
    out = []

    for line in lines:
        out.append(line)

        if line.strip() == STYLE_LINE:
            out.append(line[: len(line) - len(line.lstrip())] + FACES_LINE)

    return "\n".join(out)


def add_wiring(text: str) -> str:
    return text.replace(CTOR_LINE, CTOR_LINE + WIRING, 1)


def main():
    changed, skipped, problem = [], [], []

    for name in PAGES_12:
        path = PAGES / f"{name}.xaml.cs"

        if not path.exists():
            problem.append(f"{name} (missing)")
            continue

        if FACES_LINE not in path.read_text(encoding="utf-8-sig"):
            state = edit(path, add_faces, FACES_LINE)
        else:
            state = "skipped"

        if WIRING.strip() not in path.read_text(encoding="utf-8-sig"):
            state2 = edit(path, add_wiring, WIRING.strip())
        else:
            state2 = "skipped"

        (changed if "changed" in (state, state2) else skipped).append(name)

    for name, bullet in LOGOS.items():
        path = HELP / name
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")

        if bullet in text:
            skipped.append(name)
            continue

        anchor = _race_help.BULLETS[name]

        if text.count(anchor) != 1:
            problem.append(f"{name} ({text.count(anchor)} anchor matches)")
            continue

        path.write_bytes((text.replace(anchor, anchor + "\n" + bullet)).encode("utf-8"))
        changed.append(name)

    print(f"changed : {len(changed)}  {' '.join(changed)}")
    print(f"skipped : {len(skipped)}  {' '.join(skipped) or '-'}")
    print(f"problem : {len(problem)}  {' '.join(problem) or '-'}")


if __name__ == "__main__":
    main()
