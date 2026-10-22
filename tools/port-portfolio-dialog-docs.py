# -*- coding: utf-8 -*-
r"""把 14 份手册的「实时持仓收益」一章补上 2026-10-22 的两条行为。

1. **管理持仓对话框显示收盘** —— 从前它只读账本（当天开盘），读者导入 800 股后打开
   对话框看到的还是 100 股，报「导入没生效」。现在弹出的每一行都是页面此刻的数，
   与列表一字不差；只看不改不动账本，真改了才写回（此后当天回放只画标记）。

2. **退出时滚动账本** —— 退出应用时把当天的最后持仓折进账本，第二天打开接着记。
   这条行为 10-22 落地，手册从未写过。

插在哪：本章最后一个粗体条（导入成交）之后，紧跟在「账本存在应用自己的目录里」
那条之前 —— 说的都是账本这件事。
幂等：新句子已经在文件里就跳过。文件编码照原样（帮助手册 LF 无 BOM）。

用法：<venv python> tools/port-portfolio-dialog-docs.py   （跑第二遍应当是 14 个 already there）
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP

CHAPTER = lt.chapter_of("NavPortfolioPnl")

DIALOG = {
    "zh-Hans": "- **「管理持仓」打开就是最新持仓。** 弹出的每一行都是页面此刻的数：当天买进的股数与摊出来的成本已经算进去，和列表一字不差。只看不改，账本一个字节都不动；真改了哪一行，写回的就是账本本身，当天的回放从此只画买卖点、不再重复数股数。退出应用时，当天的最后持仓折进账本，第二天打开接着记。",
    "zh-Hant": "- **「管理持倉」打開就是最新持倉。** 彈出的每一行都是畫面此刻的數：當天買進的股數與攤出來的成本已經算進去，和列表一字不差。只看不改，賬本一個位元組都不動；真改了哪一行，寫回的就是賬本本身，當天的回放從此只畫買賣點、不再重複數股數。退出應用時，當天的最後持倉摺進賬本，第二天打開接著記。",
    "en-US": "- **\"Holdings\" opens on the latest figures.** Every row in the dialog is what the page shows right now: today's fills are already in the shares and the diluted cost, the same numbers the list carries. Look without touching and the book does not move; change a row for real and it is the book itself you are writing — from then on the day's replay draws its markers without recounting the shares. On exit the day's final holdings fold into the book, ready to carry on the next morning.",
    "ja": "- **「保有銘柄」は最新の数で開く。** ダイアログの各行はページがいま示している数です。当日の約定はすでに株数と取得単価に反映され、一覧と一字違わず一致します。見るだけなら帳簿は一バイトも動かず、本当に直した行だけが帳簿そのものに書き戻されます。以後その日の再生は売買の印を描くだけで、株数を二重に数えません。アプリを終了すると、その日最後の保有が帳簿に折り込まれ、翌日そのまま続きを記せます。",
    "ko": "- **'보유 종목'은 최신 수치로 열린다.** 대화 상자의 각 행은 페이지가 지금 보여 주는 값이다. 오늘 체결이 이미 주식 수와 평균 단가에 반영되어 목록과 한 글자도 다르지 않다. 보기만 하면 장부는 한 글자도 움직이지 않고, 실제로 고친 행만 장부 자체에 쓰인다. 이후 그날의 재생은 매수·매도 표시만 그릴 뿐 주식 수를 다시 세지 않는다. 앱을 종료하면 그날 마지막 보유가 장부에 접혀 들어가고, 다음 날 이어서 기록한다.",
    "de": "- **„Bestand“ öffnet mit den neuesten Zahlen.** Jede Zeile im Dialog ist das, was die Seite gerade zeigt: Die Geschäfte des Tages stecken bereits in Stückzahl und verdünnten Kosten, dieselben Zahlen wie in der Liste. Nur ansehen und das Buch rückt kein Byte; eine Zeile wirklich ändern, und du schreibst das Buch selbst — die Wiedergabe des Tages zeichnet danach nur noch die Markierungen, ohne die Stückzahlen doppelt zu zählen. Beim Beenden falten sich die letzten Bestände des Tages ins Buch, und am nächsten Morgen geht es damit weiter.",
    "fr": "- **« Positions » s'ouvre sur les dernières valeurs.** Chaque ligne de la boîte est ce que la page montre à l'instant : les ordres du jour sont déjà dans les titres et le coût dilué, les mêmes chiffres que la liste. Regarder sans toucher ne déplace pas le registre d'un octet ; modifier vraiment une ligne, c'est le registre même qu'on écrit — la relecture du jour ne dessine ensuite que ses marques, sans recompter les titres. À la fermeture, les dernières positions du jour se plient dans le registre, prêt à continuer le lendemain matin.",
    "it": "- **«Posizioni» si apre sui valori più recenti.** Ogni riga della finestra è ciò che la pagina mostra in questo momento: le operazioni del giorno sono già nelle azioni e nel costo diluito, gli stessi numeri dell'elenco. Guardare senza toccare non muove il registro di un byte; modificare davvero una riga significa scrivere il registro stesso — da lì in poi la riproduzione del giorno disegna solo i segni, senza contare di nuovo le azioni. All'uscita le ultime posizioni del giorno si piegano nel registro, pronte a riprendere la mattina dopo.",
    "es": "- **«Posiciones» se abre con las cifras más recientes.** Cada fila del cuadro es lo que la página muestra en este momento: las operaciones del día ya están en las acciones y el coste diluido, las mismas cifras de la lista. Mirar sin tocar no mueve el libro un byte; cambiar de verdad una fila es escribir el libro mismo — desde entonces la reproducción del día solo dibuja sus marcas, sin contar de nuevo las acciones. Al salir, las últimas posiciones del día se pliegan en el libro, listas para continuar a la mañana siguiente.",
    "pt-BR": "- **\"Posições\" abre com os números mais recentes.** Cada linha da janela é o que a página mostra neste momento: as operações do dia já estão nas ações e no custo diluído, os mesmos números da lista. Olhar sem tocar não move o livro um byte; mudar de verdade uma linha é escrever o próprio livro — daí em diante a reprodução do dia desenha apenas as marcas, sem contar de novo as ações. Ao sair, as últimas posições do dia se dobram no livro, prontas para continuar na manhã seguinte.",
    "pl": "- **„Pozycje” otwierają się na najnowszych liczbach.** Każdy wiersz okna to to, co strona pokazuje właśnie teraz: transakcje dnia są już w liczbie akcji i rozcieńczonym koszcie, tych samych liczbach co na liście. Samo obejrzenie nie porusza księgi ani o bajt; prawdziwa zmiana wiersza to zapis w samej księdze — odtąd odtwarzanie dnia rysuje już tylko znaczniki, nie licząc akcji po raz drugi. Przy wyjściu ostatnie pozycje dnia składają się do księgi, gotowe na jutro.",
    "cs": "- **„Pozice” se otevírají s nejnovějšími čísly.** Každý řádek okna je to, co stránka právě ukazuje: obchody dne jsou už v počtu akcí a zředěných nákladech, stejných číslech jako v seznamu. Pouhé pohlednutí knihu nepohně o bajt; skutečná změna řádku je zápis do samotné knihy — od té chvíle přehrávání dne kreslí jen značky, aniž by počty akcí počítalo znovu. Při ukončení se poslední pozice dne složí do knihy, připravené na zítra.",
    "ru": "- **«Позиции» открываются на самых свежих цифрах.** Каждая строка окна — то, что страница показывает прямо сейчас: сделки дня уже учтены в количестве акций и усреднённой цене, тех же числах, что и в списке. Простой просмотр не двигает книгу ни на байт; настоящая правка строки — это запись в саму книгу, и дальше воспроизведение дня рисует только отметки, не пересчитывая акции. При выходе последние позиции дня складываются в книгу, готовые к продолжению на следующий день.",
    "tr": "- **\"Pozisyonlar\" en güncel rakamlarla açılır.** Penceredeki her satır, sayfanın şu anda gösterdiği şeydir: günün işlemleri hisse adedinde ve seyreltilmiş maliyette hazırdır, listedeki rakamların aynısıdır. Bakmak dokunmamaktır, defter tek bayt oynamaz; bir satırı gerçekten değiştirmek defterin kendisine yazmaktır — o andan sonra günün oynatımı yalnızca işaretleri çizer, hisse adedini yeniden saymaz. Çıkışta günün son pozisyonları deftere katlanır, ertesi sabah kaldığı yerden sürer.",
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

        if any(line.strip() == DIALOG[tag] for line in section):
            print(f"{tag:9} already there")
            continue

        # 插在最后一个粗体条之后（当前是「导入成交」那条）。
        bolds = [i for i in range(start, end) if lines[i].startswith("- **")]

        assert bolds, f"{tag}: 本章没有粗体条"

        at = bolds[-1] + 1
        block = ["", DIALOG[tag]] if lines[at].strip() == "" else [DIALOG[tag]]
        lines[at:at] = block

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +1")


if __name__ == "__main__":
    main()
