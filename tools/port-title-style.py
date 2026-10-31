# -*- coding: utf-8 -*-
"""Adds the title-style captions to all fourteen resource files.

24 keys: the per-page main-title extras (font/size/rotation/wrap cap), the subtitle group on
the portfolio page, the same as global defaults on the settings page, and the two combo items
the code fills by hand (「跟随全局」 and 「默认」) — the latter two carry `.Content` because
`Strings.Get` reads the dotted name as a path, the same trap the skin items fell into.

Idempotent: an existing key is left alone, and the file's BOM and LF endings are preserved by
editing the decoded text and writing it back the way it was read.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

KEYS = [
    "PortfolioPnlTitleFont.Header",
    "PortfolioPnlTitleSize.Header",
    "PortfolioPnlTitleRotation.Header",
    "PortfolioPnlTitleLines.Header",
    "PortfolioPnlFollowGlobal.Content",
    "PortfolioPnlSubtitleHeader.Text",
    "PortfolioPnlShowSubtitle.Content",
    "PortfolioPnlSubtitleText.PlaceholderText",
    "PortfolioPnlSubtitleSkin.Header",
    "PortfolioPnlSubtitleFont.Header",
    "PortfolioPnlSubtitleSize.Header",
    "PortfolioPnlSubtitleLines.Header",
    "PortfolioPnlSubtitleColour.Text",
    "SettingsTitleFont.Text",
    "SettingsTitleSize.Text",
    "SettingsTitleRotation.Text",
    "SettingsTitleLines.Text",
    "SettingsSubtitleHeader.Text",
    "SettingsSubtitleNote.Text",
    "SettingsSubtitleSkin.Text",
    "SettingsSubtitleFont.Text",
    "SettingsSubtitleSize.Text",
    "SettingsSubtitleLines.Text",
    "SettingsFollowDefault.Content",
]

ROWS = {
    "zh-Hans": (
        "主标题字体", "主标题字号", "主标题旋转", "换行上限", "跟随全局",
        "副标题", "显示副标题", "副标题文本，回车可换行",
        "副标题样式", "副标题字体", "副标题字号", "副标题换行上限", "颜色",
        "主标题字体", "主标题字号", "主标题旋转", "换行上限",
        "副标题默认", "各页面的副标题文本归页面自己；这里只是样式默认，页面未配置的项落到这里。",
        "副标题样式", "副标题字体", "副标题字号", "副标题换行上限", "默认",
    ),
    "zh-Hant": (
        "主標題字體", "主標題字號", "主標題旋轉", "換行上限", "跟隨全域",
        "副標題", "顯示副標題", "副標題文字，Enter 可換行",
        "副標題樣式", "副標題字體", "副標題字號", "副標題換行上限", "顏色",
        "主標題字體", "主標題字號", "主標題旋轉", "換行上限",
        "副標題預設", "各頁面的副標題文字歸頁面自己；這裡只是樣式預設，頁面未配置的項落到這裡。",
        "副標題樣式", "副標題字體", "副標題字號", "副標題換行上限", "預設",
    ),
    "en-US": (
        "Title font", "Title size", "Title rotation", "Wrap limit", "Follow global",
        "Subtitle", "Show subtitle", "Subtitle text — press Enter for a new line",
        "Subtitle style", "Subtitle font", "Subtitle size", "Subtitle wrap limit", "Colour",
        "Title font", "Title size", "Title rotation", "Wrap limit",
        "Subtitle defaults", "Each page owns its subtitle's text; these are only the style defaults a page's unconfigured fields fall back to.",
        "Subtitle style", "Subtitle font", "Subtitle size", "Subtitle wrap limit", "Default",
    ),
    "ja": (
        "タイトルのフォント", "タイトルのサイズ", "タイトルの回転", "折り返し上限", "グローバルに従う",
        "サブタイトル", "サブタイトルを表示", "サブタイトルのテキスト（Enterで改行）",
        "サブタイトルのスタイル", "サブタイトルのフォント", "サブタイトルのサイズ", "サブタイトルの折り返し上限", "色",
        "タイトルのフォント", "タイトルのサイズ", "タイトルの回転", "折り返し上限",
        "サブタイトルの既定", "サブタイトルのテキストは各ページのものです。ここはスタイルの既定値です。",
        "サブタイトルのスタイル", "サブタイトルのフォント", "サブタイトルのサイズ", "サブタイトルの折り返し上限", "既定",
    ),
    "ko": (
        "제목 글꼴", "제목 크기", "제목 회전", "줄바꿈 제한", "전역 설정 따르기",
        "부제목", "부제목 표시", "부제목 텍스트 (Enter로 줄바꿈)",
        "부제목 스타일", "부제목 글꼴", "부제목 크기", "부제목 줄바꿈 제한", "색",
        "제목 글꼴", "제목 크기", "제목 회전", "줄바꿈 제한",
        "부제목 기본값", "부제목 텍스트는 각 페이지의 것입니다. 여기는 스타일 기본값입니다.",
        "부제목 스타일", "부제목 글꼴", "부제목 크기", "부제목 줄바꿈 제한", "기본값",
    ),
    "de": (
        "Titelschriftart", "Titelgröße", "Titeldrehung", "Zeilenumbruch-Limit", "Global folgen",
        "Untertitel", "Untertitel anzeigen", "Untertiteltext — Enter für eine neue Zeile",
        "Untertitel-Stil", "Untertitel-Schriftart", "Untertitelgröße", "Untertitel-Umbruchlimit", "Farbe",
        "Titelschriftart", "Titelgröße", "Titeldrehung", "Zeilenumbruch-Limit",
        "Untertitel-Standards", "Der Untertiteltext gehört jeder Seite selbst; hier liegen nur die Stil-Standards, auf die nicht gesetzte Felder fallen.",
        "Untertitel-Stil", "Untertitel-Schriftart", "Untertitelgröße", "Untertitel-Umbruchlimit", "Standard",
    ),
    "fr": (
        "Police du titre", "Taille du titre", "Rotation du titre", "Limite de lignes", "Suivre le global",
        "Sous-titre", "Afficher le sous-titre", "Texte du sous-titre — Entrée pour aller à la ligne",
        "Style du sous-titre", "Police du sous-titre", "Taille du sous-titre", "Limite de lignes du sous-titre", "Couleur",
        "Police du titre", "Taille du titre", "Rotation du titre", "Limite de lignes",
        "Valeurs par défaut du sous-titre", "Le texte du sous-titre appartient à chaque page ; ceci n'est que le style par défaut des champs non définis.",
        "Style du sous-titre", "Police du sous-titre", "Taille du sous-titre", "Limite de lignes du sous-titre", "Par défaut",
    ),
    "es": (
        "Fuente del título", "Tamaño del título", "Rotación del título", "Límite de líneas", "Seguir el global",
        "Subtítulo", "Mostrar subtítulo", "Texto del subtítulo — Enter para una línea nueva",
        "Estilo del subtítulo", "Fuente del subtítulo", "Tamaño del subtítulo", "Límite de líneas del subtítulo", "Color",
        "Fuente del título", "Tamaño del título", "Rotación del título", "Límite de líneas",
        "Valores predeterminados del subtítulo", "El texto del subtítulo pertenece a cada página; esto es solo el estilo predeterminado de los campos sin configurar.",
        "Estilo del subtítulo", "Fuente del subtítulo", "Tamaño del subtítulo", "Límite de líneas del subtítulo", "Predeterminado",
    ),
    "it": (
        "Carattere del titolo", "Dimensione del titolo", "Rotazione del titolo", "Limite di righe", "Segui il globale",
        "Sottotitolo", "Mostra sottotitolo", "Testo del sottotitolo — Invio per andare a capo",
        "Stile del sottotitolo", "Carattere del sottotitolo", "Dimensione del sottotitolo", "Limite di righe del sottotitolo", "Colore",
        "Carattere del titolo", "Dimensione del titolo", "Rotazione del titolo", "Limite di righe",
        "Impostazioni predefinite del sottotitolo", "Il testo del sottotitolo appartiene a ogni pagina; qui ci sono solo gli stili predefiniti dei campi non configurati.",
        "Stile del sottotitolo", "Carattere del sottotitolo", "Dimensione del sottotitolo", "Limite di righe del sottotitolo", "Predefinito",
    ),
    "pt-BR": (
        "Fonte do título", "Tamanho do título", "Rotação do título", "Limite de linhas", "Seguir o global",
        "Subtítulo", "Mostrar subtítulo", "Texto do subtítulo — Enter para uma nova linha",
        "Estilo do subtítulo", "Fonte do subtítulo", "Tamanho do subtítulo", "Limite de linhas do subtítulo", "Cor",
        "Fonte do título", "Tamanho do título", "Rotação do título", "Limite de linhas",
        "Padrões do subtítulo", "O texto do subtítulo pertence a cada página; aqui ficam apenas os padrões de estilo dos campos não configurados.",
        "Estilo do subtítulo", "Fonte do subtítulo", "Tamanho do subtítulo", "Limite de linhas do subtítulo", "Padrão",
    ),
    "ru": (
        "Шрифт заголовка", "Размер заголовка", "Наклон заголовка", "Лимит строк", "Как в общих",
        "Подзаголовок", "Показывать подзаголовок", "Текст подзаголовка — Enter для новой строки",
        "Стиль подзаголовка", "Шрифт подзаголовка", "Размер подзаголовка", "Лимит строк подзаголовка", "Цвет",
        "Шрифт заголовка", "Размер заголовка", "Наклон заголовка", "Лимит строк",
        "Подзаголовок по умолчанию", "Текст подзаголовка принадлежит самой странице; здесь только стиль по умолчанию для ненастроенных полей.",
        "Стиль подзаголовка", "Шрифт подзаголовка", "Размер подзаголовка", "Лимит строк подзаголовка", "По умолчанию",
    ),
    "pl": (
        "Czcionka tytułu", "Rozmiar tytułu", "Obrót tytułu", "Limit wierszy", "Według globalnych",
        "Podtytuł", "Pokaż podtytuł", "Tekst podtytułu — Enter dla nowego wiersza",
        "Styl podtytułu", "Czcionka podtytułu", "Rozmiar podtytułu", "Limit wierszy podtytułu", "Kolor",
        "Czcionka tytułu", "Rozmiar tytułu", "Obrót tytułu", "Limit wierszy",
        "Domyślne podtytułu", "Tekst podtytułu należy do strony; tutaj są tylko domyślne style dla nieustawionych pól.",
        "Styl podtytułu", "Czcionka podtytułu", "Rozmiar podtytułu", "Limit wierszy podtytułu", "Domyślnie",
    ),
    "cs": (
        "Písmo titulku", "Velikost titulku", "Natočení titulku", "Limit řádků", "Podle globálních",
        "Podtitul", "Zobrazit podtitul", "Text podtitulu — Enter pro nový řádek",
        "Styl podtitulu", "Písmo podtitulu", "Velikost podtitulu", "Limit řádků podtitulu", "Barva",
        "Písmo titulku", "Velikost titulku", "Natočení titulku", "Limit řádků",
        "Výchozí podtitul", "Text podtitulu patří stránce; zde jsou pouze výchozí styly pro nenastavená pole.",
        "Styl podtitulu", "Písmo podtitulu", "Velikost podtitulu", "Limit řádků podtitulu", "Výchozí",
    ),
    "tr": (
        "Başlık yazı tipi", "Başlık boyutu", "Başlık döndürme", "Satır sınırı", "Geneli izle",
        "Alt başlık", "Alt başlığı göster", "Alt başlık metni — yeni satır için Enter",
        "Alt başlık stili", "Alt başlık yazı tipi", "Alt başlık boyutu", "Alt başlık satır sınırı", "Renk",
        "Başlık yazı tipi", "Başlık boyutu", "Başlık döndürme", "Satır sınırı",
        "Alt başlık varsayılanları", "Alt başlık metni sayfanındır; burada yalnızca yapılandırılmamış alanlar için varsayılan stiller vardır.",
        "Alt başlık stili", "Alt başlık yazı tipi", "Alt başlık boyutu", "Alt başlık satır sınırı", "Varsayılan",
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
