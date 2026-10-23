# -*- coding: utf-8 -*-
r"""给「持仓」对话框加上列表导入/导出所需的 13 条文案（14 种语言）。

新控件两枚按钮（导入列表 / 导出列表）、两条完成回执、四条逐行报错理由、一条
「还有几行有问题」、一条空文件、一条编码不对。

**编码那条是有原因的**：Excel 在中文环境下「CSV（逗号分隔）」存的是系统代码页
（GBK），拿 UTF-8 解会得到一串 U+FFFD —— 也就是用户这次报的「乱码」。所以导入端
严格按 UTF-8 读，读不动就明说「另存为 CSV UTF-8」，不猜。

插在 `PortfolioDialogAddButton.Content` 那一行之后（对话框自己的词条聚在一起）。
resw 是 LF 带 BOM，照原样写回。幂等：键已在文件里就跳过。
"""

import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.STRINGS

ANCHOR = 'name="PortfolioDialogAddButton.Content"'

# key -> {lang: value}
STRINGS = {
    "PortfolioDialogImport.Content": {
        "zh-Hans": "导入列表", "zh-Hant": "匯入列表", "en-US": "Import list",
        "ja": "リストをインポート", "ko": "목록 가져오기", "de": "Liste importieren",
        "fr": "Importer la liste", "it": "Importa elenco", "es": "Importar lista",
        "pt-BR": "Importar lista", "pl": "Importuj listę", "cs": "Importovat seznam",
        "ru": "Импорт списка", "tr": "Listeyi içe aktar",
    },
    "PortfolioDialogExport.Content": {
        "zh-Hans": "导出列表", "zh-Hant": "匯出列表", "en-US": "Export list",
        "ja": "リストをエクスポート", "ko": "목록 내보내기", "de": "Liste exportieren",
        "fr": "Exporter la liste", "it": "Esporta elenco", "es": "Exportar lista",
        "pt-BR": "Exportar lista", "pl": "Eksportuj listę", "cs": "Exportovat seznam",
        "ru": "Экспорт списка", "tr": "Listeyi dışa aktar",
    },
    "PortfolioDialogExportDone": {
        "zh-Hans": "已导出 {0} 行。",
        "zh-Hant": "已匯出 {0} 列。",
        "en-US": "Exported {0} rows.",
        "ja": "{0} 行を書き出しました。",
        "ko": "{0}개 행을 내보냈습니다.",
        "de": "{0} Zeilen exportiert.",
        "fr": "{0} lignes exportées.",
        "it": "Esportate {0} righe.",
        "es": "Se exportaron {0} filas.",
        "pt-BR": "{0} linhas exportadas.",
        "pl": "Wyeksportowano {0} wierszy.",
        "cs": "Exportováno {0} řádků.",
        "ru": "Экспортировано строк: {0}.",
        "tr": "{0} satır dışa aktarıldı.",
    },
    "PortfolioDialogImportDone": {
        "zh-Hans": "已导入 {0} 行，列表已按文件更新。",
        "zh-Hant": "已匯入 {0} 列，列表已按檔案更新。",
        "en-US": "Imported {0} rows — the list now matches the file.",
        "ja": "{0} 行を取り込み、一覧をファイルの内容にしました。",
        "ko": "{0}개 행을 가져왔고 목록이 파일과 같아졌습니다.",
        "de": "{0} Zeilen importiert — die Liste entspricht jetzt der Datei.",
        "fr": "{0} lignes importées — la liste correspond désormais au fichier.",
        "it": "Importate {0} righe — l'elenco ora corrisponde al file.",
        "es": "Se importaron {0} filas — la lista ya coincide con el archivo.",
        "pt-BR": "{0} linhas importadas — a lista agora corresponde ao arquivo.",
        "pl": "Zaimportowano {0} wierszy — lista odpowiada teraz plikowi.",
        "cs": "Importováno {0} řádků — seznam teď odpovídá souboru.",
        "ru": "Импортировано строк: {0} — список теперь совпадает с файлом.",
        "tr": "{0} satır içe aktarıldı — liste artık dosyayla aynı.",
    },
    "PortfolioDialogImportEmpty": {
        "zh-Hans": "文件里没有可用的持仓行。",
        "zh-Hant": "檔案裡沒有可用的持倉列。",
        "en-US": "There are no holdings rows in that file.",
        "ja": "ファイルに使える保有行がありません。",
        "ko": "파일에 쓸 수 있는 보유 행이 없습니다.",
        "de": "In dieser Datei stehen keine Bestandszeilen.",
        "fr": "Ce fichier ne contient aucune ligne de position.",
        "it": "In quel file non ci sono righe di posizioni.",
        "es": "Ese archivo no tiene filas de posiciones.",
        "pt-BR": "Esse arquivo não tem linhas de posições.",
        "pl": "W tym pliku nie ma wierszy pozycji.",
        "cs": "V tom souboru nejsou žádné řádky pozic.",
        "ru": "В этом файле нет строк позиций.",
        "tr": "O dosyada pozisyon satırı yok.",
    },
    "PortfolioDialogImportRow": {
        "zh-Hans": "第 {0} 行：{1}",
        "zh-Hant": "第 {0} 列：{1}",
        "en-US": "Line {0}: {1}",
        "ja": "{0} 行目：{1}",
        "ko": "{0}번째 줄: {1}",
        "de": "Zeile {0}: {1}",
        "fr": "Ligne {0} : {1}",
        "it": "Riga {0}: {1}",
        "es": "Fila {0}: {1}",
        "pt-BR": "Linha {0}: {1}",
        "pl": "Wiersz {0}: {1}",
        "cs": "Řádek {0}: {1}",
        "ru": "Строка {0}: {1}",
        "tr": "Satır {0}: {1}",
    },
    "PortfolioDialogImportMore": {
        "zh-Hans": "另有 {0} 行有问题，改好再导入。",
        "zh-Hant": "另有 {0} 列有問題，改好再匯入。",
        "en-US": "{0} more lines have problems — fix them and import again.",
        "ja": "ほかに {0} 行問題があります。直してから取り込んでください。",
        "ko": "문제가 있는 줄이 {0}개 더 있습니다. 고친 뒤 다시 가져오세요.",
        "de": "{0} weitere Zeilen haben Fehler — korrigiere sie und importiere erneut.",
        "fr": "{0} autres lignes posent problème — corrigez-les puis importez à nouveau.",
        "it": "Altre {0} righe hanno problemi — correggile e importa di nuovo.",
        "es": "Otras {0} filas tienen problemas — corríjalas y vuelva a importar.",
        "pt-BR": "Outras {0} linhas têm problemas — corrija e importe de novo.",
        "pl": "Jeszcze {0} wierszy ma błędy — popraw je i zaimportuj ponownie.",
        "cs": "Dalších {0} řádků má problémy — opravte je a importujte znovu.",
        "ru": "Ещё в {0} строках есть ошибки — исправьте их и импортируйте снова.",
        "tr": "{0} satırda daha sorun var — düzeltip yeniden aktarın.",
    },
    "PortfolioDialogRowColumns": {
        "zh-Hans": "列数不对，应为「代码,名称,数量,成本」",
        "zh-Hant": "欄位數不對，應為「代碼,名稱,數量,成本」",
        "en-US": "Wrong column count — expected code,name,shares,cost",
        "ja": "列数が違います（コード,名称,数量,コスト）",
        "ko": "열 개수가 맞지 않습니다(코드,이름,수량,단가)",
        "de": "Falsche Spaltenzahl — erwartet code,name,shares,cost",
        "fr": "Nombre de colonnes incorrect — attendu code,name,shares,cost",
        "it": "Numero di colonne errato — atteso code,name,shares,cost",
        "es": "Número de columnas incorrecto — se espera code,name,shares,cost",
        "pt-BR": "Número de colunas errado — esperado code,name,shares,cost",
        "pl": "Zła liczba kolumn — oczekiwano code,name,shares,cost",
        "cs": "Špatný počet sloupců — očekává se code,name,shares,cost",
        "ru": "Неверное число столбцов — ожидается code,name,shares,cost",
        "tr": "Sütun sayısı yanlış — code,name,shares,cost bekleniyor",
    },
    "PortfolioDialogRowCode": {
        "zh-Hans": "代码看不懂", "zh-Hant": "代碼看不懂", "en-US": "That code is not readable",
        "ja": "コードが読めません", "ko": "코드를 읽을 수 없습니다", "de": "Dieser Code ist nicht lesbar",
        "fr": "Ce code est illisible", "it": "Quel codice non è leggibile",
        "es": "Ese código no se puede leer", "pt-BR": "Esse código não é legível",
        "pl": "Ten kod jest nieczytelny", "cs": "Ten kód je nečitelný",
        "ru": "Этот код не читается", "tr": "Bu kod okunamıyor",
    },
    "PortfolioDialogRowShares": {
        "zh-Hans": "数量要是正数", "zh-Hant": "數量要是正數",
        "en-US": "The share count must be a positive number",
        "ja": "数量は正の数にしてください", "ko": "수량은 양수여야 합니다",
        "de": "Die Stückzahl muss eine positive Zahl sein",
        "fr": "La quantité doit être un nombre positif",
        "it": "La quantità deve essere un numero positivo",
        "es": "La cantidad debe ser un número positivo",
        "pt-BR": "A quantidade deve ser um número positivo",
        "pl": "Liczba akcji musi być dodatnia", "cs": "Počet akcií musí být kladné číslo",
        "ru": "Количество акций должно быть положительным числом",
        "tr": "Adet pozitif bir sayı olmalı",
    },
    "PortfolioDialogRowCost": {
        "zh-Hans": "成本不是数字", "zh-Hant": "成本不是數字",
        "en-US": "The cost is not a number",
        "ja": "コストが数値ではありません", "ko": "단가가 숫자가 아닙니다",
        "de": "Die Kosten sind keine Zahl", "fr": "Le coût n'est pas un nombre",
        "it": "Il costo non è un numero", "es": "El coste no es un número",
        "pt-BR": "O custo não é um número", "pl": "Koszt nie jest liczbą",
        "cs": "Náklad není číslo", "ru": "Цена не является числом",
        "tr": "Maliyet bir sayı değil",
    },
    "PortfolioDialogRowDuplicate": {
        "zh-Hans": "代码和上面重复", "zh-Hant": "代碼和上面重複",
        "en-US": "That code repeats a line above",
        "ja": "コードが上の行と重複しています", "ko": "코드가 위 줄과 중복됩니다",
        "de": "Dieser Code wiederholt eine Zeile darüber",
        "fr": "Ce code répète une ligne au-dessus",
        "it": "Quel codice ripete una riga sopra",
        "es": "Ese código repite una fila anterior",
        "pt-BR": "Esse código repete uma linha acima",
        "pl": "Ten kod powtarza wiersz powyżej", "cs": "Ten kód opakuje řádek výše",
        "ru": "Этот код повторяет строку выше", "tr": "Bu kod yukarıdaki satırı tekrarlıyor",
    },
    "PortfolioDialogSheetEncoding": {
        "zh-Hans": "这个文件不是 UTF-8：请在 Excel 里另存为「CSV UTF-8」再导入。",
        "zh-Hant": "這個檔案不是 UTF-8：請在 Excel 裡另存為「CSV UTF-8」再匯入。",
        "en-US": "That file is not UTF-8 — save it as \"CSV UTF-8\" in Excel and import it again.",
        "ja": "このファイルは UTF-8 ではありません。Excel で「CSV UTF-8」として保存し直してください。",
        "ko": "이 파일은 UTF-8이 아닙니다. Excel에서 'CSV UTF-8'로 저장한 뒤 다시 가져오세요.",
        "de": "Diese Datei ist nicht UTF-8 — speichere sie in Excel als \"CSV UTF-8\" und importiere erneut.",
        "fr": "Ce fichier n'est pas en UTF-8 — enregistrez-le en « CSV UTF-8 » dans Excel puis réimportez.",
        "it": "Quel file non è UTF-8 — salvalo come \"CSV UTF-8\" in Excel e importa di nuovo.",
        "es": "Ese archivo no es UTF-8 — guárdelo como «CSV UTF-8» en Excel y vuelva a importar.",
        "pt-BR": "Esse arquivo não é UTF-8 — salve como \"CSV UTF-8\" no Excel e importe de novo.",
        "pl": "Ten plik nie jest w UTF-8 — zapisz go w Excelu jako \"CSV UTF-8\" i zaimportuj ponownie.",
        "cs": "Ten soubor není v UTF-8 — uložte ho v Excelu jako \"CSV UTF-8\" a importujte znovu.",
        "ru": "Этот файл не в UTF-8 — сохраните его в Excel как «CSV UTF-8» и импортируйте снова.",
        "tr": "Bu dosya UTF-8 değil — Excel'de \"CSV UTF-8\" olarak kaydedip yeniden aktarın.",
    },
}


def xml(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    for tag in lt.LANGS:
        path = ROOT / tag / "Resources.resw"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")

        # 锚点在 `PortfolioDialogAddButton.Content` 那一行，插在它后面。
        anchor = next((i for i, line in enumerate(lines) if ANCHOR in line), None)

        assert anchor is not None, f"{tag}: 找不到锚点 {ANCHOR}"

        added = []

        for key, table in STRINGS.items():
            if f'name="{key}"' in body:
                continue

            added.append(f'  <data name="{key}"><value>{xml(table[tag])}</value></data>')

        if not added:
            print(f"{tag:9} already there")
            continue

        lines[anchor + 1:anchor + 1] = added

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +{len(added)}")


if __name__ == "__main__":
    main()
