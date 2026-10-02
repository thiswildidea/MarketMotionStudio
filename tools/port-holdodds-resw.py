# -*- coding: utf-8 -*-
r"""把「持有胜率」这一页的 resw 键注入 14 份 Resources.resw。

第十六个页面。前两页（大类资产 / 回撤与修复）对着同一批八档问了两个问题：
赚了多少、付出了什么代价。这一页问第三个——随便什么时候进去，这事儿有多常
成立。

**复用第十四页的键**：标的三组的名字（`AssetRaceListAll` 等）、区间的选项与
「最长」（`DcaRange3Y` / `AssetRaceRangeMax`）、下拉的头（`AssetRaceList.Header`）、
表头两个计数词（`AssetRaceUnitAssets` / `MarketCapUnitMonths`）。三页跑的是同一批
标的，一个东西有三个名字就是让读的人自己翻译。本脚本只读它们，不写。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。
第一列必须是英文——`port-ahpremium-resw.py` 里 `AhPremiumFetched` 就是在
这里栽过：第一列写成了中文，英文界面于是显示一整行中文状态。

用法：python tools\port-holdodds-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 导航项、页面标题、无数据时舞台上的标题，共用一份：三处说的是同一件事。
NAV = [
    "Hold odds", "Haltequote", "Tasa de acierto", "Taux de réussite",
    "Tasso di riuscita", "Skuteczność", "Taxa de acerto", "Úspěšnost",
    "Tutma oranı", "Доля удачных", "保有勝率", "보유 승률",
    "持有勝率", "持有胜率",
]

SUBTITLE = [
    "The same eight holdings as the asset race, scored on how often holding them worked: of every "
    "month a holder could have bought in and held for the same length of time, the share that "
    "ended up ahead.",

    "Dieselben acht Anlagen wie beim Rennen der Anlageklassen, bewertet danach, wie oft das Halten "
    "funktionierte: von allen Monaten, in denen man hätte einsteigen und gleich lang halten "
    "können, der Anteil, der am Ende im Plus lag.",

    "Las mismas ocho inversiones que en la carrera de clases de activos, puntuadas por cuántas "
    "veces funcionó mantenerlas: de todos los meses en que se pudo entrar y mantener el mismo "
    "tiempo, la proporción que acabó en ganancia.",

    "Les huit mêmes supports que la course des classes d'actifs, notés sur la fréquence à laquelle "
    "les détenir a fonctionné : parmi tous les mois où l'on aurait pu entrer et garder la même "
    "durée, la part qui s'est terminée dans le vert.",

    "Gli stessi otto strumenti della corsa delle classi di attività, valutati su quanto spesso "
    "tenerli ha funzionato: fra tutti i mesi in cui si sarebbe potuti entrare e mantenere per la "
    "stessa durata, la quota finita in guadagno.",

    "Te same osiem instrumentów co w wyścigu klas aktywów, oceniane według tego, jak często ich "
    "trzymanie się opłaciło: ze wszystkich miesięcy, w których można było wejść i trzymać równie "
    "długo, udział tych zakończonych na plusie.",

    "Os mesmos oito ativos da corrida de classes de ativos, pontuados por quantas vezes mantê-los "
    "funcionou: de todos os meses em que se poderia ter entrado e mantido pelo mesmo tempo, a "
    "parcela que terminou no positivo.",

    "Týchž osm nástrojů jako v závodu tříd aktiv, hodnocených podle toho, jak často držení "
    "fungovalo: ze všech měsíců, v nichž se dalo vstoupit a držet stejně dlouho, podíl těch, "
    "které skončily v plusu.",

    "Varlık sınıfları yarışındaki aynı sekiz varlık, ama puanı elde tutmanın işe yarama sıklığına "
    "göre: aynı süre boyunca girilip tutulabilecek her ay içinde, kârla bitenlerin payı.",

    "Те же восемь инструментов, что в гонке классов активов, но оценённые по тому, как часто "
    "удержание срабатывало: из всех месяцев, в которые можно было войти и держать одинаково долго, "
    "доля завершившихся в плюсе.",

    "資産クラスレースと同じ八つの資産を、保有がうまくいった頻度で採点する——同じ期間だけ買って"
    "保有できるすべての月のうち、最終的にプラスになった割合。",

    "자산군 경주와 같은 여덟 자산을 보유가 얼마나 자주 통했는지로 평가한다—같은 기간만 사서 "
    "보유할 수 있었던 모든 달 중, 결국 플러스로 끝난 비율.",

    "與「大類資產」同為那八檔，但打分的是「持有」這件事多常成立：在區間裡每一個可以買進並"
    "持有相同時間的月份中，最後是賺的那一部分佔多少。",

    "与「大类资产」同为那八档，但打分的是「持有」这件事多常成立：在区间里每一个可以买进并"
    "持有相同时间的月份中，最后是赚的那一部分占多少。",
]

NOTE = [
    "A row is the share of finished entries that gained. Every month in the range is an entry, "
    "each held for the same length of time: one entry is luck, eighty-four of them are a rate.",

    "Eine Zeile ist der Anteil der beendeten Einstiege, die gewonnen haben. Jeder Monat im "
    "Zeitraum ist ein Einstieg, alle gleich lang gehalten: ein Einstieg ist Glück, vierundachtzig "
    "sind eine Quote.",

    "Cada fila es la proporción de entradas terminadas que ganaron. Cada mes del periodo es una "
    "entrada, todas mantenidas el mismo tiempo: una entrada es suerte, ochenta y cuatro son una "
    "tasa.",

    "Une ligne est la part des entrées terminées qui ont gagné. Chaque mois de la période est une "
    "entrée, toutes gardées la même durée : une entrée, c'est de la chance ; quatre-vingt-quatre, "
    "c'est un taux.",

    "Una riga è la quota delle entrate concluse che hanno guadagnato. Ogni mese dell'intervallo è "
    "un'entrata, tutte mantenute per la stessa durata: un'entrata è fortuna, ottantaquattro sono "
    "un tasso.",

    "Wiersz to udział zakończonych wejść, które zarobiły. Każdy miesiąc okresu jest wejściem, "
    "wszystkie trzymane równie długo: jedno wejście to szczęście, osiemdziesiąt cztery to "
    "wskaźnik.",

    "Uma linha é a parcela das entradas concluídas que ganharam. Cada mês do período é uma entrada, "
    "todas mantidas pelo mesmo tempo: uma entrada é sorte, oitenta e quatro são uma taxa.",

    "Řádek je podíl uzavřených vstupů, které vydělaly. Každý měsíc období je vstup, všechny držené "
    "stejně dlouho: jeden vstup je náhoda, osmdesát čtyři je míra.",

    "Bir satır, kazançla biten tamamlanmış girişlerin payıdır. Aralıktaki her ay bir giriştir ve "
    "hepsi aynı süre tutulur: bir giriş şanstır, seksen dördü bir orandır.",

    "Строка — это доля завершённых входов, которые оказались в плюсе. Каждый месяц диапазона — это "
    "вход, и все они держатся одинаково долго: один вход — это везение, восемьдесят четыре — это "
    "доля.",

    "行は、利益で終わった完了エントリーの割合。区間の各月がエントリーで、どれも同じ期間"
    "保有する——一つのエントリーは運、八十四个は率である。",

    "행은 이익으로 끝난 완료 진입의 비율이다. 구간의 매달이 진입이며 모두 같은 기간 "
    "보유한다—하나의 진입은 운이고, 여든네 개는 비율이다.",

    "一行是已走完的持有中賺錢的那一部分。區間裡每一個月都是一次買進，每一次都持有相同的時間："
    "一次是運氣，八十四次才是比率。",

    "一行是已走完的持有中赚钱的那一部分。区间里每一个月都是一次买进，每一次都持有相同的时间："
    "一次是运气，八十四次才是比率。",
]

METHOD = [
    "Monthly and adjusted — dividends and splits put back — and each row starts on its own first "
    "month. An entry counts from the month it finishes, so nothing bought near the end of the "
    "range is counted as a loss; a row joins once six entries have finished.",

    "Monatlich und adjustiert – Dividenden und Splits eingerechnet – und jede Zeile beginnt in "
    "ihrem eigenen ersten Monat. Ein Einstieg zählt ab dem Monat, in dem er endet, damit nichts, "
    "was am Ende des Zeitraums gekauft wurde, als Verlust zählt; eine Zeile kommt dazu, sobald "
    "sechs Einstiege beendet sind.",

    "Mensual y ajustado — dividendos y splits incluidos — y cada fila empieza en su propio primer "
    "mes. Una entrada cuenta desde el mes en que termina, para que nada comprado cerca del final "
    "del periodo cuente como pérdida; una fila entra cuando han terminado seis entradas.",

    "Mensuel et ajusté — dividendes et divisions intégrés — et chaque ligne commence à son propre "
    "premier mois. Une entrée compte à partir du mois où elle se termine : rien de ce qui est "
    "acheté près de la fin de la période n'est compté comme une perte ; une ligne arrive dès que "
    "six entrées sont terminées.",

    "Mensile e aggiustato — dividendi e frazionamenti inclusi — e ogni riga parte dal proprio primo "
    "mese. Un'entrata conta dal mese in cui finisce, così nulla di ciò che è comprato vicino alla "
    "fine dell'intervallo conta come perdita; una riga entra quando sei entrate sono concluse.",

    "Miesięcznie i z korektą — dywidendy i splity wliczone — a każdy wiersz zaczyna się w swoim "
    "pierwszym miesiącu. Wejście liczy się od miesiąca, w którym się kończy, więc nic kupionego "
    "blisko końca okresu nie jest liczone jako strata; wiersz dołącza, gdy zakończy się sześć "
    "wejść.",

    "Mensal e ajustado — dividendos e desdobramentos incluídos — e cada linha começa no seu "
    "primeiro mês. Uma entrada conta a partir do mês em que termina, para que nada comprado perto "
    "do fim do período seja contado como perda; uma linha entra quando seis entradas terminaram.",

    "Měsíčně a s úpravou — dividendy a štěpení započítány — a každý řádek začíná ve svém prvním "
    "měsíci. Vstup se počítá od měsíce, v němž končí, takže nic koupeného blízko konce období se "
    "nepočítá jako ztráta; řádek nastupuje, jakmile skončí šest vstupů.",

    "Aylık ve düzeltilmiş — temettüler ve bölünmeler dahil — ve her satır kendi ilk ayında başlar. "
    "Bir giriş, bittiği aydan itibaren sayılır; böylece aralığın sonuna yakın alınan hiçbir şey "
    "zarar sayılmaz; altı giriş tamamlandığında satır katılır.",

    "Ежемесячно и с поправкой — дивиденды и сплиты возвращены — и каждая строка начинается в своём "
    "первом месяце. Вход считается с месяца, в котором он завершился, поэтому ничто, купленное "
    "ближе к концу диапазона, не считается убытком; строка появляется, когда завершились шесть "
    "входов.",

    "月次・調整済み（配当と分割を戻し込み）、各行は自分の最初の月から始まる。エントリーは"
    "完了した月から数えるため、区間の終わり近くで買った分が損失として数えられることはない。"
    "六つのエントリーが完了した時点で行が参加する。",

    "월간·조정 기준(배당과 분할 반영)이며 각 행은 자신의 첫 달에서 시작한다. 진입은 끝난 달부터 "
    "세므로 구간 끝 무렵에 산 것이 손실로 집계되지 않는다. 여섯 진입이 끝나면 행이 합류한다.",

    "月線、已復原（股息與份額折算都還原），每行從自己在區間裡的第一個月起算。一次持有從「走完的"
    "那個月」才計入，所以靠近區間末尾買進的不會被算成虧損；一個行要有六次持有走完才上板。",

    "月线、已复原（股息与份额折算都还原），每行从自己在区间里的第一个月起算。一次持有从「走完的"
    "那个月」才计入，所以靠近区间末尾买进的不会被算成亏损；一行要有六次持有走完才上板。",
]

# 持有期下拉的头。
HOLD = [
    "Holding period", "Haltedauer", "Periodo de tenencia", "Durée de détention",
    "Periodo di detenzione", "Okres utrzymania", "Período de manutenção", "Doba držení",
    "Tutma süresi", "Срок удержания", "保有期間", "보유 기간",
    "持有期", "持有期",
]

# 四档持有期。写全词而不是「1Y」：这一页的选项是一个时长，不是一个代号。
HOLD_1Y = [
    "1 year", "1 Jahr", "1 año", "1 an", "1 anno", "1 rok", "1 ano", "1 rok",
    "1 yıl", "1 год", "1 年", "1년", "1 年", "1 年",
]

HOLD_2Y = [
    "2 years", "2 Jahre", "2 años", "2 ans", "2 anni", "2 lata", "2 anos", "2 roky",
    "2 yıl", "2 года", "2 年", "2년", "2 年", "2 年",
]

HOLD_3Y = [
    "3 years", "3 Jahre", "3 años", "3 ans", "3 anni", "3 lata", "3 anos", "3 roky",
    "3 yıl", "3 года", "3 年", "3년", "3 年", "3 年",
]

HOLD_5Y = [
    "5 years", "5 Jahre", "5 años", "5 ans", "5 anni", "5 lat", "5 anos", "5 let",
    "5 yıl", "5 лет", "5 年", "5년", "5 年", "5 年",
]

# 七个占位符：档数、月数、持有几个月、最常赚的那档名字与胜率、最不常赚的那档名字与胜率。
FETCHED = [
    "Fetched {0} holdings · {1} months · held {2} months · most often ahead: {3} {4} · least often: {5} {6}",
    "{0} Anlagen geladen · {1} Monate · {2} Monate gehalten · am häufigsten im Plus: {3} {4} · am seltensten: {5} {6}",
    "Obtenidas {0} inversiones · {1} meses · mantenidas {2} meses · más a menudo en ganancia: {3} {4} · menos a menudo: {5} {6}",
    "{0} supports récupérés · {1} mois · détenus {2} mois · le plus souvent en gain : {3} {4} · le moins souvent : {5} {6}",
    "Recuperati {0} strumenti · {1} mesi · detenuti {2} mesi · più spesso in guadagno: {3} {4} · meno spesso: {5} {6}",
    "Pobrano {0} instrumentów · {1} miesięcy · trzymane {2} miesięcy · najczęściej na plusie: {3} {4} · najrzadziej: {5} {6}",
    "Obtidos {0} ativos · {1} meses · mantidos {2} meses · com mais frequência no positivo: {3} {4} · com menos frequência: {5} {6}",
    "Načteno {0} nástrojů · {1} měsíců · drženo {2} měsíců · nejčastěji v plusu: {3} {4} · nejméně často: {5} {6}",
    "{0} varlık alındı · {1} ay · {2} ay tutuldu · en sık kârda: {3} {4} · en az: {5} {6}",
    "Получено инструментов: {0} · месяцев: {1} · удерживались {2} мес. · чаще всего в плюсе: {3} {4} · реже всего: {5} {6}",
    "{0} 銘柄を取得 · {1} か月 · 保有 {2} か月 · プラスで終わった割合が最も高い: {3} {4} · 最も低い: {5} {6}",
    "{0}개 종목 조회 · {1}개월 · {2}개월 보유 · 가장 자주 플러스: {3} {4} · 가장 드물게: {5} {6}",
    "取到 {0} 檔 · {1} 個月 · 持有 {2} 個月 · 最常賺：{3} {4} · 最不常賺：{5} {6}",
    "取到 {0} 档 · {1} 个月 · 持有 {2} 个月 · 最常赚：{3} {4} · 最不常赚：{5} {6}",
]

TOO_FEW = [
    "Not enough months in that range for entries to finish — pick a longer range or a shorter holding period.",
    "Zu wenige Monate in diesem Zeitraum, als dass Einstiege enden könnten – wählen Sie einen längeren Zeitraum oder eine kürzere Haltedauer.",
    "No hay suficientes meses en ese periodo para que terminen las entradas: elija un periodo más largo o una tenencia más corta.",
    "Pas assez de mois dans cette période pour que des entrées se terminent — choisissez une période plus longue ou une durée de détention plus courte.",
    "Non abbastanza mesi in questo intervallo perché le entrate finiscano: scegliete un intervallo più lungo o un periodo di detenzione più breve.",
    "Za mało miesięcy w tym okresie, by wejścia zdążyły się zakończyć — wybierz dłuższy okres albo krótszy czas trzymania.",
    "Meses insuficientes nesse período para que as entradas terminem — escolha um período mais longo ou uma manutenção mais curta.",
    "V tomto období je příliš málo měsíců na to, aby vstupy skončily — zvolte delší období nebo kratší dobu držení.",
    "Girişlerin tamamlanması için bu aralıkta yeterince ay yok — daha uzun bir aralık ya da daha kısa bir tutma süresi seçin.",
    "В этом диапазоне слишком мало месяцев, чтобы входы успели завершиться, — выберите диапазон подлиннее или срок удержания покороче.",
    "この期間ではエントリーが完了するだけの月数が足りません——もっと長い期間か、もっと短い保有期間を選んでください。",
    "진입이 끝나기에 이 구간의 개월 수가 부족합니다—더 긴 구간이나 더 짧은 보유 기간을 고르세요.",
    "這個區間的月份不夠讓持有走完——請選長一點的區間，或短一點的持有期。",
    "这个区间的月份不够让持有走完——请选长一点的区间，或短一点的持有期。",
]

ROWS = [
    # `.Content`, not `.Text`: a NavigationViewItem is a ContentControl, and the x:Uid loader
    # asks for the property the type actually has. Written as `.Text` the app does not start.
    ("NavHoldOdds.Content", NAV),
    ("HoldOddsPageTitle.Text", NAV),
    ("HoldOddsStageTitle", NAV),
    ("HoldOddsPageSubtitle.Text", SUBTITLE),
    ("HoldOddsNote.Text", NOTE),
    ("HoldOddsMethodNote.Text", METHOD),
    ("HoldOddsHold.Header", HOLD),
    ("HoldOddsHold1Y", HOLD_1Y),
    ("HoldOddsHold2Y", HOLD_2Y),
    ("HoldOddsHold3Y", HOLD_3Y),
    ("HoldOddsHold5Y", HOLD_5Y),
    ("HoldOddsFetched", FETCHED),
    ("HoldOddsTooFew", TOO_FEW),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project file
    rather than the string that caused it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        lines = []

        for key, values in ROWS:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in ROWS:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at = text.rfind("</root>")
        assert at > 0, f"{tag}: no </root>"

        text = text[:at] + "".join(lines) + text[at:]

        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
