# -*- coding: utf-8 -*-
"""Adds the title-dialog captions to all fourteen resource files.

7 keys: the two menu items the gear opens (main title / subtitle), the two dialog titles,
the hint inside the dialog, the dialog's confirm button, and the badge placeholder the
preview falls back to when the text is empty. The existing field captions (字体/字号/旋转/
换行上限/颜色/样式名) are reused from port-title-style.py, so they are not touched here.

Idempotent, and it keeps the file's BOM and LF endings the way it found them.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

KEYS = [
    "PortfolioPnlTitleEdit.Text",
    "PortfolioPnlSubtitleEdit.Text",
    "PortfolioPnlTitleDialog",
    "PortfolioPnlSubtitleDialog",
    "PortfolioPnlStyleHint.Text",
    "PortfolioPnlStyleOk",
    "PortfolioPnlTitleBadge",
]

ROWS = {
    "zh-Hans": (
        "主标题样式…", "副标题样式…", "主标题样式", "副标题样式",
        "未配置的项跟随「设置」页的全局默认；打开「跟随全局」即交还该选项。",
        "确定", "标题",
    ),
    "zh-Hant": (
        "主標題樣式…", "副標題樣式…", "主標題樣式", "副標題樣式",
        "未配置的項跟隨「設定」頁的全域預設；開啟「跟隨全域」即交還該選項。",
        "確定", "標題",
    ),
    "en-US": (
        "Main title style…", "Subtitle style…", "Main title style", "Subtitle style",
        "Unset fields follow the global defaults on the settings page; switching 「Follow global」 back on hands the choice over.",
        "OK", "Title",
    ),
    "ja": (
        "タイトルのスタイル…", "サブタイトルのスタイル…", "タイトルのスタイル", "サブタイトルのスタイル",
        "未設定の項目は設定ページのグローバル既定に従います。「グローバルに従う」をオンにするとそちらに戻ります。",
        "OK", "タイトル",
    ),
    "ko": (
        "제목 스타일…", "부제목 스타일…", "제목 스타일", "부제목 스타일",
        "설정되지 않은 항목은 설정 페이지의 전역 기본값을 따릅니다. 「전역 설정 따르기」를 켜면 그쪽으로 돌아갑니다.",
        "확인", "제목",
    ),
    "de": (
        "Haupttitel-Stil…", "Untertitel-Stil…", "Haupttitel-Stil", "Untertitel-Stil",
        "Nicht gesetzte Felder folgen den globalen Standards der Einstellungsseite; „Global folgen“ gibt die Wahl dorthin zurück.",
        "OK", "Titel",
    ),
    "fr": (
        "Style du titre…", "Style du sous-titre…", "Style du titre", "Style du sous-titre",
        "Les champs non définis suivent les valeurs globales de la page de réglages ; réactiver « Suivre le global » lui rend la décision.",
        "OK", "Titre",
    ),
    "es": (
        "Estilo del título…", "Estilo del subtítulo…", "Estilo del título", "Estilo del subtítulo",
        "Los campos sin configurar siguen los valores globales de la página de ajustes; activar «Seguir el global» le devuelve la decisión.",
        "Aceptar", "Título",
    ),
    "it": (
        "Stile del titolo…", "Stile del sottotitolo…", "Stile del titolo", "Stile del sottotitolo",
        "I campi non configurati seguono i valori globali della pagina delle impostazioni; riattivare «Segui il globale» restituisce la scelta.",
        "OK", "Titolo",
    ),
    "pt-BR": (
        "Estilo do título…", "Estilo do subtítulo…", "Estilo do título", "Estilo do subtítulo",
        "Os campos não configurados seguem os padrões globais da página de ajustes; ativar «Seguir o global» devolve a escolha.",
        "OK", "Título",
    ),
    "ru": (
        "Стиль заголовка…", "Стиль подзаголовка…", "Стиль заголовка", "Стиль подзаголовка",
        "Ненастроенные поля следуют общим значениям на странице настроек; включение «Как в общих» возвращает выбор туда.",
        "ОК", "Заголовок",
    ),
    "pl": (
        "Styl tytułu…", "Styl podtytułu…", "Styl tytułu", "Styl podtytułu",
        "Nieustawione pola mają wartości globalne ze strony ustawień; włączenie „Według globalnych” oddaje tam wybór.",
        "OK", "Tytuł",
    ),
    "cs": (
        "Styl titulku…", "Styl podtitulu…", "Styl titulku", "Styl podtitulu",
        "Nenastavená pole sledují globální výchozí hodnoty na stránce nastavení; zapnutí „Podle globálních“ volbu vrací zpět.",
        "OK", "Titulek",
    ),
    "tr": (
        "Başlık stili…", "Alt başlık stili…", "Başlık stili", "Alt başlık stili",
        "Yapılandırılmamış alanlar ayarlar sayfasındaki genel varsayılanları izler; «Geneli izle» açılırsa seçim oraya döner.",
        "Tamam", "Başlık",
    ),
}

ANCHOR = '  <data name="PortfolioPnlFeeKongMinimum.Header">'


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


changed = 0

for resw in sorted(ROOT.glob("*/Resources.resw")):
    lang = resw.parent.name

    if lang not in ROWS:
        print(f"{lang}: no row")
        continue

    raw = resw.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")

    values = ROWS[lang]
    assert len(values) == len(KEYS), lang

    wanted = [
        f'  <data name="{key}"><value>{esc(value)}</value></data>'
        for key, value in zip(KEYS, values)
    ]

    missing = [line for line in wanted if line.split('"')[1] not in text]

    if not missing:
        print(f"{lang}: already present")
        continue

    at = text.index(ANCHOR)
    end = text.index("\n", at) + 1
    text = text[:end] + "\n".join(missing) + "\n" + text[end:]

    resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))
    changed += 1
    print(f"{lang}: added {len(missing)}")

print("files changed:", changed)
