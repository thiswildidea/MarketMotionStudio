#!/usr/bin/env python3
"""Rewrites `IndexRaceMethodNote.Text` in all fourteen resource files.

That string is the one sentence on the index race page that says how the numbers were made, and it
still read "monthly bars, unadjusted" — the rule the board dropped when it took a reader's own
list. Thirteenth page moved from `RawBarsAsync` to `TotalReturnBarsAsync`; the help chapters were
rewritten at the time and the resource string was not, so the page was telling readers the opposite
of what the code does, in fourteen languages, and every verification script was green because a
script asserts the call and not the sentence under it.

What replaces it has to say three things, not one:
  - adjusted now;
  - an index is unaffected, so every number already published on the board is unchanged — which is
    the reader's real question, and why this is not a correction of any figure;
  - a stock is not unaffected, so an index row is a price return and a stock row a total return.

Idempotent: a file already carrying the new sentence is left alone. BOM and LF are preserved.
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

NEW = {
    "en-US": (
        "Monthly bars, adjusted. The source ignores the adjustment for an index, so every number "
        "already published on this board is unchanged — but a stock is another matter: a dividend "
        "is a cliff and a split is a halving, and neither is anything a holder lost. So an index "
        "row is a price return and a stock row a total return. Coverage differs: the S&amp;P "
        "reaches back to 1950, the Dow to 2009 and the Hang Seng Tech index to 2020. This board is "
        "not governed by the market setting: it reads three markets at once."
    ),
    "de": (
        "Monatskerzen, bereinigt. Die Quelle ignoriert die Bereinigung bei einem Index, also bleibt "
        "jede auf diesem Board veröffentlichte Zahl unverändert — eine Aktie ist jedoch etwas "
        "anderes: Eine Dividende ist ein Abgrund und ein Split eine Halbierung, und beides hat ein "
        "Halter nie verloren. Daher ist eine Index-Zeile eine Kursrendite und eine Aktien-Zeile "
        "eine Gesamtrendite. Die Reichweite unterscheidet sich: Der S&amp;P reicht zurück bis 1950, "
        "der Dow bis 2009 und der Hang-Seng-Tech-Index bis 2020. Dieses Board unterliegt nicht der "
        "Markt-Einstellung: Es liest drei Märkte zugleich."
    ),
    "es": (
        "Velas mensuales, ajustadas. La fuente ignora el ajuste en un índice, así que todas las "
        "cifras ya publicadas en este tablero siguen iguales — pero una acción es otra cosa: un "
        "dividendo es un acantilado y un split una división por la mitad, y ninguna de las dos es "
        "algo que un tenedor haya perdido. Por eso una fila de índice es una rentabilidad por "
        "precio y una fila de acción una rentabilidad total. La cobertura difiere: el S&amp;P llega "
        "hasta 1950, el Dow hasta 2009 y el Hang Seng Tech hasta 2020. Este tablero no está "
        "gobernado por el ajuste de mercado: lee tres mercados a la vez."
    ),
    "fr": (
        "Bougies mensuelles, ajustées. La source ignore l'ajustement pour un indice : tous les "
        "chiffres déjà publiés sur ce tableau restent donc identiques — mais une action est une "
        "autre affaire : un dividende est une falaise et une division du nominal une chute de "
        "moitié, et le détenteur n'a perdu ni l'un ni l'autre. Une ligne d'indice est donc un "
        "rendement de prix et une ligne d'action un rendement total. La couverture diffère : le "
        "S&amp;P remonte à 1950, le Dow à 2009 et le Hang Seng Tech à 2020. Ce tableau n'est pas "
        "régi par le réglage de marché : il lit trois marchés à la fois."
    ),
    "it": (
        "Candele mensili, rettificate. La fonte ignora la rettifica per un indice, quindi ogni "
        "numero già pubblicato su questa tavola resta identico — ma un'azione è un'altra cosa: un "
        "dividendo è un dirupo e un frazionamento un dimezzamento, e nessuno dei due è qualcosa che "
        "un detentore abbia perso. Perciò una riga di indice è un rendimento di prezzo e una riga "
        "di azione un rendimento totale. La copertura differisce: l'S&amp;P arriva al 1950, il Dow "
        "al 2009 e l'Hang Seng Tech al 2020. Questa tavola non è governata dall'impostazione di "
        "mercato: legge tre mercati insieme."
    ),
    "pl": (
        "Świece miesięczne, skorygowane. Źródło ignoruje korektę dla indeksu, więc wszystkie już "
        "opublikowane na tej tablicy liczby pozostają bez zmian — ale akcja to inna sprawa: "
        "dywidenda to urwisko, a podział akcji to przepołowienie, i żadnej z tych rzeczy posiadacz "
        "nie stracił. Dlatego wiersz indeksu to zwrot cenowy, a wiersz akcji to zwrot całkowity. "
        "Zasięg danych różni się: S&amp;P sięga 1950, Dow 2009, a Hang Seng Tech 2020. Ta tablica "
        "nie podlega ustawieniu rynku: czyta trzy rynki naraz."
    ),
    "pt-BR": (
        "Velas mensais, ajustadas. A fonte ignora o ajuste para um índice, portanto todos os números "
        "já publicados neste quadro permanecem iguais — mas uma ação é outra coisa: um dividendo é "
        "um penhasco e um desdobramento uma divisão pela metade, e nenhum dos dois é algo que um "
        "detentor tenha perdido. Assim, uma linha de índice é um retorno de preço e uma linha de "
        "ação um retorno total. A cobertura difere: o S&amp;P chega a 1950, o Dow a 2009 e o Hang "
        "Seng Tech a 2020. Este quadro não é governado pela configuração de mercado: lê três "
        "mercados ao mesmo tempo."
    ),
    "cs": (
        "Měsíční svíčky, upravené. Zdroj u indexu úpravu ignoruje, takže všechna čísla už na této "
        "tabuli zveřejněná zůstávají stejná — ale akcie je jiná věc: dividenda je sráž a rozdělení "
        "akcie zpolovení, a ani jedno není něco, co by držitel ztratil. Řádek indexu je proto výnos "
        "z ceny a řádek akcie celkový výnos. Rozsah dat se liší: S&amp;P sahá do roku 1950, Dow do "
        "2009 a Hang Seng Tech do 2020. Tato tabule nepodléhá nastavení trhu: čte tři trhy zároveň."
    ),
    "tr": (
        "Aylık mumlar, düzeltilmiş. Kaynak bir endeks için düzeltmeyi yok sayar, bu yüzden bu "
        "tabloda yayınlanmış her sayı aynı kalır — ama bir hisse başka bir iştir: temettü bir "
        "uçurum, bölünme ise yarıya iniştir ve ikisi de bir yatırımcının kaybettiği bir şey "
        "değildir. Bu nedenle bir endeks satırı fiyat getirisi, bir hisse satırı toplam getiridir. "
        "Kapsam farklıdır: S&amp;P 1950'e, Dow 2009'a ve Hang Seng Tech 2020'ye kadar uzanır. Bu "
        "tablo piyasa ayarına tabi değildir: üç piyasayı aynı anda okur."
    ),
    "ru": (
        "Месячные бары, с корректировкой. Источник игнорирует корректировку для индекса, поэтому "
        "все уже опубликованные на этой доске числа остались прежними — но акция это другое дело: "
        "дивиденд это обрыв, а дробление это деление пополам, и ни то ни другое держатель не "
        "терял. Поэтому строка индекса это доходность по цене, а строка акции — полная доходность. "
        "Охват различается: S&amp;P уходит к 1950 году, Dow — к 2009, а Hang Seng Tech — к 2020. "
        "Эта доска не подчиняется настройке рынка: она читает три рынка сразу."
    ),
    "ja": (
        "月足、調整済み — ソースは指数に対して調整を無視するため、このボードで既に公開されている"
        "数字はすべて変わりません。しかし個別株は別の話です。配当は断崖、分割は半減であり、どちらも"
        "保有者が失ったものではありません。したがって指数の行は価格リターン、個別株の行は"
        "トータルリターンです。データの範囲は異なります。S&amp;Pは1950年、ダウは2009年、"
        "ハンセンテック指数は2020年まで遡れます。このボードは市場設定に支配されません。三つの市場を"
        "同時に読みます。"
    ),
    "ko": (
        "월별 봉, 조정 적용 — 출처는 지수에 대해 조정을 무시하므로 이 보드에 이미 게시된 모든 숫자는 "
        "그대로입니다. 그러나 개별 종목은 다른 이야기입니다. 배당은 절벽이고 분할은 반토막이며, 둘 다 "
        "보유자가 잃은 것이 아닙니다. 따라서 지수 행은 가격 수익률이고 종목 행은 총수익률입니다. "
        "데이터 범위는 서로 다릅니다. S&amp;P는 1950년, 다우는 2009년, 항셍테크 지수는 2020년까지 "
        "거슬러 올라갑니다. 이 보드는 시장 설정의 적용을 받지 않습니다. 세 시장을 동시에 읽습니다."
    ),
    "zh-Hans": (
        "月线，复权——源端对指数忽略复权参数，所以这一页已发布的数字一个都没变；但个股是另一回事："
        "分红是一道断崖、拆股是一次腰斩，持有人谁也没亏这笔钱。因此指数行是价格回报，个股行是"
        "总回报。数据起点各不相同：标普 500 可回溯到 1950 年，道琼斯到 2009 年，恒生科技指数到 "
        "2020 年。这一页不受市场设置管辖：它同时读三个市场。"
    ),
    "zh-Hant": (
        "月線，復權——源頭對指數忽略復權參數，所以這一頁已發佈的數字一個都沒變；但個股是另一回事："
        "分紅是一道斷崖、拆股是一次腰斬，持有人誰也沒虧這筆錢。因此指數列是價格回報，個股列是"
        "總回報。資料起點各不相同：標普 500 可回溯到 1950 年，道瓊斯到 2009 年，恒生科技指數到 "
        "2020 年。這一頁不受市場設定管轄：它同時讀三個市場。"
    ),
}

# An old sentence is recognised by what it claimed, in the language it was written in. Checked so
# a second run does nothing, and so a file whose sentence has already been rewritten by hand is
# not matched again.
OLD_MARKERS = [
    "unadjusted", "nicht bereinigt", "sin ajustar", "non ajustées", "non rettificate",
    "bez korekty", "sem ajuste", "bez úprav", "düzeltilmemiş", "без корректировки",
    "調整なし", "조정 없음", "不调整", "不調整",
]

PATTERN = re.compile(
    r'(<data name="IndexRaceMethodNote\.Text"[^>]*>)\s*<value>.*?</value>(\s*</data>)',
    re.S,
)


def main():
    changed = []
    skipped = []
    missing = []

    for folder in sorted(NEW):
        path = STRINGS / folder / "Resources.resw"

        if not path.exists():
            missing.append(folder)
            continue

        text = path.read_text(encoding="utf-8-sig")
        after = text.lstrip("\ufeff")

        if NEW[folder] in after:
            skipped.append(folder)
            continue

        match = PATTERN.search(after)

        if match is None:
            missing.append(folder)
            continue

        # A sentence we do not recognise is left alone rather than overwritten: rewriting
        # fourteen languages is only safe when each one is the sentence this script thinks it is.
        old = match.group(0)

        if not any(marker in old for marker in OLD_MARKERS):
            missing.append(folder + " (unrecognised)")
            continue

        after = after[:match.start()] + match.group(1) + "<value>" + NEW[folder] + "</value>" \
            + match.group(2) + after[match.end():]

        # The byte-order mark goes back on the way out. These files arrive with one and a resource
        # file without it is a file the build reads differently; `utf-8-sig` takes it off on the
        # way in and nothing puts it back by itself.
        path.write_bytes(b"\xef\xbb\xbf" + after.encode("utf-8"))
        changed.append(folder)

    print(f"rewrote : {len(changed)}  {' '.join(changed)}")
    print(f"skipped : {len(skipped)}  {' '.join(skipped) or '-'}")
    print(f"problem : {len(missing)}  {' '.join(missing) or '-'}")

    keys = 0
    for folder in sorted(NEW):
        path = STRINGS / folder / "Resources.resw"
        if path.exists():
            keys = max(keys, len(re.findall(r'<data name="', path.read_text(encoding="utf-8-sig"))))

    print(f"key count: {keys}")


if __name__ == "__main__":
    main()
