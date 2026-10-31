#!/usr/bin/env python3
"""Adds the two-press confirmation strings to all fourteen resource files.

The whole-record import cannot ask in a second dialog — WinUI allows one ContentDialog at a
time — so it asks with the same button, renamed, plus a line stating the trade. Two keys: the
button's second state and the sentence above it.

Idempotent: a file already carrying `TradeHistoryReplaceAsk` is left alone. resw keeps its
BOM and LF endings.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

ZH = {
    "TradeHistoryImportConfirm.Content": "确认替换：{0} 笔",
    "TradeHistoryReplaceAsk": "将用这 {0} 笔替换现有 {1} 笔——再点一次「确认替换」才会执行。",
}

T = {
    "en-US": {
        "TradeHistoryImportConfirm.Content": "Confirm: {0} fills",
        "TradeHistoryReplaceAsk": "{0} fills will replace the {1} filed — press again to go ahead.",
    },
    "zh-Hant": {
        "TradeHistoryImportConfirm.Content": "確認替換：{0} 筆",
        "TradeHistoryReplaceAsk": "將用這 {0} 筆替換現有 {1} 筆——再點一次「確認替換」才會執行。",
    },
    "cs": {
        "TradeHistoryImportConfirm.Content": "Potvrdit: {0} obchodů",
        "TradeHistoryReplaceAsk": "{0} obchodů nahradí {1} uložených — stiskněte ještě jednou.",
    },
    "de": {
        "TradeHistoryImportConfirm.Content": "Bestätigen: {0}",
        "TradeHistoryReplaceAsk": "{0} Ausführungen ersetzen die {1} abgelegten — noch einmal bestätigen.",
    },
    "es": {
        "TradeHistoryImportConfirm.Content": "Confirmar: {0}",
        "TradeHistoryReplaceAsk": "{0} operaciones reemplazarán las {1} archivadas; pulsa otra vez.",
    },
    "fr": {
        "TradeHistoryImportConfirm.Content": "Confirmer : {0}",
        "TradeHistoryReplaceAsk": "{0} opérations remplaceront les {1} archivées ; appuyez encore.",
    },
    "it": {
        "TradeHistoryImportConfirm.Content": "Conferma: {0}",
        "TradeHistoryReplaceAsk": "{0} operazioni sostituiranno le {1} archiviate; premi di nuovo.",
    },
    "ja": {
        "TradeHistoryImportConfirm.Content": "確認：{0} 件",
        "TradeHistoryReplaceAsk": "{0} 件で既存の {1} 件を置き換えます。もう一度押すと実行します。",
    },
    "ko": {
        "TradeHistoryImportConfirm.Content": "확인: {0}건",
        "TradeHistoryReplaceAsk": "{0}건이 기존 {1}건을 교체합니다. 한 번 더 누르면 실행됩니다.",
    },
    "pl": {
        "TradeHistoryImportConfirm.Content": "Potwierdź: {0}",
        "TradeHistoryReplaceAsk": "{0} transakcji zastąpi {1} zapisanych — naciśnij jeszcze raz.",
    },
    "pt-BR": {
        "TradeHistoryImportConfirm.Content": "Confirmar: {0}",
        "TradeHistoryReplaceAsk": "{0} operações substituirão as {1} arquivadas; pressione de novo.",
    },
    "ru": {
        "TradeHistoryImportConfirm.Content": "Подтвердить: {0}",
        "TradeHistoryReplaceAsk": "Сделок {0} заменят {1} сохранённых — нажмите ещё раз.",
    },
    "tr": {
        "TradeHistoryImportConfirm.Content": "Onayla: {0}",
        "TradeHistoryReplaceAsk": "{0} işlem, kayıtlı {1} işlemin yerini alacak — bir kez daha onaylayın.",
    },
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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

        missing = {k: v for k, v in table.items() if f'name="{k}"' not in text}

        if not missing:
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
