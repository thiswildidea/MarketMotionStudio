# -*- coding: utf-8 -*-
r"""清掉导入对话框里截图时代的两句残留文案（14 种语言）。

截图导入整个删掉之后，界面上还有两句在说一个不存在的东西：

- `PortfolioImportHint.Text` —— 对话框顶上那句「选一张当日成交的截图，或者直接把成交记录
  粘进来」。读者照它说的去找选截图的按钮，找不到 —— 提示句指着一个被删掉的入口，比没有
  提示句更糟。
- `PortfolioImportReading` —— 点「导入表格」之后状态行写的「正在识别截图…」。读的是
  表格，不是截图。

resw 是 LF 带 BOM，照原样写回。幂等：值已经等于新句就跳过。
"""

import io
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.STRINGS

HINT = {
    "zh-Hans": "把成交记录粘进来，或导入当日委托记录的表格（.xlsx）。解析结果逐行确认，全部读对才能导入。",
    "zh-Hant": "把成交記錄貼進來，或匯入當日委託記錄的表格（.xlsx）。解析結果逐行確認，全部讀對才能匯入。",
    "en-US": "Paste the day's fills in, or import the day's order sheet (.xlsx). The parse is confirmed row by row; everything must read cleanly before it can be applied.",
    "ja": "当日の約定を貼り付けるか、当日の注文記録の表（.xlsx）を取り込みます。解析結果を一行ずつ確認し、すべて読めたときだけ取り込めます。",
    "ko": "당일 체결을 붙여넣거나 당일 주문 기록 표(.xlsx)를 가져옵니다. 해석 결과를 한 줄씩 확인하며 모두 읽혀야 가져올 수 있습니다.",
    "de": "Füge die Geschäfte des Tages ein oder importiere das Orderblatt des Tages (.xlsx). Das Ergebnis wird Zeile für Zeile geprüft; erst wenn alles lesbar ist, kann es übernommen werden.",
    "fr": "Collez les ordres du jour ou importez la feuille d'ordres du jour (.xlsx). Le résultat se vérifie ligne par ligne ; tout doit être lisible pour pouvoir l'appliquer.",
    "it": "Incolla le operazioni del giorno o importa il foglio ordini della giornata (.xlsx). Il risultato si controlla riga per riga; tutto deve essere leggibile per poterlo applicare.",
    "es": "Pegue las operaciones del día o importe la hoja de órdenes del día (.xlsx). El resultado se revisa fila por fila; todo tiene que leerse bien para poder aplicarlo.",
    "pt-BR": "Cole as operações do dia ou importe a planilha de ordens do dia (.xlsx). O resultado é conferido linha por linha; tudo precisa ser lido corretamente para ser aplicado.",
    "pl": "Wklej transakcje dnia albo zaimportuj arkusz zleceń dnia (.xlsx). Wynik sprawdza się wiersz po wierszu; import jest możliwy, gdy wszystko jest czytelne.",
    "cs": "Vložte obchody dne nebo importujte tabulku s pokyny dne (.xlsx). Výsledek se kontroluje řádek po řádku; importovat lze, jen když je vše čitelné.",
    "ru": "Вставьте сделки дня или импортируйте таблицу заявок дня (.xlsx). Результат проверяется построчно; применить можно, только когда всё прочитано.",
    "tr": "Günün işlemlerini yapıştırın veya günün emir tablosunu (.xlsx) içe aktarın. Sonuç satır satır kontrol edilir; her şey okunmadan aktarılamaz.",
}

READING = {
    "zh-Hans": "正在读取表格…",
    "zh-Hant": "正在讀取表格…",
    "en-US": "Reading the sheet…",
    "ja": "表を読み込んでいます…",
    "ko": "표를 읽고 있습니다…",
    "de": "Tabelle wird gelesen…",
    "fr": "Lecture de la feuille…",
    "it": "Lettura del foglio…",
    "es": "Leyendo la hoja…",
    "pt-BR": "Lendo a planilha…",
    "pl": "Czytanie arkusza…",
    "cs": "Načítá se tabulka…",
    "ru": "Чтение таблицы…",
    "tr": "Tablo okunuyor…",
}


def replace_value(text, key, new):
    """把 `<data name="{key}"><value>…</value>` 的值换成 new。返回 (新文本, 是否改了)。"""
    pattern = re.compile(
        r'(<data name="%s"><value>).*?(</value></data>)' % re.escape(key))

    hit = pattern.search(text)

    if hit is None:
        raise AssertionError(f"找不到 {key}")

    if hit.group(1) + new + hit.group(2) == hit.group(0):
        return text, False

    return pattern.sub(lambda m: m.group(1) + new + m.group(2), text, count=1), True


def main():
    for tag in lt.LANGS:
        path = ROOT / tag / "Resources.resw"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        changed = 0

        for key, new in ((f"PortfolioImportHint.Text", HINT[tag]),
                         ("PortfolioImportReading", READING[tag])):
            body, done = replace_value(body, key, new)
            changed += 1 if done else 0

        if not changed:
            print(f"{tag:9} already there")
            continue

        rebuilt = body.replace("\n", "\r\n") if crlf else body

        with io.open(path, "w", encoding="utf-8-sig", newline="") as handle:
            handle.write(rebuilt)

        print(f"{tag:9} +{changed}")


if __name__ == "__main__":
    main()
