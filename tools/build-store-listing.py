# -*- coding: utf-8 -*-
"""Build the two Store-listing deliverables at the project root from the canonical
copy in docs/.

Inputs (read-only):
  docs/store-listing.md                          the fourteen-language listing copy
  docs/listingData-9NGDNH0CCW7L-1152921505702020674.csv
                                                 the Partner Center listing-data template
                                                 (field rows + language columns + the
                                                 Feature1..N rows, which are pre-split
                                                 to the 200-character feature limit)

Outputs (written):
  store-listing.md                               submission-ready listing document
  listingData-9NGDNH0CCW7L-1152921505702020674.csv
                                                 the same template, filled

Everything the two outputs share is generated from the same parsed text, so the CSV
and the markdown cannot drift. Run from the repo root:  python tools/build-store-listing.py
"""

import csv
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
TEMPLATE = os.path.join(
    DOCS, "listingData-9NGDNH0CCW7L-1152921505702020674.csv")
LISTING = os.path.join(DOCS, "store-listing.md")

VERSION = "1.0.22.0"
VERSION_DATE = "2026-10-29"
APP_TITLE = "MarketMotionStudio"
DEV_STUDIO = "YiwenYang"
COPYRIGHT = "© 2026 YiwenYang. All rights reserved."

# The nine screenshots, in Partner Center order, and the description bullet each
# one illustrates (0-based index into the thirty-one-chart list, identical in every
# language, which is where the per-language captions come from).
SHOTS = [
    ("01-market-turnover", 0),
    ("02-sector-race", 2),
    ("03-gain-calendar", 4),
    ("04-monthly-matrix", 3),
    ("05-dca-plan", 5),
    ("06-position", 6),
    ("07-candle", 8),
    ("08-market-cap", 9),
    ("09-bond-race", 17),
]

# Languages that get their own rendered set; every other region falls back to
# en-us, which Partner Center offers automatically.
SHOT_LANGS = {"en-us": "en-us", "zh-hans": "zh-hans", "zh-hant": "zh-hant"}

# ---- authored copy ------------------------------------------------------------

SHORT_DESC = {
    "en-us": "Turn stock-market data into 9:16 vertical animated videos — 30 chart pages across A-shares, Hong Kong, the US and cryptocurrency. Fetch, preview and export an H.264 MP4 ready to post.",
    "zh-hans": "把股市数据变成 9:16 竖屏动画视频——A股、港股、美股与加密货币共三十种图表页，取数、预览并导出可直接发布的 H.264 MP4。",
    "zh-hant": "把股市數據變成 9:16 豎屏動畫視頻——A股、港股、美股與加密貨幣共三十種圖表頁，取數、預覽並匯出可直接發佈的 H.264 MP4。",
    "ja": "株・市場データを9:16の縦型アニメ動画に。A株・香港・米国・暗号資産の30種類のチャートページで、データ取得からH.264 MP4書き出しまで。",
    "ko": "주식·시장 데이터를 9:16 세로 애니메이션 영상으로. A주·홍콩·미국·암호화폐의 30가지 차트 페이지로 데이터 조회부터 H.264 MP4 내보내기까지.",
    "de": "Verwandelt Börsendaten in vertikale 9:16-Animationen — 30 Diagrammseiten für A-Aktien, Hongkong, USA und Krypto, inklusive H.264-MP4-Export.",
    "fr": "Transformez les données boursières en animations verticales 9:16 — 30 pages de graphiques (A-shares, Hong Kong, USA, crypto) avec export MP4 H.264.",
    "es": "Convierte datos de bolsa en animaciones verticales 9:16 — 30 páginas de gráficos (A-shares, Hong Kong, EE. UU. y cripto) con exportación MP4 H.264.",
    "it": "Trasforma i dati di borsa in animazioni verticali 9:16 — 30 pagine di grafici (azioni A, Hong Kong, USA e crypto) con esportazione MP4 H.264.",
    "pt-br": "Transforma dados de mercado em animações verticais 9:16 — 30 páginas de gráficos (A-shares, Hong Kong, EUA e cripto) com exportação em MP4 H.264.",
    "ru": "Превращает биржевые данные в вертикальные анимации 9:16 — 30 страниц графиков (A-акции, Гонконг, США, крипто) с экспортом MP4 H.264.",
    "pl": "Zamienia dane giełdowe w pionowe animacje 9:16 — 30 stron wykresów (akcje A, Hongkong, USA, krypto) z eksportem MP4 H.264.",
    "cs": "Proměňuje burzovní data ve svislé animace 9:16 — 30 stran grafů (akcie A, Hongkong, USA, krypto) s exportem MP4 H.264.",
    "tr": "Borsa verilerini 9:16 dikey animasyonlara dönüştürür — A hisseleri, Hong Kong, ABD ve kripto için 30 grafik sayfası, H.264 MP4 dışa aktarımıyla.",
}

KEYWORDS = {
    "en-us": ["stock market video", "market animation", "A-share charts",
              "sector race", "candlestick video", "vertical video", "MP4 export"],
    "zh-hans": ["行情动画", "A股数据可视化", "板块竞速", "K线动画", "定投回测", "竖屏视频", "MP4导出"],
    "zh-hant": ["行情動畫", "A股數據可視化", "板塊競速", "K線動畫", "定投回測", "豎屏視頻", "MP4匯出"],
    "ja": ["株価アニメ", "市場データ可視化", "セクターレース", "ローソク足",
           "積立投資シミュレーション", "縦型動画", "MP4書き出し"],
    "ko": ["주식 애니메이션", "시장 데이터 시각화", "섹터 레이스", "캔들 차트",
           "적립식 투자", "세로형 영상", "MP4 내보내기"],
    "de": ["Börsenvideo", "Marktanimation", "Aktiencharts", "Sektorrennen",
           "Candlestick", "Vertikalvideo", "MP4-Export"],
    "fr": ["vidéo bourse", "animation marché", "graphiques actions",
           "course sectorielle", "chandeliers", "vidéo verticale", "export MP4"],
    "es": ["vídeo de bolsa", "animación de mercado", "gráficos de acciones",
           "carrera sectorial", "velas japonesas", "vídeo vertical", "exportar MP4"],
    "it": ["video di borsa", "animazione mercato", "grafici azionari",
           "gara settoriale", "candele giapponesi", "video verticale", "esportazione MP4"],
    "pt-br": ["vídeo de bolsa", "animação de mercado", "gráficos de ações",
              "corrida de setores", "candlesticks", "vídeo vertical", "exportar MP4"],
    "ru": ["биржевое видео", "анимация рынка", "графики акций", "гонка секторов",
           "японские свечи", "вертикальное видео", "экспорт MP4"],
    "pl": ["wideo giełdowe", "animacja rynku", "wykresy akcji", "wyścig sektorów",
           "świece japońskie", "wideo pionowe", "eksport MP4"],
    "cs": ["burzovní video", "animace trhu", "grafy akcí", "závod sektorů",
           "japonské svíčky", "svislé video", "export MP4"],
    "tr": ["borsa videosu", "piyasa animasyonu", "hisse grafikleri", "sektör yarışı",
           "mum grafikleri", "dikey video", "MP4 dışa aktarma"],
}

# ---- parse docs/store-listing.md ----------------------------------------------

LANG_HEADERS = [
    ("zh-hans", "简体中文（zh-Hans）"), ("zh-hant", "繁體中文（zh-Hant）"),
    ("en-us", "English (en-US)"), ("ja", "日本語（ja）"), ("ko", "한국어 (ko)"),
    ("de", "Deutsch (de)"), ("fr", "Français (fr)"), ("it", "Italiano (it)"),
    ("es", "Español (es)"), ("pt-br", "Português (Brasil) (pt-BR)"),
    ("pl", "Polski (pl)"), ("cs", "Čeština (cs)"), ("ru", "Русский (ru)"),
    ("tr", "Türkçe (tr)"),
]
# The section heading for description / what's-new / features in each language.
SEC = {
    "zh-hans": ("说明", "此版本的新增功能", "产品功能"),
    "zh-hant": ("說明", "此版本的新增功能", "產品功能"),
    "en-us": ("Description", "What's new in this version", "Product features"),
    "ja": ("説明", "このバージョンの新機能", "製品の機能"),
    "ko": ("설명", "이 버전의 새 기능", "제품 기능"),
    "de": ("Beschreibung", "Neu in dieser Version", "Produktfunktionen"),
    "fr": ("Description", "Nouveautés de cette version", "Fonctionnalités"),
    "it": ("Descrizione", "Novità di questa versione", "Funzionalità del prodotto"),
    "es": ("Descripción", "Novedades de esta versión", "Funciones del producto"),
    "pt-br": ("Descrição", "Novidades desta versão", "Funcionalidades do produto"),
    "pl": ("Opis", "Co nowego w tej wersji", "Funkcje produktu"),
    "cs": ("Popis", "Co je nového v této verzi", "Funkce produktu"),
    "ru": ("Описание", "Что нового в этой версии", "Функции продукта"),
    "tr": ("Açıklama", "Bu sürümdeki yenilikler", "Ürün özellikleri"),
}


def parse_listing():
    lines = io.open(LISTING, encoding="utf-8").read().splitlines()
    spans = []
    for i, (code, title) in enumerate(LANG_HEADERS):
        start = next(n for n, ln in enumerate(lines)
                     if ln.strip() == "## " + title)
        end = (next(n for n, ln in enumerate(lines[start + 1:], start + 1)
                    if ln.startswith("## "))
               if i + 1 < len(LANG_HEADERS) else len(lines))
        spans.append((code, lines[start:end]))

    out = {}
    for code, block in spans:
        d_head, w_head, f_head = SEC[code]

        def section(head):
            s = next(n for n, ln in enumerate(block)
                     if ln.strip() == "### " + head)
            e = next((n for n, ln in enumerate(block[s + 1:], s + 1)
                      if ln.startswith("### ")), len(block))
            return [ln for ln in block[s + 1:e]]

        desc = [ln.rstrip() for ln in section(d_head) if ln.strip()]
        whats = [ln.rstrip() for ln in section(w_head) if ln.strip()]
        feats = [ln[2:].rstrip() for ln in section(f_head)
                 if ln.startswith("- ")]
        bullets = [re.sub(r"^•\s*", "", ln).rstrip()
                   for ln in desc if ln.startswith("•")]
        out[code] = {"desc": desc, "whats": "\n".join(whats),
                     "feats": feats, "bullets": bullets}
    return out


# ---- parse the template CSV ---------------------------------------------------

def parse_template():
    text = io.open(TEMPLATE, encoding="utf-8-sig").read()
    rows = list(csv.reader(text.splitlines()))
    header, body = rows[0], rows[1:]
    langs = header[4:]
    return header, langs, body


LIMIT = 200  # Partner Center: each product feature is at most 200 characters.


def split_bullet(bullet, limit=LIMIT):
    """One listing bullet -> one or more <=200-char features.

    A short bullet passes through whole. A long one — in practice the
    thirty-chart list — is split after its label into numbered parts
    ("Thirty charts: (1/4) …"), the way the old CSV already did for English.
    """
    if len(bullet) <= limit:
        return [bullet]
    m = re.match(r"^(.*?[:：])\s*(.*)$", bullet)
    if not m:
        return [bullet[i:i + limit] for i in range(0, len(bullet), limit)]
    label, rest = m.group(1), m.group(2)
    joiner = "、" if "、" in rest else ", "
    items = [s for s in re.split(r"、|,\s*", rest) if s]
    room = limit - len(label) - 12  # leave space for " (n/N)"
    chunks, cur = [], ""
    for item in items:
        cand = (cur + joiner + item) if cur else item
        if cur and len(cand) > room:
            chunks.append(cur)
            cur = item
        else:
            cur = cand
    if cur:
        chunks.append(cur)
    return ["%s (%d/%d) %s" % (label, i + 1, len(chunks), ch)
            for i, ch in enumerate(chunks)]


# ---- assemble -----------------------------------------------------------------

def main():
    listing = parse_listing()
    header, langs, body = parse_template()
    col = {lang: 4 + i for i, lang in enumerate(langs)}

    # Product features: every language's own six bullets, long ones split to the
    # 200-character limit, so all fourteen languages come out with the same shape
    # and every Feature row in the CSV is exactly what the markdown shows.
    feats = {lang: [f for b in listing[lang]["feats"]
                    for f in split_bullet(b)]
             for lang in langs}

    # --- the CSV -------------------------------------------------------------
    def set_field(name, value_by_lang):
        row = next(r for r in body if r and r[0] == name)
        for lang in langs:
            row[col[lang]] = value_by_lang.get(lang, "")

    set_field("Title", {l: APP_TITLE for l in langs})
    set_field("ShortDescription", SHORT_DESC)
    set_field("Description", {l: "\n".join(listing[l]["desc"]) for l in langs})
    set_field("ReleaseNotes", {l: listing[l]["whats"] for l in langs})
    set_field("DevStudio", {l: DEV_STUDIO for l in langs})
    set_field("CopyrightTrademarkInformation", {l: COPYRIGHT for l in langs})
    set_field("OverrideLogosForWin10", {l: "False" for l in langs})

    # Partner Center allows twenty feature rows; rewrite all of them so stale
    # values from an older pass cannot survive past this language's count.
    for n in range(1, 21):
        set_field("Feature%d" % n,
                  {l: (feats[l][n - 1] if n <= len(feats[l]) else "")
                   for l in langs})

    for n in range(1, 8):
        set_field("SearchTerm%d" % n,
                  {l: (KEYWORDS[l][n - 1] if n <= len(KEYWORDS[l]) else "")
                   for l in langs})

    for n, (stem, bullet) in enumerate(SHOTS, 1):
        shot, cap = {}, {}
        for lang in langs:
            folder = SHOT_LANGS.get(lang, "en-us")
            shot[lang] = "screenshots/%s/%s.png" % (folder, stem)
            text = listing[lang]["bullets"][bullet] if bullet < len(
                listing[lang]["bullets"]) else ""
            cap[lang] = text[:200]
        set_field("DesktopScreenshot%d" % n, shot)
        set_field("DesktopScreenshotCaption%d" % n, cap)

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(header)
    w.writerows(body)
    csv_path = os.path.join(ROOT, os.path.basename(TEMPLATE))
    io.open(csv_path, "w", encoding="utf-8-sig", newline="").write(buf.getvalue())

    # --- the markdown --------------------------------------------------------
    md = io.StringIO()
    md.write("# %s — Microsoft Store 上架文案（store listing）\n\n" % APP_TITLE)
    md.write("> 生成自 `docs/store-listing.md`（14 种语言的既有文案）与 "
             "`docs/listingData-9NGDNH0CCW7L-1152921505702020674.csv`"
             "（Partner Center listing data 模板，功能要点已按每条 ≤200 字符预拆分），"
             "由 `tools/build-store-listing.py` 产出。**两个产物的同名字段出自同一份解析文本，不会漂移。**\n\n")
    md.write("> 字符上限（Partner Center）：说明 ≤ 10000；此版本的新增功能 ≤ 1500；"
             "产品功能每条 ≤ 200（最多 20 条）；搜索关键词最多 7 个，每个 ≤ 30 字符。\n\n---\n\n")
    md.write("## 提交摘要\n\n")
    md.write("| 项 | 值 |\n|---|---|\n")
    md.write("| 应用名称（Title，全部语言统一） | %s |\n" % APP_TITLE)
    md.write("| 发布者 / 开发者（DevStudio） | %s |\n" % DEV_STUDIO)
    md.write("| 版权（Copyright/Trademark） | %s |\n" % COPYRIGHT)
    md.write("| 本版版本号 / 更新日志对应版本 | %s（%s） |\n" % (VERSION, VERSION_DATE))
    md.write("| 桌面截图 | 9 张 × %s，1920×1020 PNG，见 `screenshots/`；"
             "其余区域回退 en-us（Partner Center 自动回退默认语言） |\n"
             % "、".join(sorted(SHOT_LANGS.values())))
    md.write("| 上架数据文件 | `listingData-9NGDNH0CCW7L-1152921505702020674.csv`"
             "（Partner Center 模板：每行一个字段，每个区域一列） |\n\n")
    md.write("> 命名约定：包标识 `MarketMotionStudio` 在所有市场固定不变；"
             "中文市场的应用内显示名为「行情指标动画工作室」，商店 Title 统一为 `%s`；"
             "其余市场显示 Market Motion Studio。两者都指向同一包标识。\n\n---\n\n" % APP_TITLE)

    for code, title in LANG_HEADERS:
        d = listing[code]
        md.write("## %s\n\n" % title)
        md.write("### 应用标题\n\n%s\n\n" % APP_TITLE)
        md.write("### 简短描述\n\n%s\n\n" % SHORT_DESC[code])
        md.write("### 完整描述\n\n")
        for ln in d["desc"]:
            md.write(ln + "  \n" if not ln.startswith("•") else ln.rstrip() + "  \n")
        md.write("\n### 功能要点\n\n")
        for f in feats[code]:
            md.write("- %s\n" % f)
        md.write("\n### 关键词\n\n%s\n\n" % "、".join(KEYWORDS[code]))
        md.write("### 更新日志（%s）\n\n%s\n\n" % (VERSION, d["whats"]))
        md.write("### 截图\n\n")
        for n, (stem, bullet) in enumerate(SHOTS, 1):
            folder = SHOT_LANGS.get(code, "en-us")
            md.write("%d. `%s/%s/%s.png` — %s\n"
                     % (n, "screenshots", folder, stem,
                        d["bullets"][bullet][:200]))
        md.write("\n---\n\n")

    md.write("## 适用语言\n\n")
    md.write("| 商店语言 | 界面语言 | 截图集 |\n|---|---|---|\n")
    ui = {"en-us": "en-US", "zh-hans": "zh-Hans", "zh-hant": "zh-Hant",
          "ja": "ja", "ko": "ko", "de": "de", "fr": "fr", "it": "it",
          "es": "es", "pt-br": "pt-BR", "pl": "pl", "cs": "cs", "ru": "ru", "tr": "tr"}
    for code, title in LANG_HEADERS:
        md.write("| %s | Strings/%s/Resources.resw | %s |\n"
                 % (title, ui[code], SHOT_LANGS.get(code, "en-us（回退）")))
    md.write("\n## 待人工补充 / 留意\n\n")
    md.write("1. 商店 Logo 与宣传图（StoreLogo300x300、PromoImage1920x1080 等）不在本次范围，"
             "CSV 中留空，提交前需在 Partner Center 上传。\n")
    md.write("2. 硬件要求（MinimumHardwareReq/RecommendedHardwareReq）留空，按 Partner Center 默认。\n")
    md.write("3. 功能要点由各语言既有要点统一拆分到每条 ≤ 200 字符（长条即三十图表清单，拆成 4 条编号小段），"
             "14 种语言条数一致；CSV 的 Feature1..N 与本文档逐字相同。\n")
    md.write("4. 加密货币十一页只在中国大陆以外的市场提供——描述里已写明，提交时保持勾选的市场范围与此一致。\n")

    io.open(os.path.join(ROOT, "store-listing.md"), "w",
            encoding="utf-8", newline="\n").write(md.getvalue())

    print("written:", csv_path)
    print("written:", os.path.join(ROOT, "store-listing.md"))
    for code, _ in LANG_HEADERS:
        d = listing[code]
        print("%-8s desc %3d lines, %2d bullets, %d features, whats %d chars"
              % (code, len(d["desc"]), len(d["bullets"]), len(d["feats"]),
                 len(d["whats"])))


if __name__ == "__main__":
    main()
