# -*- coding: utf-8 -*-
r"""给 14 份手册的「实时持仓收益」一章补一条：整份列表能导出成表格、也能整份换掉。

2026-10-23 新增（「管理持仓」里两枚按钮）：导出 CSV（`code,name,shares,cost`，UTF-8 带
BOM，Excel 双击不乱码）；导入整份替换，逐行校验（列数 / 代码 / 数量 / 成本 / 重复），
有一条不合就一条都不改，报错带行号。

插在上一轮那条「管理持仓」之后（`port-portfolio-dialog-docs.py` 写的），所以锚点取它的
开头。幂等：新句子已经在文件里就跳过。帮助手册 LF 无 BOM，照原样写回。
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP

CHAPTER = lt.chapter_of("NavPortfolioPnl")

SHEET = {
    "zh-Hans": "- **整份列表能导出成表格，也能从表格整份换掉。** 导出的是 CSV：代码、名称、数量、成本四列，UTF-8 带 BOM，Excel 双击打开不乱码。改完存回同一格式再导入，列表就按文件换掉；有一条读不动（列数不对、代码看不懂、数量不是正数、成本不是数字、代码重复）就一条都不改，报错带行号，改好再导。",
    "zh-Hant": "- **整份列表能匯出成表格，也能從表格整份換掉。** 匯出的是 CSV：代碼、名稱、數量、成本四欄，UTF-8 帶 BOM，Excel 雙擊打開不亂碼。改完存回同一格式再匯入，列表就按檔案換掉；有一列讀不動（欄位數不對、代碼看不懂、數量不是正數、成本不是數字、代碼重複）就一列都不改，報錯帶列號，改好再匯。",
    "en-US": "- **The whole list exports as a sheet, and imports back over itself.** Export writes a CSV of code, name, shares and cost — UTF-8 with a BOM, so Excel opens it by double-click without mojibake. Edit it, save it in the same shape and import it, and the list becomes the file; one unreadable line (wrong column count, an unreadable code, a share count that is not positive, a cost that is not a number, a repeated code) and nothing is changed at all, with the line numbers reported so they can be fixed first.",
    "ja": "- **一覧まるごとを表に書き出し、表から丸ごと差し替えられます。** 書き出すのは CSV で、コード・名称・数量・コストの四列、UTF-8（BOM 付き）なので Excel でダブルクリックしても文字化けしません。同じ形で保存し直して取り込めば、一覧はファイルの内容になります。読めない行が一つでもあれば（列数違い、コードが読めない、数量が正の数でない、コストが数値でない、コードの重複）何も変えず、行番号を添えて知らせます。",
    "ko": "- **목록 전체를 표로 내보내고, 표에서 통째로 바꿀 수 있다.** 내보내는 것은 CSV이며 코드·이름·수량·단가 네 열, UTF-8(BOM 포함)이라 Excel에서 두 번 눌러도 글자가 깨지지 않는다. 같은 형식으로 저장해 다시 가져오면 목록이 파일대로 바뀐다. 읽을 수 없는 줄이 하나라도 있으면(열 개수, 코드, 수량, 단가, 중복) 아무것도 바꾸지 않고 줄 번호와 함께 알려 준다.",
    "de": "- **Die ganze Liste lässt sich als Tabelle ausgeben und von dort wieder übernehmen.** Der Export ist eine CSV mit Code, Name, Stückzahl und Kosten — UTF-8 mit BOM, also öffnet Excel sie per Doppelklick ohne Zeichensalat. Bearbeiten, im selben Format speichern und importieren: Die Liste wird zur Datei. Eine unlesbare Zeile (falsche Spaltenzahl, unlesbarer Code, keine positive Stückzahl, keine Zahl als Kosten, doppelter Code) und es ändert sich gar nichts — die Zeilennummern stehen dabei.",
    "fr": "- **Toute la liste s'exporte en tableur et s'importe par-dessus.** L'export est un CSV code, nom, titres, coût — UTF-8 avec BOM, donc Excel l'ouvre d'un double-clic sans charabia. Modifiez, enregistrez dans la même forme, importez : la liste devient le fichier. Une seule ligne illisible (nombre de colonnes, code, quantité, coût, doublon) et rien n'est modifié, avec les numéros de ligne pour la corriger.",
    "it": "- **L'intero elenco si esporta come foglio e si reimporta sopra.** L'esportazione è un CSV con codice, nome, azioni e costo — UTF-8 con BOM, così Excel lo apre con un doppio clic senza caratteri strani. Modifica, salva nello stesso formato e importa: l'elenco diventa il file. Una sola riga illeggibile (numero di colonne, codice, quantità, costo, doppione) e non cambia nulla, con i numeri di riga indicati.",
    "es": "- **La lista entera se exporta como hoja y se importa encima.** La exportación es un CSV con código, nombre, acciones y coste — UTF-8 con BOM, así Excel lo abre con doble clic sin caracteres raros. Edite, guarde con la misma forma e importe: la lista pasa a ser el archivo. Una sola fila ilegible (columnas, código, cantidad, coste, duplicado) y no cambia nada, con los números de fila a la vista.",
    "pt-BR": "- **A lista inteira é exportada como planilha e importada por cima.** A exportação é um CSV com código, nome, ações e custo — UTF-8 com BOM, então o Excel abre com dois cliques sem caracteres estranhos. Edite, salve no mesmo formato e importe: a lista passa a ser o arquivo. Uma linha ilegível (colunas, código, quantidade, custo, repetido) e nada é alterado, com os números das linhas indicados.",
    "pl": "- **Całą listę można wyeksportować jako arkusz i wczytać z powrotem.** Eksport to CSV z kolumnami kod, nazwa, liczba akcji i koszt — UTF-8 z BOM, więc Excel otwiera go dwuklikiem bez krzaków. Popraw, zapisz w tym samym kształcie i zaimportuj: lista staje się plikiem. Jeden nieczytelny wiersz (liczba kolumn, kod, liczba akcji, koszt, powtórzenie) i nic się nie zmienia — z podanymi numerami wierszy.",
    "cs": "- **Celý seznam lze vyexportovat jako tabulku a z ní zase načíst.** Export je CSV s kódem, názvem, počtem akcií a nákladem — UTF-8 s BOM, takže ho Excel otevře dvojklikem bez změť znaků. Upravte, uložte ve stejném tvaru a importujte: seznam se stane souborem. Jediný nečitelný řádek (počet sloupců, kód, počet akcií, náklad, opakování) a nezmění se nic — s čísly řádků.",
    "ru": "- **Весь список выгружается в таблицу и загружается обратно поверх.** Экспорт — CSV с колонками код, имя, количество, цена — UTF-8 с BOM, поэтому Excel открывает его двойным щелчком без кракозябр. Исправьте, сохраните в том же виде и импортируйте: список станет файлом. Одна нечитаемая строка (столбцы, код, количество, цена, повтор) — и не меняется ничего, а номера строк названы.",
    "tr": "- **Listenin tamamı tablo olarak dışa aktarılır ve tablodan geri yüklenir.** Dışa aktarım kod, ad, adet ve maliyet sütunlu bir CSV'dir — UTF-8 ve BOM'lu, böylece Excel çift tıklamayla bozulmadan açar. Düzenleyip aynı biçimde kaydedin ve aktarın: liste dosyanın kendisi olur. Okunamayan tek satır (sütun sayısı, kod, adet, maliyet, tekrar) varsa hiçbir şey değişmez; satır numaraları bildirilir.",
}

ANCHOR = {
    "zh-Hans": "- **「管理持仓」打开就是最新持仓。**",
    "zh-Hant": "- **「管理持倉」打開就是最新持倉。**",
    "en-US": "- **\"Holdings\" opens on the latest figures.**",
    "ja": "- **「保有銘柄」は最新の数で開く。**",
    "ko": "- **'보유 종목'은 최신 수치로 열린다.**",
    "de": "- **„Bestand“ öffnet mit den neuesten Zahlen.**",
    "fr": "- **« Positions » s'ouvre sur les dernières valeurs.**",
    "it": "- **«Posizioni» si apre sui valori più recenti.**",
    "es": "- **«Posiciones» se abre con las cifras más recientes.**",
    "pt-BR": "- **\"Posições\" abre com os números mais recentes.**",
    "pl": "- **„Pozycje” otwierają się na najnowszych liczbach.**",
    "cs": "- **„Pozice” se otevírají s nejnovějšími čísly.**",
    "ru": "- **«Позиции» открываются на самых свежих цифрах.**",
    "tr": "- **\"Pozisyonlar\" en güncel rakamlarla açılır.**",
}


def main():
    for tag in lt.LANGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")
        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
        start = heads[CHAPTER]
        end = heads[CHAPTER + 1] if CHAPTER + 1 < len(heads) else len(lines)

        section = [lines[i] for i in range(start, end)]

        if any(line.strip() == SHEET[tag] for line in section):
            print(f"{tag:9} already there")
            continue

        at = next((i for i in range(start, end) if lines[i].startswith(ANCHOR[tag])), None)

        assert at is not None, f"{tag}: 找不到「管理持仓」那条"

        block = ["", SHEET[tag]] if lines[at + 1].strip() == "" else [SHEET[tag]]
        lines[at + 1:at + 1] = block

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +1")


if __name__ == "__main__":
    main()
