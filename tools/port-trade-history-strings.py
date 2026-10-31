#!/usr/bin/env python3
"""Adds the trade-history strings to all fourteen resource files.

The 导入成交记录 dialog grew a record of its own: what is filed, and the two gestures that move
the whole of it. Fourteen keys, in four groups:

  * the history block — title, the count-and-span line, and what an empty archive says;
  * its two buttons, and what each reports when it worked;
  * the two refusals a whole-record import can give (a file with no trades in it; a file whose
    rows carry no dates, which is a day's orders that walked into the wrong dialog);
  * the confirmation that names what will be lost, and the daily import's heading, plus the
    line that counts how many rows are already filed.

Idempotent: a file already carrying `TradeHistoryTitle` is left alone. resw keeps its BOM and
LF endings.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

ZH = {
    "TradeHistoryTitle.Text": "历史成交记录",
    "TradeHistorySummary": "共 {0} 笔 · {1} 至 {2}",
    "TradeHistoryEmpty": "还没有历史成交记录。",
    "TradeHistoryExport.Content": "全量导出",
    "TradeHistoryImport.Content": "全量导入（覆盖）",
    "TradeHistoryExported": "已导出 {0} 笔成交记录。",
    "TradeHistoryImported": "已全量导入：档案现有 {0} 笔（原有 {1} 笔被替换）。",
    "TradeHistoryImportShape": "这个文件里读不出成交记录——需要带 day 表头的导出文件。",
    "TradeHistoryImportUndated": "这个文件的行没有日期。全量导入要的是带日期的历史成交记录。",
    "TradeHistoryReplaceTitle": "替换全部历史成交记录？",
    "TradeHistoryReplaceBody": "将写入 {0} 笔；现有 {1} 笔会被清空，且无法找回。",
    "TradeHistoryReplaceDo": "替换",
    "PortfolioImportDaily.Text": "每日成交导入",
    "TradeImportDuplicates": "其中 {0} 笔已在档案里，导入时会跳过。",
}

T = {
    "en-US": {
        "TradeHistoryTitle.Text": "Filed trades",
        "TradeHistorySummary": "{0} fills · {1} to {2}",
        "TradeHistoryEmpty": "Nothing has been filed yet.",
        "TradeHistoryExport.Content": "Export all",
        "TradeHistoryImport.Content": "Import all (replaces)",
        "TradeHistoryExported": "Exported {0} fills.",
        "TradeHistoryImported": "Imported: {0} fills filed ({1} replaced).",
        "TradeHistoryImportShape": "No trades could be read from this file — it wants the export that starts with a `day` header.",
        "TradeHistoryImportUndated": "The rows in this file carry no dates. A whole-record import wants a dated record of trades.",
        "TradeHistoryReplaceTitle": "Replace every filed trade?",
        "TradeHistoryReplaceBody": "{0} fills will be written; the {1} already filed will be cleared and cannot be recovered.",
        "TradeHistoryReplaceDo": "Replace",
        "PortfolioImportDaily.Text": "A day's fills",
        "TradeImportDuplicates": "{0} of them are already filed and will be skipped.",
    },
    "zh-Hant": {
        "TradeHistoryTitle.Text": "歷史成交記錄",
        "TradeHistorySummary": "共 {0} 筆 · {1} 至 {2}",
        "TradeHistoryEmpty": "還沒有歷史成交記錄。",
        "TradeHistoryExport.Content": "全量匯出",
        "TradeHistoryImport.Content": "全量匯入（覆蓋）",
        "TradeHistoryExported": "已匯出 {0} 筆成交記錄。",
        "TradeHistoryImported": "已全量匯入：檔案現有 {0} 筆（原有 {1} 筆被替換）。",
        "TradeHistoryImportShape": "這個檔案裡讀不出成交記錄——需要帶 day 表頭的匯出檔案。",
        "TradeHistoryImportUndated": "這個檔案的行沒有日期。全量匯入要的是帶日期的歷史成交記錄。",
        "TradeHistoryReplaceTitle": "替換全部歷史成交記錄？",
        "TradeHistoryReplaceBody": "將寫入 {0} 筆；現有 {1} 筆會被清空，且無法找回。",
        "TradeHistoryReplaceDo": "替換",
        "PortfolioImportDaily.Text": "每日成交匯入",
        "TradeImportDuplicates": "其中 {0} 筆已在檔案裡，匯入時會跳過。",
    },
    "cs": {
        "TradeHistoryTitle.Text": "Uložené obchody",
        "TradeHistorySummary": "{0} obchodů · {1} až {2}",
        "TradeHistoryEmpty": "Zatím není nic uloženo.",
        "TradeHistoryExport.Content": "Exportovat vše",
        "TradeHistoryImport.Content": "Importovat vše (přepíše)",
        "TradeHistoryExported": "Exportováno {0} obchodů.",
        "TradeHistoryImported": "Importováno: {0} obchodů v archivu ({1} nahrazeno).",
        "TradeHistoryImportShape": "Z tohoto souboru nelze načíst obchody — je třeba export začínající hlavičkou `day`.",
        "TradeHistoryImportUndated": "Řádky v tomto souboru nemají data. Import celého archivu potřebuje obchody s daty.",
        "TradeHistoryReplaceTitle": "Nahradit všechny uložené obchody?",
        "TradeHistoryReplaceBody": "Bude zapsáno {0} obchodů; {1} stávajících bude smazáno a nelze je obnovit.",
        "TradeHistoryReplaceDo": "Nahradit",
        "PortfolioImportDaily.Text": "Denní obchody",
        "TradeImportDuplicates": "{0} z nich je již uloženo a budou přeskočeny.",
    },
    "de": {
        "TradeHistoryTitle.Text": "Abgelegte Geschäfte",
        "TradeHistorySummary": "{0} Ausführungen · {1} bis {2}",
        "TradeHistoryEmpty": "Es ist noch nichts abgelegt.",
        "TradeHistoryExport.Content": "Alles exportieren",
        "TradeHistoryImport.Content": "Alles importieren (ersetzt)",
        "TradeHistoryExported": "{0} Ausführungen exportiert.",
        "TradeHistoryImported": "Importiert: {0} Ausführungen abgelegt ({1} ersetzt).",
        "TradeHistoryImportShape": "Aus dieser Datei lassen sich keine Geschäfte lesen — erwartet wird der Export mit einer `day`-Kopfzeile.",
        "TradeHistoryImportUndated": "Die Zeilen dieser Datei tragen keine Daten. Ein Vollimport braucht ein datiertes Geschäftsarchiv.",
        "TradeHistoryReplaceTitle": "Alle abgelegten Geschäfte ersetzen?",
        "TradeHistoryReplaceBody": "{0} Ausführungen werden geschrieben; die {1} vorhandenen werden gelöscht und lassen sich nicht wiederherstellen.",
        "TradeHistoryReplaceDo": "Ersetzen",
        "PortfolioImportDaily.Text": "Tagesausführungen",
        "TradeImportDuplicates": "{0} davon sind bereits abgelegt und werden übersprungen.",
    },
    "es": {
        "TradeHistoryTitle.Text": "Operaciones archivadas",
        "TradeHistorySummary": "{0} operaciones · {1} a {2}",
        "TradeHistoryEmpty": "Todavía no hay nada archivado.",
        "TradeHistoryExport.Content": "Exportar todo",
        "TradeHistoryImport.Content": "Importar todo (reemplaza)",
        "TradeHistoryExported": "Se exportaron {0} operaciones.",
        "TradeHistoryImported": "Importado: {0} operaciones archivadas ({1} reemplazadas).",
        "TradeHistoryImportShape": "No se pueden leer operaciones de este archivo: hace falta la exportación que empieza con la cabecera `day`.",
        "TradeHistoryImportUndated": "Las filas de este archivo no llevan fecha. Una importación completa necesita un registro con fechas.",
        "TradeHistoryReplaceTitle": "¿Reemplazar todas las operaciones archivadas?",
        "TradeHistoryReplaceBody": "Se escribirán {0} operaciones; las {1} actuales se borrarán y no se pueden recuperar.",
        "TradeHistoryReplaceDo": "Reemplazar",
        "PortfolioImportDaily.Text": "Operaciones del día",
        "TradeImportDuplicates": "{0} de ellas ya están archivadas y se omitirán.",
    },
    "fr": {
        "TradeHistoryTitle.Text": "Opérations archivées",
        "TradeHistorySummary": "{0} opérations · du {1} au {2}",
        "TradeHistoryEmpty": "Rien n'est encore archivé.",
        "TradeHistoryExport.Content": "Tout exporter",
        "TradeHistoryImport.Content": "Tout importer (remplace)",
        "TradeHistoryExported": "{0} opérations exportées.",
        "TradeHistoryImported": "Importé : {0} opérations archivées ({1} remplacées).",
        "TradeHistoryImportShape": "Aucune opération lisible dans ce fichier — il faut l'export qui commence par l'en-tête `day`.",
        "TradeHistoryImportUndated": "Les lignes de ce fichier ne portent pas de date. Un import complet exige un registre daté.",
        "TradeHistoryReplaceTitle": "Remplacer toutes les opérations archivées ?",
        "TradeHistoryReplaceBody": "{0} opérations seront écrites ; les {1} actuelles seront effacées et ne pourront pas être récupérées.",
        "TradeHistoryReplaceDo": "Remplacer",
        "PortfolioImportDaily.Text": "Opérations du jour",
        "TradeImportDuplicates": "{0} d'entre elles sont déjà archivées et seront ignorées.",
    },
    "it": {
        "TradeHistoryTitle.Text": "Operazioni archiviate",
        "TradeHistorySummary": "{0} operazioni · dal {1} al {2}",
        "TradeHistoryEmpty": "Non c'è ancora nulla in archivio.",
        "TradeHistoryExport.Content": "Esporta tutto",
        "TradeHistoryImport.Content": "Importa tutto (sostituisce)",
        "TradeHistoryExported": "Esportate {0} operazioni.",
        "TradeHistoryImported": "Importato: {0} operazioni in archivio ({1} sostituite).",
        "TradeHistoryImportShape": "Da questo file non si leggono operazioni — serve l'esportazione che inizia con l'intestazione `day`.",
        "TradeHistoryImportUndated": "Le righe di questo file non hanno date. Un import completo richiede un registro datato.",
        "TradeHistoryReplaceTitle": "Sostituire tutte le operazioni archiviate?",
        "TradeHistoryReplaceBody": "Verranno scritte {0} operazioni; le {1} attuali saranno cancellate e non recuperabili.",
        "TradeHistoryReplaceDo": "Sostituisci",
        "PortfolioImportDaily.Text": "Operazioni del giorno",
        "TradeImportDuplicates": "{0} sono già in archivio e verranno saltate.",
    },
    "ja": {
        "TradeHistoryTitle.Text": "保存済みの約定",
        "TradeHistorySummary": "全 {0} 件 · {1} 〜 {2}",
        "TradeHistoryEmpty": "まだ保存された約定はありません。",
        "TradeHistoryExport.Content": "すべて書き出す",
        "TradeHistoryImport.Content": "すべて読み込む（置き換え）",
        "TradeHistoryExported": "{0} 件の約定を書き出しました。",
        "TradeHistoryImported": "読み込みました：{0} 件を保存（{1} 件を置き換え）。",
        "TradeHistoryImportShape": "このファイルから約定を読み取れません。`day` 見出しで始まる書き出しファイルが必要です。",
        "TradeHistoryImportUndated": "このファイルの行に日付がありません。全件読み込みには日付入りの約定記録が必要です。",
        "TradeHistoryReplaceTitle": "保存済みの約定をすべて置き換えますか？",
        "TradeHistoryReplaceBody": "{0} 件を書き込みます。現在の {1} 件は消去され、元に戻せません。",
        "TradeHistoryReplaceDo": "置き換え",
        "PortfolioImportDaily.Text": "当日の約定",
        "TradeImportDuplicates": "うち {0} 件は保存済みのため読み飛ばします。",
    },
    "ko": {
        "TradeHistoryTitle.Text": "저장된 거래",
        "TradeHistorySummary": "총 {0}건 · {1} ~ {2}",
        "TradeHistoryEmpty": "아직 저장된 거래가 없습니다.",
        "TradeHistoryExport.Content": "전체 내보내기",
        "TradeHistoryImport.Content": "전체 가져오기(덮어쓰기)",
        "TradeHistoryExported": "거래 {0}건을 내보냈습니다.",
        "TradeHistoryImported": "가져왔습니다: {0}건 저장(기존 {1}건 교체).",
        "TradeHistoryImportShape": "이 파일에서 거래를 읽을 수 없습니다. `day` 머리글로 시작하는 내보내기 파일이 필요합니다.",
        "TradeHistoryImportUndated": "이 파일의 행에 날짜가 없습니다. 전체 가져오기에는 날짜가 있는 거래 기록이 필요합니다.",
        "TradeHistoryReplaceTitle": "저장된 거래를 모두 교체할까요?",
        "TradeHistoryReplaceBody": "{0}건을 기록합니다. 기존 {1}건은 지워지며 되돌릴 수 없습니다.",
        "TradeHistoryReplaceDo": "교체",
        "PortfolioImportDaily.Text": "당일 거래",
        "TradeImportDuplicates": "그중 {0}건은 이미 저장되어 건너뜁니다.",
    },
    "pl": {
        "TradeHistoryTitle.Text": "Zapisane transakcje",
        "TradeHistorySummary": "{0} transakcji · {1} – {2}",
        "TradeHistoryEmpty": "Nic jeszcze nie zapisano.",
        "TradeHistoryExport.Content": "Eksportuj wszystko",
        "TradeHistoryImport.Content": "Importuj wszystko (zastąpi)",
        "TradeHistoryExported": "Wyeksportowano {0} transakcji.",
        "TradeHistoryImported": "Zaimportowano: {0} transakcji ({1} zastąpiono).",
        "TradeHistoryImportShape": "Z tego pliku nie da się odczytać transakcji — potrzebny jest eksport zaczynający się nagłówkiem `day`.",
        "TradeHistoryImportUndated": "Wiersze w tym pliku nie mają dat. Pełny import wymaga rejestru z datami.",
        "TradeHistoryReplaceTitle": "Zastąpić wszystkie zapisane transakcje?",
        "TradeHistoryReplaceBody": "Zapisanych zostanie {0} transakcji; obecne {1} zostaną usunięte i nie da się ich odzyskać.",
        "TradeHistoryReplaceDo": "Zastąp",
        "PortfolioImportDaily.Text": "Transakcje dnia",
        "TradeImportDuplicates": "{0} z nich już jest zapisanych i zostaną pominięte.",
    },
    "pt-BR": {
        "TradeHistoryTitle.Text": "Operações arquivadas",
        "TradeHistorySummary": "{0} operações · {1} a {2}",
        "TradeHistoryEmpty": "Nada foi arquivado ainda.",
        "TradeHistoryExport.Content": "Exportar tudo",
        "TradeHistoryImport.Content": "Importar tudo (substitui)",
        "TradeHistoryExported": "{0} operações exportadas.",
        "TradeHistoryImported": "Importado: {0} operações arquivadas ({1} substituídas).",
        "TradeHistoryImportShape": "Não é possível ler operações deste arquivo — é preciso a exportação que começa com o cabeçalho `day`.",
        "TradeHistoryImportUndated": "As linhas deste arquivo não têm datas. Uma importação completa exige um registro datado.",
        "TradeHistoryReplaceTitle": "Substituir todas as operações arquivadas?",
        "TradeHistoryReplaceBody": "{0} operações serão gravadas; as {1} atuais serão apagadas e não poderão ser recuperadas.",
        "TradeHistoryReplaceDo": "Substituir",
        "PortfolioImportDaily.Text": "Operações do dia",
        "TradeImportDuplicates": "{0} delas já estão arquivadas e serão ignoradas.",
    },
    "ru": {
        "TradeHistoryTitle.Text": "Сохранённые сделки",
        "TradeHistorySummary": "сделок: {0} · {1} — {2}",
        "TradeHistoryEmpty": "Пока ничего не сохранено.",
        "TradeHistoryExport.Content": "Выгрузить всё",
        "TradeHistoryImport.Content": "Загрузить всё (заменит)",
        "TradeHistoryExported": "Выгружено сделок: {0}.",
        "TradeHistoryImported": "Загружено: сделок {0} (заменено {1}).",
        "TradeHistoryImportShape": "Из этого файла нельзя прочитать сделки — нужен экспорт с заголовком `day`.",
        "TradeHistoryImportUndated": "В строках этого файла нет дат. Для полной загрузки нужен архив сделок с датами.",
        "TradeHistoryReplaceTitle": "Заменить все сохранённые сделки?",
        "TradeHistoryReplaceBody": "Будет записано сделок: {0}; текущие {1} будут удалены без возможности восстановления.",
        "TradeHistoryReplaceDo": "Заменить",
        "PortfolioImportDaily.Text": "Сделки за день",
        "TradeImportDuplicates": "{0} из них уже сохранены и будут пропущены.",
    },
    "tr": {
        "TradeHistoryTitle.Text": "Kayıtlı işlemler",
        "TradeHistorySummary": "{0} işlem · {1} – {2}",
        "TradeHistoryEmpty": "Henüz hiçbir şey kaydedilmedi.",
        "TradeHistoryExport.Content": "Tümünü dışa aktar",
        "TradeHistoryImport.Content": "Tümünü içe aktar (değiştirir)",
        "TradeHistoryExported": "{0} işlem dışa aktarıldı.",
        "TradeHistoryImported": "İçe aktarıldı: {0} işlem kayıtlı ({1} değiştirildi).",
        "TradeHistoryImportShape": "Bu dosyadan işlem okunamıyor — `day` başlığıyla başlayan dışa aktarım dosyası gerekiyor.",
        "TradeHistoryImportUndated": "Bu dosyadaki satırlarda tarih yok. Tam içe aktarma tarihli bir işlem kaydı ister.",
        "TradeHistoryReplaceTitle": "Kayıtlı tüm işlemler değiştirilsin mi?",
        "TradeHistoryReplaceBody": "{0} işlem yazılacak; mevcut {1} işlem silinecek ve geri alınamayacak.",
        "TradeHistoryReplaceDo": "Değiştir",
        "PortfolioImportDaily.Text": "Günün işlemleri",
        "TradeImportDuplicates": "Bunlardan {0} tanesi zaten kayıtlı ve atlanacak.",
    },
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# The unsuffixed spellings of the two headings, dropped from any file that picked them up:
# `x:Uid` never looks for them, and a name that is both a resource and a scope is refused by the
# resource index (PRI278).
LEGACY = ("TradeHistoryTitle", "PortfolioImportDaily")


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
