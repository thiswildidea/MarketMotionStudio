# -*- coding: utf-8 -*-
r"""把「加密货币月度收益」一章插进 14 份 help-*.md。

**位置按序号找，不按标题找**（`POSITION = 26`，也就是「Video」那一章之前）：14 份文件里
标题是各语言自己写的，唯一相同的是顺序。当前章序：加密市值榜占 25（0 起），视频在 26，
所以新章插在 26 —— 落在市值榜之后，与导航顺序一致。

**整块替换才算幂等**：先按「本章标题行」摘掉旧块再插（与 port-crypto-caps-help.py 同一招）。
注意本脚本与 caps 脚本各自先删自己那块、再按各自 POSITION 插回，两个 POSITION 互不干扰
（caps 删掉三章后视频回到 23；本脚本删掉一章后视频回到 26）。

**这一章暂不带配图行**：14 语言的加密页配图要在下一次发版前统一重拍
（`store-screenshots.py --crypto`）。到时候把 `("NavCryptoMatrix", "crypto-matrix.png")`
加进 port-help-images.py 的 PICTURES，跑一遍它就会把图行挂上 —— 现在写一个指向
不存在文件的图行只会让 verify-docs 红。

**这一章要说清的事**（14 份都要说，措辞各自来）：

1. 月份是**折叠**出来的：加密没有月K接口，日线全部历史取回后按月折；
   年数因此只是重读，改档不取数；
2. **没走完的月不算** —— 半个月冒充整月是这张图最容易被当真的错误；
3. 年数 1–10、没有「全部」：日线源端约十年封顶；备源只有一年，切到它格子只剩一行；
4. 收尾统计：最强月 / 最弱月 / 上涨月占比 / 最强单月。

文件是 **UTF-8 不带 BOM**；BOM 与行尾照抄原文。

用法：python tools\port-crypto-matrix-help.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

TAGS = [
    "en-US", "de", "es", "fr", "it", "pl", "pt-BR",
    "cs", "tr", "ru", "ja", "ko", "zh-Hans", "zh-Hant",
]

# 插在这里：「Video」那一章之前（现处 26，0 起）。市值榜占 25，新章落在它后面。
POSITION = 26

SECTIONS = {
    "en-US": """## Crypto Monthly Returns

One coin's month-by-month moves as a year × month grid, red for rises and green for falls, with the whole year compounded in the last column.

- **The months are folded, not asked for.** Crypto has no monthly endpoint: the page fetches everything the daily source holds — about ten years — and folds each month's last daily close against the month before's into that month's move. That also makes the year count a re-reading: changing it re-lays the grid and fetches nothing.
- **A month counts only when it is over.** The month being walked is not on the grid. Half a month's move dressed up as a whole one is the mistake this picture invites most, which is why it is made impossible rather than labelled.
- The years run 1–10, and there is no "all": the daily source tops out at about ten years, so the longest honest answer is the last entry. The fallback source carries a single year, and on it the grid is one row.
- The closing statistics give the strongest and the weakest month, the share of months that rose, and the strongest single month.
""",
    "de": """## Krypto-Monatsrenditen

Die Bewegungen einer Münze Monat für Monat als Jahr-×-Monat-Raster, rot für Steigungen und grün für Stürze, in der letzten Spalte das ganze Jahr aufgezinst.

- **Die Monate sind gefaltet, nicht erfragt.** Krypto hat keinen Monatsendpunkt: Die Seite holt alles, was die Tagesquelle hat — etwa zehn Jahre — und faltet den letzten Tagesschluss jedes Monats gegen den des Vormonats in die Bewegung dieses Monats. Die Jahreszahl ist damit nur ein Nachlesen: Sie legt das Raster neu und holt nichts.
- **Ein Monat zählt erst, wenn er vorbei ist.** Der laufende Monat steht nicht im Raster. Die Bewegung eines halben Monats im Kleid eines ganzen ist der Fehler, den dieses Bild am ehesten einlädt — deshalb wird er unmöglich gemacht, nicht beschriftet.
- Die Jahre laufen 1–10, und ein „Alle“ gibt es nicht: Die Tagesquelle endet bei etwa zehn Jahren, die längste ehrliche Antwort ist der letzte Eintrag. Die Ausweichquelle trägt ein einziges Jahr, und auf ihr ist das Raster eine Zeile.
- Die Abschlussstatistik nennt den stärksten und den schwächsten Monat, den Anteil der Monate im Plus und den stärksten einzelnen Monat.
""",
    "es": """## Rendimientos mensuales cripto

Los movimientos mes a mes de una moneda en una cuadrícula de año × mes, rojo para las subidas y verde para las bajadas, con el año completo compuesto en la última columna.

- **Los meses se pliegan, no se piden.** El mercado cripto no tiene un acceso mensual: la página trae todo lo que la fuente diaria guarda — unos diez años — y pliega el último cierre diario de cada mes contra el del mes anterior en el movimiento de ese mes. El número de años es, por eso, una releída: cambiarlo vuelve a tender la cuadrícula sin pedir nada.
- **Un mes cuenta solo cuando terminó.** El mes en curso no está en la cuadrícula. El movimiento de medio mes vestido de mes entero es el error que esta imagen más induce a creer; por eso se vuelve imposible en vez de avisarlo.
- Los años van de 1 a 10, y no hay «todos»: la fuente diaria llega a unos diez años, y la respuesta honesta más larga es la última. La fuente de respaldo lleva un solo año, y en ella la cuadrícula es una sola fila.
- La estadística final da el mes más fuerte y el más débil, la proporción de meses al alza y el mes individual más fuerte.
""",
    "fr": """## Rendements mensuels crypto

Les mouvements mois par mois d'une cryptomonnaie en une grille année × mois, rouge pour les hausses et vert pour les baisses, l'année entière composée dans la dernière colonne.

- **Les mois sont repliés, pas demandés.** Le marché crypto n'a pas d'accès mensuel : la page récupère tout ce que la source journalière détient — une dizaine d'années — et replie le dernier cours quotidien de chaque mois face à celui du mois précédent dans le mouvement de ce mois. Le nombre d'années n'est donc qu'une relecture : le changer retend la grille sans rien demander.
- **Un mois ne compte que lorsqu'il est terminé.** Le mois en cours n'est pas sur la grille. Le mouvement d'un demi-mois déguisé en mois entier est l'erreur que cette image invite le plus à prendre pour argent comptant ; c'est pourquoi elle est rendue impossible plutôt que signalée.
- Les années vont de 1 à 10, sans « tout » : la source journalière s'arrête à une dizaine d'années, et la plus longue réponse honnête est la dernière. La source de secours ne porte qu'une année, et dessus la grille tient en une seule ligne.
- Les statistiques finales donnent le mois le plus fort et le plus faible, la part des mois en hausse et le meilleur mois isolé.
""",
    "it": """## Rendimenti mensili crypto

I movimenti mese per mese di una moneta in una griglia anno × mese, rosso per i rialzi e verde per i ribassi, con l'intero anno composto nell'ultima colonna.

- **I mesi sono ripiegati, non richiesti.** Il mercato crypto non ha un endpoint mensile: la pagina recupera tutto ciò che la fonte giornaliera possiede — circa dieci anni — e ripiega l'ultima chiusura giornaliera di ogni mese contro quella del mese precedente nel movimento di quel mese. Il numero di anni è quindi una rilettura: cambiarlo stende di nuovo la griglia senza chiedere nulla.
- **Un mese conta solo quando è finito.** Il mese in corso non è sulla griglia. Il movimento di mezzo mese vestito da mese intero è l'errore che questa immagine invita più facilmente a prendere per buono; per questo lo si rende impossibile invece di segnalarlo.
- Gli anni vanno da 1 a 10, e non c'è «tutto»: la fonte giornaliera si ferma a circa dieci anni, e la risposta onesta più lunga è l'ultima voce. La fonte di riserva porta un solo anno, e su di essa la griglia è una sola riga.
- Le statistiche finali danno il mese più forte e il più debole, la quota dei mesi in rialzo e il singolo mese più forte.
""",
    "pl": """## Miesięczne stopy zwrotu krypto

Zmiany monety miesiąc po miesiącu jako siatka rok × miesiąc, czerwony dla wzrostów, zielony dla spadków, a w ostatniej kolumnie cały rok skumulowany.

- **Miesiące są składane, nie wypytane.** Rynek krypto nie ma miesięcznego źródła: strona pobiera wszystko, co niesie źródło dzienne — około dziesięciu lat — i składa ostatni kurs dzienny każdego miesiąca z kursem poprzedniego w zmianę tego miesiąca. Liczba lat to więc tylko ponowne odczytanie: jej zmiana rozkłada siatkę na nowo i niczego nie pobiera.
- **Miesiąc liczy się dopiero, gdy się skończył.** Bieżącego miesiąca na siatce nie ma. Zmiana pół miesiąca przebrana za cały to błąd, który ten obraz najłatwiej każe wziąć za dobrą monetę; dlatego zostaje uczyniony niemożliwym, a nie tylko opisany.
- Lata biegną od 1 do 10, a „wszystkich” nie ma: źródło dzienne kończy się na około dziesięciu latach, a najdłuższa uczciwa odpowiedź to ostatnia pozycja. Źródło zapasowe niesie jeden jedyny rok, a na nim siatka to jeden wiersz.
- Statystyki końcowe podają najsilniejszy i najsłabszy miesiąc, udział miesięcy na plusie oraz najsilniejszy pojedynczy miesiąc.
""",
    "pt-BR": """## Retornos mensais cripto

Os movimentos mês a mês de uma moeda em uma grade de ano × mês, vermelho para altas e verde para baixas, com o ano inteiro composto na última coluna.

- **Os meses são dobrados, não pedidos.** O mercado cripto não tem um acesso mensal: a página traz tudo o que a fonte diária guarda — cerca de dez anos — e dobra o último fechamento diário de cada mês contra o do mês anterior no movimento daquele mês. O número de anos é, por isso, uma releitura: mudá-lo redesenha a grade sem pedir nada.
- **Um mês só conta quando terminou.** O mês em andamento não está na grade. O movimento de meio mês vestido de mês inteiro é o erro que esta imagem mais induz a acreditar; por isso ele é tornado impossível, e não apenas avisado.
- Os anos vão de 1 a 10, e não há «todos»: a fonte diária chega a cerca de dez anos, e a resposta honesta mais longa é a última. A fonte de reserva carrega um único ano, e nela a grade é uma só fileira.
- As estatísticas finais dão o mês mais forte e o mais fraco, a proporção de meses em alta e o mês isolado mais forte.
""",
    "cs": """## Měsíční výnosy krypto

Měsíční pohyby jedné mince jako mřížka rok × měsíc, červená pro růsty, zelená pro poklesy, v posledním sloupci celý rok složený.

- **Měsíce se skládají, nevyptávají.** Krypto nemá měsíční zdroj: stránka stáhne vše, co denní zdroj drží — zhruba deset let — a složí poslední denní kurz každého měsíce s kurzem předchozího do pohybu toho měsíce. Počet let je proto jen opětovné čtení: jeho změna znovu rozestře mřížku a nic nestáhne.
- **Měsíc se počítá, až skončil.** Běžící měsíc v mřížce není. Pohyb půl měsíce převlečený za celý je chyba, kterou tento obraz nejsnáze svádí věřit; proto je učiněna nemožnou, nikoli pouze ohlášena.
- Roky běží 1–10 a „všechny“ nejsou: denní zdroj končí zhruba u deseti let a nejdelší poctivá odpověď je poslední položka. Záložní zdroj nese jediný rok, a na něm je mřížka jediná řada.
- Závěrečné statistiky dají nejsilnější a nejslabší měsíc, podíl měsíců v plusu a nejsilnější jednotlivý měsíc.
""",
    "tr": """## Kripto aylık getiriler

Bir coin'in ay ay hareketleri, yıl × ay ızgarası olarak; yükselişler kırmızı, düşüşler yeşil, son sütunda bileşik edilmiş bütün yıl.

- **Aylar katlanır, sorulmaz.** Kripto piyasasının aylık bir kaynağı yoktur: sayfa, günlük kaynağın tuttuğu her şeyi — yaklaşık on yıl — alır ve her ayın son günlük kapanışını önceki ayın kapanışıyla karşılaştırıp o ayın hareketine katlar. Yıl sayısı bu yüzden yalnızca bir yeniden okumadır: onu değiştirmek ızgarayı yeniden serer ve hiçbir şey istemez.
- **Bir ay ancak bittiğinde sayılır.** İçinde bulunulan ay ızgarada yok. Yarım ayın hareketinin bütün ay kılığına girmesi, bu resmin en kolay yuttuğu hatadır; bu yüzden imkânsız kılınır, yalnızca uyarı yapılmaz.
- Yıllar 1–10 arası ve «hepsi» yoktur: günlük kaynak yaklaşık on yılda biter, en uzun dürüst cevap son seçenektir. Yedek kaynak yalnızca bir yıl taşır, ve onunla ızgara tek sıradır.
- Kapanış istatistikleri en güçlü ve en zayıf ayı, artı kapanan ayların payını ve en güçlü tek ayı verir.
""",
    "ru": """## Месячная доходность крипто

Помесячная динамика монеты в виде сетки «год × месяц», красный — рост, зелёный — падение, в последнем столбце весь год с реинвестированием.

- **Месяцы складываются, а не запрашиваются.** У крипторынка нет месячного источника: страница забирает всё, что хранит дневной — около десяти лет — и складывает последний дневной курс каждого месяца с курсом предыдущего в движение этого месяца. Число лет потому лишь повторное чтение: изменить его значит заново расстелить сетку, ничего не запросив.
- **Месяц считается, только когда он закончился.** Текущего месяца на сетке нет. Движение полумесяца, переодетое в целый месяц, — ошибка, которую эта картинка легче всего навязывает за чистую монету; поэтому её делают невозможной, а не просто предупреждают о ней.
- Годы идут от 1 до 10, и «всех» нет: дневной источник заканчивается примерно десятью годами, и самый длинный честный ответ — последняя строка. Резервный источник несёт один-единственный год, и на нём сетка — один ряд.
- Итоговая статистика даёт самый сильный и самый слабый месяц, долю месяцев в плюсе и самый сильный отдельный месяц.
""",
    "ja": """## 暗号資産の月次リターン

ある暗号資産の月ごとの動きを「年 × 月」の格子に敷き詰めます。上が赤、下が緑。右端の列は一年を複利で合算した値です。

- **月は折り畳まれるのであって、尋ねられるのではない。** 暗号資産には月足の取得先がありません。ページは日足の取得元が持つすべて —— およそ十年 —— を取り込み、各月の月末終値を前月のそれと比べてその月の動きに折り畳みます。だから年数は読み直しにすぎません。変えても格子を敷き直すだけで、取り直しはしません。
- **月は終わってから数える。** 進行中の月は格子に載りません。半月の動きをひと月のふりで飾るのが、この図がいちばん顔から取り違えやすい誤りです。だから注意書きではなく、そもそも不可能にしてあります。
- 年数は 1〜10、「全部」はありません。日足の取得元はおよそ十年で頭打ちであり、いちばん長い正直な答えが最後の選択肢です。予備の取得元は一年分だけで、そちらでは格子は一列になります。
- 終わりの統計は、最強の月と最弱の月、上昇月の割合、最強の単月を示します。
""",
    "ko": """## 크립토 월간 수익률

한 코인의 월별 움직임을 연도 × 월 격자로 펼칩니다. 상승은 빨강, 하락은 초록, 마지막 열은 1년 전체를 복리로 합산한 값입니다.

- **월은 접어 만드는 것이지, 물어 오는 것이 아닙니다.** 암호화폐에는 월봉 출처가 없습니다. 페이지는 일봉 출처가 가진 전부 —— 약 10년 —— 을 가져와 각 달의 마지막 일간 종가를 전월 종가와 비교해 그 달의 움직임으로 접습니다. 연도 수는 그래서 다시 읽기일 뿐입니다. 바꾸면 격자를 다시 깔 뿐, 다시 가져오지 않습니다.
- **월은 끝나야 셉니다.** 진행 중인 달은 격자에 없습니다. 반 달의 움직임이 온 달인 양 꾸미는 것이 이 그림이 가장 얼굴에 직접 받아들이기 쉬운 오류입니다. 그래서 경고문이 아니라 애초에 불가능하게 만들어 뒀습니다.
- 연도는 1~10이며 「전체」는 없습니다. 일봉 출처는 약 10년에서 끝나므로 가장 긴 정직한 답이 마지막 항목입니다. 예비 출처는 1년치만 갖고 있으며, 그쪽에서는 격자가 한 줄이 됩니다.
- 마무리 통계는 가장 강한 달과 약한 달, 상승달의 비율, 가장 강한 단일 달을 보여줍니다.
""",
    "zh-Hans": """## 加密货币月度收益

把一个币种逐月的涨跌铺成年 × 月的格子，涨红跌绿，最右一栏是全年复利合计。

- **月份是折出来的，不是问出来的。** 加密市场没有月K接口：页面取回日线源端持有的全部历史——约十年——把每个月最后一天的收盘对上一个月，折成那一个月的涨跌。这也让年数只是一次重读：改年数是重新铺格子，不再取一次数。
- **没走完的月不算。** 进行中的那个月不会出现在格子上。半个月的涨跌冒充整月，是这张图最容易让人当真的错误；所以不是加一句提醒，而是让它根本进不来。
- 年数 1–10，没有「全部」：日线源端约十年封顶，最长的诚实答案就是最后一档。备源只有最近一年，切到它时格子只剩一行。
- 收尾统计给出最强月、最弱月、上涨月占比与最强单月。
""",
    "zh-Hant": """## 加密貨幣月度收益

把某個幣種逐月的漲跌鋪成年 × 月的格子，漲紅跌綠，最右一欄是全年複利合計。

- **月份是折出來的，不是問出來的。** 加密市場沒有月K介面：頁面取回日線源端持有的全部歷史——約十年——把每個月最後一天的收盤對上一個月，折成那一個月的漲跌。這也讓年數只是一次重讀：改年數是重新鋪格子，不再取一次數。
- **沒走完的月不算。** 進行中的那個月不會出現在格子上。半個月的漲跌冒充整月，是這張圖最容易讓人當真的錯誤；所以不是加一句提醒，而是讓它根本進不來。
- 年數 1–10，沒有「全部」：日線源端約十年封頂，最長的誠實答案就是最後一檔。備用源端只有最近一年，切到它時格子只剩一列。
- 收尾統計給出最強月、最弱月、上漲月占比與最強單月。
""",
}


def chapter_titles(tag):
    """本章的标题行，用来认旧块。"""
    return {line.strip() for line in SECTIONS[tag].split("\n") if line.startswith("## ")}


def main() -> int:
    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        raw = path.read_bytes()

        # BOM 与行尾照抄原文（这 14 份现在不带 BOM）。
        had_bom = raw.startswith(b"\xef\xbb\xbf")

        text = raw.decode("utf-8-sig").lstrip("\ufeff")

        crlf = "\r\n" in text
        joiner = "\r\n" if crlf else "\n"
        lines = text.split(joiner)

        # 整块摘掉：按本章标题行认（块里只有一个 ##，但招式与 caps 脚本一致）。
        titles = chapter_titles(tag)

        kept = []
        skipping = False

        for line in lines:
            if line.startswith("## "):
                skipping = line.strip() in titles

            if not skipping:
                kept.append(line)

        headings = [i for i, line in enumerate(kept) if line.startswith("## ")]

        if len(headings) <= POSITION:
            print(f"{tag}: only {len(headings)} headings, expected more than {POSITION}")
            return 1

        section = SECTIONS[tag].rstrip("\n").split("\n")

        # 位置由序号定，不由标题定：14 份文件里唯一相同的是顺序。
        at = headings[POSITION]

        lines = kept[:at] + section + [""] + kept[at:]

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + joiner.join(lines).encode("utf-8"))

        print(f"{tag:9} inserted before {kept[at]!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
