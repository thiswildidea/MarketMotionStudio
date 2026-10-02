# -*- coding: utf-8 -*-
"""把「极端交易日」那一章里「标的只有一个，是当前市场的宽基指数之一」改成「任意标的」。

页面加了搜索框之后那一句就是错的 —— 个股和 ETF 也能上这一页，下面的清单只是常用几个的
快捷方式。同一句话在 14 份帮助里各有一份，**改一处改全部 14 份**，顺序和位置都一样：
第 9 章（章节顺序 = 导航顺序），那一章里第 4 条 bullet（第 1 条是复权口径，第 2 条是按幅度
排序，第 3 条是只算已发生的日）。

用法：
    python tools/port-extremedays-any.py            # 只打印要换掉的那一行，不写
    python tools/port-extremedays-any.py --apply    # 真的写
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELP = os.path.join(ROOT, "src/MarketMotionStudio/Assets/Help")

CHAPTER = 8  # 0-based：第 9 章，极端交易日
BULLET = 3   # 0-based：那一章里第 4 条以 "- " 开头的行

NEW = {
    "en-US": """- **Any instrument the market quotes, not only the broad indices.** Type a code, a name or
  pinyin into the search box: a single stock and an exchange-traded fund belong on this board as
  much as an index does, and the list underneath is only a shortcut to the usual ones. Changing the
  market swaps that list and leaves behind an instrument from another market; choosing an instrument
  or a span only saves a preference — nothing is fetched until 取数 is pressed.""",
    "de": """- **Jedes Instrument, das der Markt notiert, nicht nur die breiten Indizes.** Code, Name oder
  Pinyin in das Suchfeld tippen: Eine einzelne Aktie und ein börsennotierter Fonds gehören auf
  dieses Tableau so sehr wie ein Index, und die Liste darunter ist nur ein Schnellweg zu den
  üblichen. Ein anderer Markt tauscht die Liste und lässt ein Instrument von einem anderen Markt
  zurück; ein anderes Instrument oder ein anderer Zeitraum speichert nur eine Einstellung — geholt
  wird erst mit 取数.""",
    "es": """- **Cualquier instrumento que cotice en el mercado, no solo los índices amplios.** Escriba un
  código, un nombre o pinyin en el buscador: una acción concreta y un fondo cotizado pertenecen a
  este tablero tanto como un índice, y la lista de abajo es solo un atajo a los habituales. Cambiar
  de mercado sustituye esa lista y deja atrás un instrumento de otro mercado; elegir instrumento o
  periodo solo guarda una preferencia — nada se descarga hasta pulsar 取数.""",
    "fr": """- **N'importe quel instrument coté sur le marché, pas seulement les grands indices.** Tapez un
  code, un nom ou du pinyin dans la recherche : une action particulière et un fonds coté ont autant
  leur place ici qu'un indice, et la liste en dessous n'est qu'un raccourci vers les habituels.
  Changer de marché remplace cette liste et abandonne un instrument d'un autre marché ; choisir un
  instrument ou une période n'enregistre qu'une préférence — rien n'est chargé avant 取数.""",
    "it": """- **Qualsiasi strumento quotato dal mercato, non solo gli indici ampi.** Scrivete un codice, un
  nome o il pinyin nella casella di ricerca: un'azione singola e un fondo quotato stanno su questa
  tavola quanto un indice, e l'elenco sotto è solo una scorciatoia ai soliti. Cambiare mercato
  sostituisce quell'elenco e lascia indietro uno strumento di un altro mercato; scegliere strumento
  o intervallo salva solo una preferenza — nulla viene scaricato finché non si preme 取数.""",
    "pl": """- **Dowolny instrument notowany na tym rynku, nie tylko szerokie indeksy.** Wpisz kod, nazwę lub
  pinyin w polu wyszukiwania: pojedyncza akcja i fundusz notowany na giełdzie pasują tu tak samo jak
  indeks, a lista poniżej to tylko skrót do najczęstszych. Zmiana rynku podmienia tę listę i porzuca
  instrument z innego rynku; wybór instrumentu lub zakresu zapisuje tylko preferencję — nic nie jest
  pobierane, dopóki nie naciśniesz 取数.""",
    "pt-BR": """- **Qualquer instrumento que o mercado cote, não apenas os índices amplos.** Digite um código, um
  nome ou pinyin na busca: uma ação individual e um fundo negociado em bolsa cabem neste quadro
  tanto quanto um índice, e a lista abaixo é só um atalho para os de sempre. Mudar o mercado troca
  essa lista e deixa para trás um instrumento de outro mercado; escolher instrumento ou intervalo só
  salva uma preferência — nada é buscado até 取数 ser pressionado.""",
    "cs": """- **Jakýkoli nástroj, který trh kotuje, nejen široké indexy.** Napište kód, název nebo pinyin do
  vyhledávání: jedna akcie a burzovně obchodovaný fond patří na tuto tabuli stejně jako index,
  a seznam pod ním je jen zkratka k obvyklým. Změna trhu tento seznam vymění a ponechá stranou
  nástroj z jiného trhu; volba nástroje nebo rozsahu uloží jen předvolbu — nic se nestahuje, dokud
  nestisknete 取数.""",
    "tr": """- **Piyasanın kotasyon verdiği her enstrüman, sadece geniş endeksler değil.** Arama kutusuna bir
  kod, bir ad veya pinyin yazın: tek bir hisse ve borsada işlem gören bir fon bu tabloya bir endeks
  kadar uyar, alttaki liste ise yalnızca alışılmış olanlara bir kısayoldur. Piyasa değiştirmek
  listeyi değiştirir ve başka bir piyasanın enstrümanını geride bırakır; enstrüman veya aralık
  seçmek yalnızca bir tercih kaydeder — 取数'e basılana kadar hiçbir şey çekilmez.""",
    "ru": """- **Любой инструмент, который котирует рынок, а не только широкие индексы.** Введите код,
  название или пинъинь в поле поиска: отдельная акция и биржевой фонд уместны здесь не меньше, чем
  индекс, а список ниже — лишь быстрый путь к привычным. Смена рынка меняет этот список и оставляет
  в стороне инструмент с другого рынка; выбор инструмента или интервала сохраняет только настройку —
  ничего не загружается, пока не нажата 取数.""",
    "ja": """- **その市場が値付けする銘柄なら何でも、広範な指数だけではありません。** 検索欄にコード・名前・
  拼音を入力してください。個別株や上場投信も、指数と同じくこのボードに乗ります。下の一覧はよく
  使うものへの近道にすぎません。市場を変えると一覧が入れ替わり、別の市場の銘柄は持ち越されません。
  銘柄や期間を選ぶのは設定の保存だけで、取数 を押すまで何も取得しません。""",
    "ko": """- **넓은 지수만이 아니라 그 시장이 호가하는 어떤 종목이라도.** 검색 상자에 코드·이름·병음을
  입력하세요. 개별 종목과 상장지수펀드는 지수만큼이나 이 보드에 어울리고, 아래 목록은 자주 쓰는
  것들로 가는 지름길일 뿐입니다. 시장을 바꾸면 그 목록이 바뀌고 다른 시장의 종목은 넘어오지
  않습니다. 종목이나 구간을 고르는 것은 선호를 저장할 뿐이며, 取数 를 누르기 전에는 아무것도
  가져오지 않습니다.""",
    "zh-Hans": """- **任何当前市场能报出价的标的都行，不只是宽基指数。** 在搜索框里输代码、名字或拼音——一只个股、
  一只 ETF 和指数一样适合这一页，下面那份清单只是常用几个的快捷方式。换市场会换掉这份清单，别的
  市场的代码不带过来；换标的或换区间都只存偏好，按「取数」才真的去取。""",
    "zh-Hant": """- **任何目前市場報得出價格的標的都行，不只是寬基指數。** 在搜尋框裡輸入代碼、名稱或拼音——
  一檔個股、一檔 ETF 和指數一樣適合這一頁，下面那份清單只是常用幾個的捷徑。換市場會換掉這份清單，
  別的市場的代碼不會帶過來；換標的或換區間都只存偏好，按「取數」才真的去取。""",
}


def main():
    apply = "--apply" in sys.argv

    for tag, new in NEW.items():
        path = os.path.join(HELP, f"help-{tag}.md")

        raw = open(path, "rb").read()
        text = raw.decode("utf-8-sig").lstrip("\ufeff")
        lines = text.replace("\r\n", "\n").split("\n")

        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(heads) <= CHAPTER:
            print(f"!! {tag}: 章节不够（{len(heads)}）")
            continue

        start = heads[CHAPTER]
        end = heads[CHAPTER + 1] if len(heads) > CHAPTER + 1 else len(lines)

        bullets = [i for i in range(start, end) if lines[i].startswith("- ")]

        if len(bullets) <= BULLET:
            print(f"!! {tag}: bullet 不够（{len(bullets)}）")
            continue

        at = bullets[BULLET]
        stop = bullets[BULLET + 1] if len(bullets) > BULLET + 1 else end

        while stop > at and lines[stop - 1].strip() == "":
            stop -= 1

        old = "\n".join(lines[at:stop])

        if not apply:
            print(f"--- {tag} · 第 {CHAPTER + 1} 章第 {BULLET + 1} 条 ---")
            print(old)
            print()
            continue

        lines[at:stop] = new.split("\n")

        out = "\n".join(lines)

        if not out.endswith("\n"):
            out += "\n"

        # 保 BOM：源文件有，写回去也得有。
        with io.open(path, "wb") as handle:
            handle.write(b"\xef\xbb\xbf" + out.encode("utf-8"))

        print(f"{tag}: 已替换（{len(old)} → {len(new)} 字符）")


if __name__ == "__main__":
    main()
