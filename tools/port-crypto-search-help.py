# -*- coding: utf-8 -*-
r"""把手册里那句「这里没有搜索框」换掉 —— 14 份，只换后半句。

**为什么要换。** 加密 K 线那一章本来写着：这里没有搜索框，因为两个源对同一个币种的写法
不同、敲进去的名字哪个源都到不了。现在控件上有框了，这句话从「解释一个设计」变成了
「描述一个不存在的东西」—— 手册里最不该留的就是这种句子，它读起来仍然通顺。

**只动后半句**：前半句（十二个币种是哪些、为什么是这十二个）与框无关，一个字不改。
所以每份按各语言那句「没有搜索框」的开头**切开整行**，前半段原样留下，接上新写的后半段。

**新后半句说的是匹配口径** —— 「本界面语言的币种名或代码」：这是这一版真正的行为，
也是它和那个股票页搜索框的区别（那边按代码/名字/拼音搜任意标的，这边是在固定的十二个
里收窄）。翻译跟着各语言已有的措辞走（「币种」「銘柄」「코인」「Münze」「moneta」…）。

**幂等靠标记词**：第二次运行时那句「没有搜索框」已经不在，脚本按新句的标记词认出
「已经换过了」并跳过，不报错、不重复接。两边都找不到才是真的出问题。

BOM **照抄原文**（这 14 份实测**不带** BOM，不要顺手加上 —— `port-crypto-help.py` 的
注释说它们带，那是过时的）。

用法：python tools\port-crypto-search-help.py
"""
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 每份一条：(原句开头, 新后半段)。新后半段以语言习惯决定要不要前导空格。
RULES = {
    "en-US": (
        "There is no search box",
        " The box above narrows the row to what is typed, matching the name this "
        "interface language spells or the code — type bit or BTC and Bitcoin is what "
        "comes up. A coin already chosen stays on the row whatever is typed, so the "
        "count below always has its coins on screen."),

    "de": (
        "Es gibt kein Suchfeld",
        " Das Feld darüber grenzt die Zeile auf das Eingetippte ein: Es passt auf den "
        "Namen, den diese Oberflächensprache schreibt, oder auf den Code — bit wie BTC "
        "findet Bitcoin. Eine bereits gewählte Münze bleibt stehen, egal was eingetippt "
        "wurde."),

    "es": (
        "No hay buscador",
        " El cuadro de arriba estrecha la fila a lo que se escribe: coincide con el "
        "nombre que escribe este idioma de interfaz o con el código — bit y BTC "
        "encuentran Bitcoin. Una moneda ya elegida sigue en la fila se escriba lo que "
        "se escriba."),

    "fr": (
        "Il n'y a pas de champ de recherche",
        " Le champ ci-dessus resserre la ligne sur ce qui est saisi : il correspond au "
        "nom qu'écrit cette langue d'interface ou au code — bit comme BTC trouvent "
        "Bitcoin. Une cryptomonnaie déjà choisie reste affichée quoi qu'on saisisse."),

    "it": (
        "Non c'è una casella di ricerca",
        " Il campo qui sopra restringe la riga a ciò che si digita: corrisponde al nome "
        "che scrive questa lingua dell'interfaccia o al codice — bit e BTC trovano "
        "Bitcoin. Una moneta già scelta resta nella riga qualunque cosa si digiti."),

    "pl": (
        "Nie ma pola wyszukiwania",
        " Pole powyżej zawęża wiersz do wpisanego tekstu: pasuje do nazwy, którą "
        "zapisuje ten język interfejsu, albo do kodu — bit i BTC znajdują Bitcoin. "
        "Wybrana moneta zostaje w wierszu niezależnie od wpisanego tekstu."),

    "pt-BR": (
        "Não há caixa de busca",
        " A caixa acima estreita a linha ao que for digitado: corresponde ao nome que "
        "este idioma da interface escreve ou ao código — bit e BTC encontram Bitcoin. "
        "Uma moeda já escolhida continua na linha independentemente do que for "
        "digitado."),

    "cs": (
        "Vyhledávací pole tu není",
        " Pole výše zužuje řádek na zadaný text: odpovídá názvu, který píše tento jazyk "
        "rozhraní, nebo kódu — bit i BTC najdou Bitcoin. Zvolená mince na řádku zůstává "
        "bez ohledu na zadaný text."),

    "tr": (
        "Arama kutusu yok",
        " Yukarıdaki kutu satırı yazılana göre daraltır: bu arayüz dilinin yazdığı adla "
        "ya da kodla eşleşir — bit de BTC de Bitcoin'i bulur. Seçilmiş bir coin ne "
        "yazılırsa yazılsın satırda kalır."),

    "ru": (
        "Поля поиска нет",
        " Поле выше сужает строку до введённого: оно совпадает с названием, которое "
        "пишет этот язык интерфейса, или с кодом — bit и BTC находят Bitcoin. Уже "
        "выбранная монета остаётся в строке независимо от ввода."),

    "ja": (
        "検索欄はありません",
        "上の欄でこの行を絞り込めます。この画面の言語での銘柄名かコードに一致し"
        "ます——bit でも BTC でも Bitcoin が出ます。すでに選んだコインは、何を入力"
        "しても行に残ります。"),

    "ko": (
        "검색창은 없습니다",
        " 위의 입력란으로 이 줄을 좁힐 수 있습니다. 이 화면 언어의 코인 이름이나 "
        "코드와 일치합니다 — bit 이든 BTC 든 Bitcoin 이 나옵니다. 이미 고른 코인은 "
        "무엇을 입력해도 줄에 남습니다."),

    "zh-Hant": (
        "這裡沒有搜尋框",
        "上面的框可以把這一行收窄：按本介面語言裡的幣種名或代碼匹配——輸入「比特」"
        "或「BTC」都能找到比特幣。已經選中的幣不會因為不匹配而消失。"),

    "zh-Hans": (
        "这里没有搜索框",
        "上面的框可以把这一行收窄：按本界面语言里的币种名或代码匹配——输入「比特」"
        "或「BTC」都能找到比特币。已选中的币不会因为不匹配而消失。"),
}

# 「已经换过」的标记：新句里都有、旧句里都没有的一个词。
DONE = {
    "en-US": "narrows the row to what is typed",
    "de": "grenzt die Zeile auf das Eingetippte ein",
    "es": "estrecha la fila a lo que se escribe",
    "fr": "resserre la ligne sur ce qui est saisi",
    "it": "restringe la riga a ciò che si digita",
    "pl": "zawęża wiersz do wpisanego tekstu",
    "pt-BR": "estreita a linha ao que for digitado",
    "cs": "zužuje řádek na zadaný text",
    "tr": "satırı yazılana göre daraltır",
    "ru": "сужает строку до введённого",
    "ja": "この行を絞り込めます",
    "ko": "이 줄을 좁힐 수 있습니다",
    "zh-Hant": "可以把這一行收窄",
    "zh-Hans": "可以把这一行收窄",
}


def main():
    for tag, (old_marker, tail) in RULES.items():
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")

        if DONE[tag] in text:
            print(f"{tag}: already switched")
            continue

        lines = text.split("\n")
        hit = None

        for i, line in enumerate(lines):
            if old_marker in line:
                hit = i
                break

        assert hit is not None, f"{tag}: neither the old sentence nor the new one is here"

        head = lines[hit].partition(old_marker)[0].rstrip()

        lines[hit] = head + tail

        out = "\n".join(lines)

        path.write_bytes(out.encode("utf-8-sig") if had_bom else out.encode("utf-8"))

        print(f"{tag}: switched (line {hit + 1})")


if __name__ == "__main__":
    main()
