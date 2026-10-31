#!/usr/bin/env python3
"""Adds the snapshot-import and overwrite-rule strings to all fourteen resource files.

Two features, six sentences:

  * 管理持仓 gains **导入初始持仓** — the file its own 导出初始持仓 writes, read back in.
    Four keys: the button, what a successful import says, and two refusals (lines that do not
    read; a file whose rows disagree about the day).

  * 导入成交记录 gains a **rule** for its 覆盖导入 box rather than a free switch: only a record
    of many days — which is to say, one whose every row carries a date — may replace the archive.
    Two keys: the tooltip on either side of that rule.

Idempotent: a file already carrying `LedgerBaselineImport` is left alone. resw keeps its BOM
and LF endings.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

ZH = {
    "LedgerBaselineImport.Content": "导入初始持仓",
    "LedgerBaselineImported": "已载入初始持仓：{0}，共 {1} 只",
    "LedgerBaselineImportRejected": "这个文件有读不懂的行：第 {0} 行。整份都没有导入。",
    "LedgerBaselineImportMixedDays": "这个文件的日期不止一个——初始持仓只能是一天的。整份都没有导入。",
    "LedgerBaselineImportShape": "这不是导出的初始持仓列表（应为 day,code,name,shares,cost 五列）。",
    "OverwriteAllowedHint": "这份带日期，是历史成交记录，可以用它整份替换已有档案。",
    "OverwriteBlockedHint": "只有导入带日期的历史成交记录时才能覆盖；当日委托只会追加。",
}

T = {
    "en-US": {
        "LedgerBaselineImport.Content": "Import a snapshot",
        "LedgerBaselineImported": "Snapshot loaded: {0}, {1} positions",
        "LedgerBaselineImportRejected": "This file has lines that do not read: {0}. Nothing was imported.",
        "LedgerBaselineImportMixedDays": "This file names more than one day — a snapshot is one day's. Nothing was imported.",
        "LedgerBaselineImportShape": "This is not an exported snapshot (it wants the five columns day,code,name,shares,cost).",
        "OverwriteAllowedHint": "This one carries dates, so it is a record of trades: it may replace the archive outright.",
        "OverwriteBlockedHint": "Only a dated record of trades may overwrite; a day's orders are appended.",
    },
    "zh-Hant": {
        "LedgerBaselineImport.Content": "匯入初始持倉",
        "LedgerBaselineImported": "已載入初始持倉：{0}，共 {1} 檔",
        "LedgerBaselineImportRejected": "這個檔案有讀不懂的行：第 {0} 行。整份都沒有匯入。",
        "LedgerBaselineImportMixedDays": "這個檔案的日期不止一個——初始持倉只能是一天的。整份都沒有匯入。",
        "LedgerBaselineImportShape": "這不是匯出的初始持倉清單（應為 day,code,name,shares,cost 五欄）。",
        "OverwriteAllowedHint": "這份帶日期，是歷史成交記錄，可以用它整份替換既有檔案。",
        "OverwriteBlockedHint": "只有匯入帶日期的歷史成交記錄時才能覆蓋；當日委託只會追加。",
    },
    "cs": {
        "LedgerBaselineImport.Content": "Importovat počáteční pozici",
        "LedgerBaselineImported": "Počáteční pozice načtena: {0}, {1} pozic",
        "LedgerBaselineImportRejected": "Soubor má nečitelné řádky: {0}. Nic nebylo importováno.",
        "LedgerBaselineImportMixedDays": "Soubor uvádí více než jeden den — počáteční pozice je jeden den. Nic nebylo importováno.",
        "LedgerBaselineImportShape": "Toto není exportovaná počáteční pozice (čeká se pět sloupců day,code,name,shares,cost).",
        "OverwriteAllowedHint": "Tento soubor nese data, je to záznam obchodů: může archiv nahradit celý.",
        "OverwriteBlockedHint": "Přepsat lze jen záznam obchodů s daty; denní objednávky se připojují.",
    },
    "de": {
        "LedgerBaselineImport.Content": "Anfangsposition importieren",
        "LedgerBaselineImported": "Anfangsposition geladen: {0}, {1} Positionen",
        "LedgerBaselineImportRejected": "Diese Datei hat unlesbare Zeilen: {0}. Es wurde nichts importiert.",
        "LedgerBaselineImportMixedDays": "Diese Datei nennt mehr als einen Tag — eine Anfangsposition ist ein Tag. Es wurde nichts importiert.",
        "LedgerBaselineImportShape": "Das ist keine exportierte Anfangsposition (erwartet werden die fünf Spalten day,code,name,shares,cost).",
        "OverwriteAllowedHint": "Diese Datei trägt Daten, ist also ein Handelsarchiv: sie darf das bestehende ersetzen.",
        "OverwriteBlockedHint": "Nur ein datiertes Handelsarchiv darf ersetzen; Tagesaufträge werden angehängt.",
    },
    "es": {
        "LedgerBaselineImport.Content": "Importar posición inicial",
        "LedgerBaselineImported": "Posición inicial cargada: {0}, {1} posiciones",
        "LedgerBaselineImportRejected": "Este archivo tiene líneas ilegibles: {0}. No se importó nada.",
        "LedgerBaselineImportMixedDays": "Este archivo indica más de un día — una posición inicial es de un día. No se importó nada.",
        "LedgerBaselineImportShape": "Esto no es una posición inicial exportada (se esperan las cinco columnas day,code,name,shares,cost).",
        "OverwriteAllowedHint": "Este archivo lleva fechas, es un registro de operaciones: puede sustituir el archivo completo.",
        "OverwriteBlockedHint": "Solo un registro de operaciones con fechas puede sobrescribir; las órdenes del día se añaden.",
    },
    "fr": {
        "LedgerBaselineImport.Content": "Importer la position initiale",
        "LedgerBaselineImported": "Position initiale chargée : {0}, {1} positions",
        "LedgerBaselineImportRejected": "Ce fichier contient des lignes illisibles : {0}. Rien n'a été importé.",
        "LedgerBaselineImportMixedDays": "Ce fichier indique plusieurs jours — une position initiale n'en a qu'un. Rien n'a été importé.",
        "LedgerBaselineImportShape": "Ce n'est pas une position initiale exportée (cinq colonnes attendues : day,code,name,shares,cost).",
        "OverwriteAllowedHint": "Ce fichier porte des dates, c'est un registre d'opérations : il peut remplacer l'archive entière.",
        "OverwriteBlockedHint": "Seul un registre daté peut remplacer ; les ordres du jour sont ajoutés.",
    },
    "it": {
        "LedgerBaselineImport.Content": "Importa posizione iniziale",
        "LedgerBaselineImported": "Posizione iniziale caricata: {0}, {1} posizioni",
        "LedgerBaselineImportRejected": "Questo file ha righe illeggibili: {0}. Non è stato importato nulla.",
        "LedgerBaselineImportMixedDays": "Questo file indica più di un giorno — una posizione iniziale è di un giorno. Non è stato importato nulla.",
        "LedgerBaselineImportShape": "Questa non è una posizione iniziale esportata (servono le cinque colonne day,code,name,shares,cost).",
        "OverwriteAllowedHint": "Questo file porta date, è un registro di operazioni: può sostituire l'archivio intero.",
        "OverwriteBlockedHint": "Solo un registro datato può sovrascrivere; gli ordini del giorno vengono aggiunti.",
    },
    "ja": {
        "LedgerBaselineImport.Content": "初期保有を読み込む",
        "LedgerBaselineImported": "初期保有用を読み込みました：{0}、{1} 銘柄",
        "LedgerBaselineImportRejected": "読めない行があります：{0} 行目。1 件も読み込んでいません。",
        "LedgerBaselineImportMixedDays": "このファイルは日付が複数あります。初期保有は 1 日分だけです。1 件も読み込んでいません。",
        "LedgerBaselineImportShape": "これは書き出した初期保有リストではありません（day,code,name,shares,cost の 5 列が必要です）。",
        "OverwriteAllowedHint": "日付が入っているので約定記録です。既存の記録を丸ごと置き換えられます。",
        "OverwriteBlockedHint": "日付入りの約定記録だけが上書きできます。当日の注文は追加のみです。",
    },
    "ko": {
        "LedgerBaselineImport.Content": "초기 보유 불러오기",
        "LedgerBaselineImported": "초기 보유를 불러왔습니다: {0}, {1} 종목",
        "LedgerBaselineImportRejected": "읽을 수 없는 행이 있습니다: {0}행. 아무것도 가져오지 않았습니다.",
        "LedgerBaselineImportMixedDays": "이 파일은 날짜가 여러 개입니다. 초기 보유는 하루치입니다. 아무것도 가져오지 않았습니다.",
        "LedgerBaselineImportShape": "내보낸 초기 보유 목록이 아닙니다(day,code,name,shares,cost 다섯 열이 필요합니다).",
        "OverwriteAllowedHint": "날짜가 있으므로 거래 기록입니다. 기존 기록을 통째로 바꿀 수 있습니다.",
        "OverwriteBlockedHint": "날짜가 있는 거래 기록만 덮어쓸 수 있습니다. 당일 주문은 추가됩니다.",
    },
    "pl": {
        "LedgerBaselineImport.Content": "Importuj pozycję początkową",
        "LedgerBaselineImported": "Wczytano pozycję początkową: {0}, {1} pozycji",
        "LedgerBaselineImportRejected": "Ten plik ma nieczytelne wiersze: {0}. Nic nie zaimportowano.",
        "LedgerBaselineImportMixedDays": "Ten plik podaje więcej niż jeden dzień — pozycja początkowa jest z jednego dnia. Nic nie zaimportowano.",
        "LedgerBaselineImportShape": "To nie jest wyeksportowana pozycja początkowa (oczekiwane pięć kolumn day,code,name,shares,cost).",
        "OverwriteAllowedHint": "Ten plik ma daty, więc jest rejestrem transakcji: może zastąpić całe archiwum.",
        "OverwriteBlockedHint": "Tylko rejestr z datami może nadpisać; zlecenia dnia są dopisywane.",
    },
    "pt-BR": {
        "LedgerBaselineImport.Content": "Importar posição inicial",
        "LedgerBaselineImported": "Posição inicial carregada: {0}, {1} posições",
        "LedgerBaselineImportRejected": "Este arquivo tem linhas ilegíveis: {0}. Nada foi importado.",
        "LedgerBaselineImportMixedDays": "Este arquivo indica mais de um dia — uma posição inicial é de um dia. Nada foi importado.",
        "LedgerBaselineImportShape": "Esta não é uma posição inicial exportada (esperadas as cinco colunas day,code,name,shares,cost).",
        "OverwriteAllowedHint": "Este arquivo traz datas, é um registro de operações: pode substituir o arquivo inteiro.",
        "OverwriteBlockedHint": "Só um registro com datas pode sobrescrever; as ordens do dia são acrescentadas.",
    },
    "ru": {
        "LedgerBaselineImport.Content": "Импортировать начальную позицию",
        "LedgerBaselineImported": "Начальная позиция загружена: {0}, позиций: {1}",
        "LedgerBaselineImportRejected": "В файле есть нечитаемые строки: {0}. Ничего не импортировано.",
        "LedgerBaselineImportMixedDays": "В файле больше одной даты — начальная позиция относится к одному дню. Ничего не импортировано.",
        "LedgerBaselineImportShape": "Это не экспортированная начальная позиция (нужны пять столбцов day,code,name,shares,cost).",
        "OverwriteAllowedHint": "В файле есть даты, это архив сделок: он может заменить архив целиком.",
        "OverwriteBlockedHint": "Заменить архив может только архив с датами; заявки дня добавляются.",
    },
    "tr": {
        "LedgerBaselineImport.Content": "Başlangıç pozisyonunu içe aktar",
        "LedgerBaselineImported": "Başlangıç pozisyonu yüklendi: {0}, {1} pozisyon",
        "LedgerBaselineImportRejected": "Bu dosyada okunamayan satırlar var: {0}. Hiçbir şey aktarılmadı.",
        "LedgerBaselineImportMixedDays": "Bu dosya birden fazla gün içeriyor — başlangıç pozisyonu tek günlüktür. Hiçbir şey aktarılmadı.",
        "LedgerBaselineImportShape": "Bu, dışa aktarılmış bir başlangıç pozisyonu değil (day,code,name,shares,cost beş sütun gerekir).",
        "OverwriteAllowedHint": "Bu dosyada tarihler var, yani işlem kaydı: arşivi tümüyle değiştirebilir.",
        "OverwriteBlockedHint": "Yalnızca tarihli işlem kaydı üzerine yazabilir; günün emirleri eklenir.",
    },
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# `x:Uid` looks for `<uid>.Content`, so the button's key carries the suffix. A plain
# `LedgerBaselineImport` beside it would be both a resource and a scope — the resource index
# refuses that (PRI278) — so the unsuffixed spelling is dropped from any file still carrying it.
LEGACY = ("LedgerBaselineImport",)


def main():
    changed = 0

    for lang, table in [("zh-Hans", ZH), *T.items()]:
        resw = STRINGS / lang / "Resources.resw"

        if not resw.exists():
            print(f"{lang}: MISSING FILE")
            continue

        raw = resw.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")

        dropped = False

        for legacy in LEGACY:
            pattern = r'^  <data name="%s"><value>.*?</value></data>\n' % re.escape(legacy)

            if re.search(pattern, text, flags=re.M):
                text = re.sub(pattern, "", text, flags=re.M)
                dropped = True

        missing = {k: v for k, v in table.items() if f'name="{k}"' not in text}

        if not missing and not dropped:
            print(f"{lang}: already present")
            continue

        block = "".join(f'  <data name="{k}"><value>{esc(v)}</value></data>\n' for k, v in missing.items())

        trimmed = text.rstrip()
        assert trimmed.endswith("</root>"), lang
        text = trimmed[: -len("</root>")].rstrip("\n") + "\n" + block + "</root>\n"

        resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))
        changed += 1
        print(f"{lang}: added {len(missing)} keys")

    print(f"changed {changed} files")


if __name__ == "__main__":
    main()
