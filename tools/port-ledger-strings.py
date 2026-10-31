#!/usr/bin/env python3
"""Adds the ledger's strings to all fourteen resource files.

The new archive and baseline controls (需求二：成交归档/覆盖导入/全量导出; 需求 3.1：初始
持仓快照) read ten keys. Every language below is a translation of the same Chinese rather
than a new text of its own, because a control that means one thing must say one thing.

Idempotent: a file already carrying `LedgerBaseline.Header` is left alone. resw keeps its
BOM and LF endings.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

ZH = {
    "TradeImportOverwrite.Content": "覆盖导入（清空已有历史成交）",
    "LedgerBaseline.Header": "初始持仓基准",
    "LedgerBaselineSet": "以当前列表设为初始持仓",
    "LedgerBaselineExport": "导出初始持仓",
    "LedgerBaselineDone": "已把 {0} 设为初始持仓基准，共 {1} 只",
    "LedgerBaselineNone": "还没有设定初始持仓基准。",
    "LedgerArchiveExport": "导出全部成交记录",
    "LedgerArchiveDone": "归档 {0} 笔 · 忽略重复 {1} 笔 · 档案共 {2} 笔",
    "LedgerArchiveReplaced": "已覆盖：档案为 {0} 笔（原有 {1} 笔被替换）",
    "LedgerArchiveEmpty": "档案里还没有成交记录。",
}

T = {
    "en-US": {
        "TradeImportOverwrite.Content": "Overwrite (clear the archived history)",
        "LedgerBaseline.Header": "Opening snapshot",
        "LedgerBaselineSet": "Set as the snapshot",
        "LedgerBaselineExport": "Export the snapshot",
        "LedgerBaselineDone": "{0} is now the snapshot, with {1} positions",
        "LedgerBaselineNone": "No opening snapshot has been set.",
        "LedgerArchiveExport": "Export every trade",
        "LedgerArchiveDone": "{0} filed · {1} duplicates ignored · {2} in the archive",
        "LedgerArchiveReplaced": "Replaced: the archive holds {0} trades (was {1})",
        "LedgerArchiveEmpty": "There is nothing in the archive yet.",
    },
    "zh-Hant": {
        "TradeImportOverwrite.Content": "覆蓋匯入（清空既有歷史成交）",
        "LedgerBaseline.Header": "初始持倉基準",
        "LedgerBaselineSet": "以目前清單設為初始持倉",
        "LedgerBaselineExport": "匯出初始持倉",
        "LedgerBaselineDone": "已把 {0} 設為初始持倉基準，共 {1} 檔",
        "LedgerBaselineNone": "還沒有設定初始持倉基準。",
        "LedgerArchiveExport": "匯出全部成交記錄",
        "LedgerArchiveDone": "歸檔 {0} 筆 · 忽略重複 {1} 筆 · 檔案共 {2} 筆",
        "LedgerArchiveReplaced": "已覆蓋：檔案為 {0} 筆（原有 {1} 筆被替換）",
        "LedgerArchiveEmpty": "檔案裡還沒有成交記錄。",
    },
    "cs": {
        "TradeImportOverwrite.Content": "Přepsat (vymazat archiv historie)",
        "LedgerBaseline.Header": "Počáteční pozice",
        "LedgerBaselineSet": "Nastavit jako počáteční pozici",
        "LedgerBaselineExport": "Exportovat počáteční pozici",
        "LedgerBaselineDone": "{0} je počáteční pozicí, celkem {1} pozic",
        "LedgerBaselineNone": "Počáteční pozice nebyla nastavena.",
        "LedgerArchiveExport": "Exportovat všechny obchody",
        "LedgerArchiveDone": "Uloženo {0} · duplicity ignorovány {1} · v archivu {2}",
        "LedgerArchiveReplaced": "Přepsáno: archiv má {0} obchodů (bylo {1})",
        "LedgerArchiveEmpty": "Archiv je zatím prázdný.",
    },
    "de": {
        "TradeImportOverwrite.Content": "Überschreiben (Archiv leeren)",
        "LedgerBaseline.Header": "Anfangsbestand",
        "LedgerBaselineSet": "Als Anfangsbestand setzen",
        "LedgerBaselineExport": "Anfangsbestand exportieren",
        "LedgerBaselineDone": "{0} ist der Anfangsbestand, mit {1} Positionen",
        "LedgerBaselineNone": "Es wurde kein Anfangsbestand gesetzt.",
        "LedgerArchiveExport": "Alle Umsätze exportieren",
        "LedgerArchiveDone": "{0} abgelegt · {1} Duplikate übersprungen · {2} im Archiv",
        "LedgerArchiveReplaced": "Ersetzt: das Archiv enthält {0} Umsätze (vorher {1})",
        "LedgerArchiveEmpty": "Das Archiv ist noch leer.",
    },
    "es": {
        "TradeImportOverwrite.Content": "Sobrescribir (vaciar el historial)",
        "LedgerBaseline.Header": "Posición inicial",
        "LedgerBaselineSet": "Fijar como posición inicial",
        "LedgerBaselineExport": "Exportar la posición inicial",
        "LedgerBaselineDone": "{0} es la posición inicial, con {1} posiciones",
        "LedgerBaselineNone": "Aún no se ha fijado una posición inicial.",
        "LedgerArchiveExport": "Exportar todas las operaciones",
        "LedgerArchiveDone": "{0} archivadas · {1} duplicadas omitidas · {2} en el archivo",
        "LedgerArchiveReplaced": "Sustituido: el archivo tiene {0} operaciones (antes {1})",
        "LedgerArchiveEmpty": "El archivo todavía está vacío.",
    },
    "fr": {
        "TradeImportOverwrite.Content": "Écraser (vider l'historique)",
        "LedgerBaseline.Header": "Position de départ",
        "LedgerBaselineSet": "Définir comme position de départ",
        "LedgerBaselineExport": "Exporter la position de départ",
        "LedgerBaselineDone": "{0} est la position de départ, avec {1} lignes",
        "LedgerBaselineNone": "Aucune position de départ n'a été définie.",
        "LedgerArchiveExport": "Exporter toutes les opérations",
        "LedgerArchiveDone": "{0} archivées · {1} doublons ignorés · {2} dans l'archive",
        "LedgerArchiveReplaced": "Remplacé : l'archive contient {0} opérations (au lieu de {1})",
        "LedgerArchiveEmpty": "L'archive est encore vide.",
    },
    "it": {
        "TradeImportOverwrite.Content": "Sovrascrivi (svuota lo storico)",
        "LedgerBaseline.Header": "Posizione iniziale",
        "LedgerBaselineSet": "Imposta come posizione iniziale",
        "LedgerBaselineExport": "Esporta la posizione iniziale",
        "LedgerBaselineDone": "{0} è la posizione iniziale, con {1} posizioni",
        "LedgerBaselineNone": "Nessuna posizione iniziale impostata.",
        "LedgerArchiveExport": "Esporta tutte le operazioni",
        "LedgerArchiveDone": "{0} archiviate · {1} duplicati ignorati · {2} nell'archivio",
        "LedgerArchiveReplaced": "Sostituito: l'archivio contiene {0} operazioni (prima {1})",
        "LedgerArchiveEmpty": "L'archivio è ancora vuoto.",
    },
    "ja": {
        "TradeImportOverwrite.Content": "上書き（保存済みの履歴を消す）",
        "LedgerBaseline.Header": "開始時点の保有",
        "LedgerBaselineSet": "現在の一覧を開始時点にする",
        "LedgerBaselineExport": "開始時点の保有を書き出す",
        "LedgerBaselineDone": "{0} を開始時点にしました（{1} 銘柄）",
        "LedgerBaselineNone": "開始時点の保有が未設定です。",
        "LedgerArchiveExport": "すべての約定を書き出す",
        "LedgerArchiveDone": "{0} 件を保存 · 重複 {1} 件を除外 · 計 {2} 件",
        "LedgerArchiveReplaced": "上書きしました：{0} 件（元は {1} 件）",
        "LedgerArchiveEmpty": "保存された約定はまだありません。",
    },
    "ko": {
        "TradeImportOverwrite.Content": "덮어쓰기(기존 기록 비우기)",
        "LedgerBaseline.Header": "기준 보유",
        "LedgerBaselineSet": "현재 목록을 기준으로 설정",
        "LedgerBaselineExport": "기준 보유 내보내기",
        "LedgerBaselineDone": "{0}을 기준으로 설정했습니다 · {1}개 종목",
        "LedgerBaselineNone": "기준 보유가 아직 설정되지 않았습니다.",
        "LedgerArchiveExport": "모든 거래 내보내기",
        "LedgerArchiveDone": "{0}건 보관 · 중복 {1}건 건너뜀 · 전체 {2}건",
        "LedgerArchiveReplaced": "덮어썼습니다: {0}건(기존 {1}건 교체)",
        "LedgerArchiveEmpty": "보관된 거래가 아직 없습니다.",
    },
    "pl": {
        "TradeImportOverwrite.Content": "Nadpisz (wyczyść historię)",
        "LedgerBaseline.Header": "Pozycja początkowa",
        "LedgerBaselineSet": "Ustaw jako pozycję początkową",
        "LedgerBaselineExport": "Eksportuj pozycję początkową",
        "LedgerBaselineDone": "{0} to pozycja początkowa, {1} pozycji",
        "LedgerBaselineNone": "Nie ustawiono pozycji początkowej.",
        "LedgerArchiveExport": "Eksportuj wszystkie transakcje",
        "LedgerArchiveDone": "Zapisano {0} · pominięto duplikaty {1} · w archiwum {2}",
        "LedgerArchiveReplaced": "Nadpisano: archiwum ma {0} transakcji (było {1})",
        "LedgerArchiveEmpty": "Archiwum jest jeszcze puste.",
    },
    "pt-BR": {
        "TradeImportOverwrite.Content": "Sobrescrever (limpar o histórico)",
        "LedgerBaseline.Header": "Posição inicial",
        "LedgerBaselineSet": "Definir como posição inicial",
        "LedgerBaselineExport": "Exportar a posição inicial",
        "LedgerBaselineDone": "{0} é a posição inicial, com {1} posições",
        "LedgerBaselineNone": "Nenhuma posição inicial foi definida.",
        "LedgerArchiveExport": "Exportar todas as operações",
        "LedgerArchiveDone": "{0} arquivadas · {1} duplicadas ignoradas · {2} no arquivo",
        "LedgerArchiveReplaced": "Substituído: o arquivo tem {0} operações (antes {1})",
        "LedgerArchiveEmpty": "O arquivo ainda está vazio.",
    },
    "ru": {
        "TradeImportOverwrite.Content": "Заменить (очистить историю)",
        "LedgerBaseline.Header": "Начальная позиция",
        "LedgerBaselineSet": "Задать как начальную позицию",
        "LedgerBaselineExport": "Экспортировать начальную позицию",
        "LedgerBaselineDone": "{0} — начальная позиция, позиций: {1}",
        "LedgerBaselineNone": "Начальная позиция ещё не задана.",
        "LedgerArchiveExport": "Экспортировать все сделки",
        "LedgerArchiveDone": "В архиве {0} · дубликатов пропущено {1} · всего {2}",
        "LedgerArchiveReplaced": "Заменено: в архиве {0} сделок (было {1})",
        "LedgerArchiveEmpty": "В архиве пока нет сделок.",
    },
    "tr": {
        "TradeImportOverwrite.Content": "Üstüne yaz (geçmişi temizle)",
        "LedgerBaseline.Header": "Başlangıç pozisyonu",
        "LedgerBaselineSet": "Başlangıç pozisyonu olarak ayarla",
        "LedgerBaselineExport": "Başlangıç pozisyonunu dışa aktar",
        "LedgerBaselineDone": "{0} başlangıç pozisyonu oldu · {1} pozisyon",
        "LedgerBaselineNone": "Henüz başlangıç pozisyonu ayarlanmadı.",
        "LedgerArchiveExport": "Tüm işlemleri dışa aktar",
        "LedgerArchiveDone": "{0} arşivlendi · {1} tekrar atlandı · toplam {2}",
        "LedgerArchiveReplaced": "Değiştirildi: arşivde {0} işlem var (önce {1})",
        "LedgerArchiveEmpty": "Arşivde henüz işlem yok.",
    },
}


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# **`x:Uid` reads `<uid>.Content`, not `<uid>`.** A button whose text is filed without the suffix
# draws as an empty frame — no error, no warning, just a blank rounded rectangle where two of them
# should say what they do (实测：初始持仓基准下的两个按钮，框在、字没有).
#
# The two spellings cannot both exist: a plain `LedgerBaselineSet` beside `LedgerBaselineSet.Content`
# makes the first a resource and a scope at once, which the resource index refuses with PRI278. The
# plain forms are renamed here and deleted from the files below; nothing reads them from code.
LEGACY = ("LedgerBaselineSet", "LedgerBaselineExport", "LedgerArchiveExport")

for _table in [ZH, *T.values()]:
    for _key in LEGACY:
        _table[f"{_key}.Content"] = _table.pop(_key)


changed = 0

if __name__ == "__main__":
    for path in sorted(STRINGS.iterdir()):
        lang = path.name

        table = T.get(lang) if lang != "zh-Hans" else ZH

        if table is None:
            print(f"{lang}: no translation, skipped")
            continue

        assert set(table) == set(ZH), lang

        resw = path / "Resources.resw"
        raw = resw.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")

        # Drop the pre-rename spellings, if this file still carries them. Whole lines, because
        # every key in these files is one line and a rewrite of the tree would lose the BOM, the
        # LF endings and the ordering that every other tool here depends on.
        dropped = False

        for legacy in LEGACY:
            pattern = r'^  <data name="%s"><value>.*?</value></data>\n' % re.escape(legacy)

            if re.search(pattern, text, flags=re.M):
                text = re.sub(pattern, "", text, flags=re.M)
                dropped = True

        # Only what is missing: later iterations add keys to the same table, and skipping the
        # whole file for one missing key would leave an older language without it. A file that
        # only needed the old spelling dropped is a change too — 「already present」must not
        # claim it.
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
