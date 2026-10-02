# -*- coding: utf-8 -*-
r"""把「大类资产」一章插进 14 份帮助文档。

位置**按章节序号**定，不按标题文字：新章插在「指数长跑」之后、「收益矩阵」之前，
因为导航里这两页挨着——它们是同一副算术的两端，那页比发布的数字，这页比真正能
持有的东西。14 份文档的章节数与顺序必须相同，由 verify 脚本另行检查。

文件是 UTF-8 **带 BOM** + LF：`read_bytes().decode('utf-8-sig')` 读，写回时自己补 BOM。
`utf-8-sig` 只吃掉一个 BOM，文件里若已经叠了两个，要用 `lstrip('\ufeff')` 兜住。

幂等：标题已存在就整章重写。**改页面行为就要回来改这里的 BODIES** —— 市值榜那一章
曾经在榜单改了两次之后仍写着旧理由，见 `port-marketcap-help.py` 的说明。

用法：python tools\port-assetrace-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 插在第 11 章「指数长跑」之后（0 基下标 10），第 12 章「收益矩阵」之前。
AFTER = 10

TITLES = {
    "zh-Hans": "大类资产",
    "zh-Hant": "大類資產",
    "en-US": "Asset classes",
    "ja": "資産クラス",
    "ko": "자산군",
    "de": "Anlageklassen",
    "fr": "Classes d'actifs",
    "it": "Classi di attività",
    "es": "Clases de activos",
    "pt-BR": "Classes de ativos",
    "pl": "Klasy aktywów",
    "cs": "Třídy aktiv",
    "ru": "Классы активов",
    "tr": "Varlık sınıfları",
}

BODIES = {
    "zh-Hans": """一类资产一行，行是**持有它到今天赚了多少**，不是它的报价。八档都是境内交易所挂牌的基金，
买它们的钱是同一种钱，所以能直接比。

- **分红算回去了，份额折算也算回去了。** 债券和货币基金的收益几乎全在分红里：货币 ETF 的价格
  十三年从 100.161 走到 100.901，不调整是 +0.0%——那会把唯一从没跌过的那一行画成垫底。拆过份额
  的基金更极端：纳指 ETF 不调整只有 +136%，而它跟踪的指数十年涨了六倍。
- **和指数长跑正好相反。** 指数不派息，那一页不调整；基金会派息，这一页必须调整。两条路不能混。
- **境外那两行含着汇率。** 纳指 ETF 与恒生 ETF 用人民币计价，汇率的涨跌已经在里面——这正是境内
  持有人真实拿到的数。
- **起点各不相同。** 最早的一档是 2012 年，豆粕 ETF 要到 2019 年才有。没上场的行是缺席，
  不是 0.00%。
- **这一页不看市场设置**：八档都在境内挂牌，切换市场不影响它。不足 12 个月会拒绝取数。
""",
    "zh-Hant": """一類資產一行，行是**持有它到今天賺了多少**，不是它的報價。八檔都是境內交易所掛牌的基金，
買它們的錢是同一種錢，所以能直接比。

- **分紅算回去了，份額折算也算回去了。** 債券和貨幣基金的收益幾乎全在分紅裡：貨幣 ETF 的價格
  十三年從 100.161 走到 100.901，不調整是 +0.0%——那會把唯一從沒跌過的那一行畫成墊底。拆過份額
  的基金更極端：納指 ETF 不調整只有 +136%，而它跟蹤的指數十年漲了六倍。
- **和指數長跑正好相反。** 指數不派息，那一頁不調整；基金會派息，這一頁必須調整。兩條路不能混。
- **境外那兩行含著匯率。** 納指 ETF 與恆生 ETF 用人民幣計價，匯率的漲跌已經在裡面——這正是境內
  持有人真實拿到的數。
- **起點各不相同。** 最早的一檔是 2012 年，豆粕 ETF 要到 2019 年才有。沒上場的行是缺席，
  不是 0.00%。
- **這一頁不看市場設定**：八檔都在境內掛牌，切換市場不影響它。不足 12 個月會拒絕取數。
""",
    "en-US": """One row per asset class, and the row is **what holding it earned** — not its quote. All eight are
funds listed on a mainland exchange, bought with the same money, so they can be compared directly.

- **Dividends are put back in, and share splits too.** A bond and a cash fund pay almost entirely in
  income: the money-market ETF's price went from 100.161 to 100.901 across thirteen years, which
  unadjusted is +0.0% — and would draw the one row here that never fell as the bottom of the board.
  A fund that split its units is starker still: the Nasdaq ETF is +136% unadjusted, while the index
  it tracks rose sixfold over the same decade.
- **Deliberately the opposite of the index race.** An index pays no dividend, so that page is left
  alone; a fund does pay, so this one has to be adjusted. The two paths do not mix.
- **The two overseas rows carry the exchange rate.** The Nasdaq and Hang Seng ETFs are quoted in
  yuan, so the currency's moves are already inside them — which is what a mainland holder actually
  got.
- **Start dates differ.** The earliest row begins in 2012 and the commodity fund only in 2019. A row
  that has not joined yet is absent, not 0.00%.
- **The market setting does not govern this page**: all eight are listed on the mainland. Fewer than
  twelve months is refused.
""",
    "ja": """資産クラスごとに1行。行は**保有して今日までに稼いだ額**であり、気配値ではありません。
8本すべてが本土の取引所に上場するファンドで、買うお金は同じお金なので直接比べられます。

- **配当は戻し入れられ、受益権の分割も同様に戻されます。** 債券とマネーマーケットファンドは
  その收益のほとんどを配当で支払います。マネーマーケットETFの価格は13年で100.161から100.901へ、
  調整しなければ+0.0%——ここで一度も下落していない唯一の行を最下位に描くことになります。
  受益権を分割したファンドはさらに極端で、ナスダックETFは未調整で+136%ですが、その指数は同じ
  10年で6倍になりました。
- **指数レースとは意図的に逆です。** 指数は配当を払わないのであちらは調整しません。ファンドは
  払うのでこちらは調整が必要です。二つの経路は混ぜられません。
- **海外の2行は為替を含みます。** ナスダックETFとハンセンETFは人民元建てなので、為替の動きは
  すでに中に入っています——本土の保有者が実際に受け取ったものです。
- **開始はまちまちです。** 最も早い行は2012年、コモディティファンドは2019年からです。まだ
  登場していない行は不在であり、0.00%ではありません。
- **市場設定はこのページを管轄しません**：8本すべてが本土上場です。12か月未満は拒否されます。
""",
    "ko": """자산군마다 한 행이며, 행은 **보유해서 오늘까지 벌어들인 것**입니다. 시세가 아닙니다. 여덟 개
모두 본토 거래소에 상장된 펀드이고 사는 돈이 같은 돈이므로 직접 비교할 수 있습니다.

- **배당을 되돌려 넣고, 수익증권 분할도 되돌려 넣습니다.** 채권과 머니마켓펀드는 수익의 거의 전부를
  배당으로 지급합니다. 머니마켓 ETF의 가격은 13년간 100.161에서 100.901로 갔고, 미조정이면
  +0.0%입니다—한 번도 하락하지 않은 유일한 행을 최하위로 그리게 됩니다. 수익증권을 분할한 펀드는
  더 극적입니다. 나스닥 ETF는 미조정으로 +136%지만 같은 10년 동안 지수는 6배가 되었습니다.
- **지수 레이스와 의도적으로 반대입니다.** 지수는 배당을 지급하지 않으므로 그쪽은 조정하지 않고,
  펀드는 지급하므로 이쪽은 조정해야 합니다. 두 경로는 섞을 수 없습니다.
- **해외 두 행은 환율을 담고 있습니다.** 나스닥 ETF와 항셍 ETF는 위안화로 표시되므로 환율 변동이
  이미 안에 있습니다—본토 보유자가 실제로 받은 것입니다.
- **시작은 제각각입니다.** 가장 이른 행은 2012년, 상품 펀드는 2019년부터입니다. 아직 등장하지 않은
  행은 부재이며 0.00%가 아닙니다.
- **시장 설정은 이 페이지를 관할하지 않습니다**: 여덟 개 모두 본토에 상장되어 있습니다. 12개월
  미만은 거부됩니다.
""",
    "de": """Eine Zeile pro Anlageklasse, und die Zeile ist **was das Halten eingebracht hat** — nicht die
Notierung. Alle acht sind an einer Festlandbörse notierte Fonds, mit demselben Geld gekauft, also
direkt vergleichbar.

- **Ausschüttungen sind eingerechnet, Aktiensplits ebenfalls.** Eine Anleihe und ein Geldmarktfonds
  zahlen fast vollständig in Erträgen: Der Kurs des Geldmarkt-ETF ging in dreizehn Jahren von
  100,161 auf 100,901 — unadjustiert +0,0 %, was die einzige Zeile hier, die nie fiel, als Letzte
  der Tafel zeichnen würde. Ein Fonds, der seine Anteile gesplittet hat, ist drastischer: Der
  Nasdaq-ETF liegt unadjustiert bei +136 %, während der Index, dem er folgt, sich im selben
  Jahrzehnt versechsfacht hat.
- **Mit Absicht das Gegenteil des Index-Rennens.** Ein Index zahlt keine Dividende, jene Seite
  bleibt also unangetastet; ein Fonds zahlt, diese muss adjustiert werden. Die beiden Wege
  mischen sich nicht.
- **Die beiden ausländischen Zeilen tragen den Wechselkurs.** Der Nasdaq- und der Hang-Seng-ETF
  werden in Yuan notiert, die Währungsbewegung steckt also schon darin — genau das, was ein
  Festland-Anleger tatsächlich bekommen hat.
- **Die Anfänge unterscheiden sich.** Die früheste Zeile beginnt 2012, der Rohstofffonds erst 2019.
  Eine Zeile, die noch nicht dabei ist, fehlt, statt bei 0,00 % zu stehen.
- **Die Markteinstellung regiert diese Seite nicht**: alle acht sind auf dem Festland notiert.
  Weniger als zwölf Monate werden abgelehnt.
""",
    "fr": """Une ligne par classe d'actifs, et la ligne est **ce que la détention a rapporté** — pas le cours.
Les huit sont des fonds cotés sur une place continentale, achetés avec le même argent, donc
directement comparables.

- **Les dividendes sont réintégrés, et les scissions aussi.** Une obligation et un fonds monétaire
  paient presque entièrement en revenus : le cours du fonds monétaire est passé de 100,161 à
  100,901 en treize ans, soit +0,0 % sans ajustement — ce qui dessinerait en bas du tableau la seule
  ligne ici qui n'a jamais baissé. Un fonds ayant divisé ses parts est plus net encore : l'ETF
  Nasdaq affiche +136 % sans ajustement, alors que l'indice qu'il suit a sextuplé sur la même
  décennie.
- **Volontairement l'inverse de la course des indices.** Un indice ne verse pas de dividende, cette
  page-là est donc laissée telle quelle ; un fonds en verse, celle-ci doit être ajustée. Les deux
  voies ne se mélangent pas.
- **Les deux lignes étrangères portent le change.** Les ETF Nasdaq et Hang Seng sont cotés en yuan :
  la devise est déjà dedans — c'est ce qu'un détenteur continental a réellement obtenu.
- **Les débuts diffèrent.** La ligne la plus ancienne commence en 2012 et le fonds matières
  premières seulement en 2019. Une ligne qui n'a pas encore rejoint la course est absente, pas à
  0,00 %.
- **Le réglage de marché ne régit pas cette page** : les huit sont cotés sur le continent. Moins de
  douze mois est refusé.
""",
    "it": """Una riga per classe di attività, e la riga è **ciò che la detenzione ha reso** — non la
quotazione. Tutti e otto sono fondi quotati su una borsa continentale, comprati con lo stesso
denaro, quindi direttamente confrontabili.

- **I dividendi sono reinseriti, e anche i frazionamenti.** Un'obbligazione e un fondo monetario
  pagano quasi interamente in reddito: il prezzo dell'ETF monetario è passato da 100,161 a 100,901
  in tredici anni, che non aggiustato è +0,0% — e disegnerebbe in fondo alla tavola l'unica riga
  qui che non è mai scesa. Un fondo che ha frazionato le quote è ancora più netto: l'ETF Nasdaq
  segna +136% non aggiustato, mentre l'indice che replica è salito di sei volte nello stesso
  decennio.
- **Volutamente l'opposto della corsa degli indici.** Un indice non paga dividendi, quindi quella
  pagina è lasciata com'è; un fondo li paga, quindi questa va aggiustata. Le due strade non si
  mescolano.
- **Le due righe estere portano il cambio.** Gli ETF Nasdaq e Hang Seng sono quotati in yuan, quindi
  la valuta è già dentro — che è ciò che un detentore continentale ha davvero ottenuto.
- **Le partenze differiscono.** La riga più antica inizia nel 2012 e il fondo su materie prime solo
  nel 2019. Una riga non ancora entrata è assente, non a 0,00%.
- **L'impostazione di mercato non governa questa pagina**: tutti e otto sono quotati sul continente.
  Meno di dodici mesi è rifiutato.
""",
    "es": """Una fila por clase de activo, y la fila es **lo que ganó mantenerlo** — no su cotización. Las ocho
son fondos cotizados en una bolsa continental, comprados con el mismo dinero, así que se pueden
comparar directamente.

- **Los dividendos se reintegran, y también los splits.** Un bono y un fondo monetario pagan casi
  por completo en rentas: el precio del ETF monetario pasó de 100,161 a 100,901 en trece años, lo
  que sin ajuste es +0,0 % — y dibujaría al final del tablero la única fila de aquí que nunca cayó.
  Un fondo que dividió sus participaciones es aún más claro: el ETF Nasdaq da +136 % sin ajuste,
  mientras que el índice que sigue se sextuplicó en la misma década.
- **Deliberadamente lo contrario de la carrera de índices.** Un índice no paga dividendos, así que
  aquella página se deja intacta; un fondo sí paga, así que esta debe ajustarse. Los dos caminos no
  se mezclan.
- **Las dos filas extranjeras llevan el tipo de cambio.** Los ETF de Nasdaq y Hang Seng cotizan en
  yuanes, así que la divisa ya está dentro — que es lo que un tenedor continental recibió de verdad.
- **Los inicios difieren.** La fila más antigua empieza en 2012 y el fondo de materias primas solo
  en 2019. Una fila que aún no ha entrado está ausente, no en 0,00 %.
- **El ajuste de mercado no gobierna esta página**: las ocho cotizan en el continente. Menos de doce
  meses se rechaza.
""",
    "pt-BR": """Uma linha por classe de ativos, e a linha é **o que a manutenção rendeu** — não a cotação. Todas as
oito são fundos listados em uma bolsa continental, comprados com o mesmo dinheiro, então podem ser
comparadas diretamente.

- **Os dividendos são reintegrados, e também os desdobramentos.** Um título e um fundo de mercado
  monetário pagam quase inteiramente em renda: o preço do ETF de mercado monetário foi de 100,161 a
  100,901 em treze anos, o que sem ajuste é +0,0% — e desenharia no fim do quadro a única linha daqui
  que nunca caiu. Um fundo que desdobrou cotas é ainda mais claro: o ETF Nasdaq dá +136% sem ajuste,
  enquanto o índice que ele segue subiu seis vezes na mesma década.
- **Deliberadamente o oposto da corrida de índices.** Um índice não paga dividendos, então aquela
  página fica como está; um fundo paga, então esta precisa ser ajustada. Os dois caminhos não se
  misturam.
- **As duas linhas estrangeiras carregam o câmbio.** Os ETFs de Nasdaq e Hang Seng são cotados em
  yuan, então a moeda já está dentro — que é o que um detentor continental realmente recebeu.
- **Os inícios diferem.** A linha mais antiga começa em 2012 e o fundo de commodities apenas em
  2019. Uma linha que ainda não entrou está ausente, não em 0,00%.
- **A configuração de mercado não rege esta página**: todas as oito são listadas no continente.
  Menos de doze meses é recusado.
""",
    "pl": """Jeden wiersz na klasę aktywów, a wiersz to **ile zarobiło trzymanie** — nie notowanie. Wszystkie
osiem to fundusze notowane na giełdzie kontynentalnej, kupione za te same pieniądze, więc można je
porównywać wprost.

- **Dywidendy są wliczone, i podziały też.** Obligacja i fundusz rynku pieniężnego płacą prawie
  wyłącznie dochodem: cena funduszu rynku pieniężnego przeszła w trzynaście lat ze 100,161 do
  100,901, co bez korekty jest +0,0% — narysowałoby na dole tablicy jedyny wiersz, który nigdy nie
  spadł. Fundusz po podziale jednostek jest bardziej jaskrawy: ETF Nasdaq ma bez korekty +136%,
  podczas gdy indeks, który naśladuje, w tej samej dekadzie wzrósł sześciokrotnie.
- **Celowo odwrotność wyścigu indeksów.** Indeks nie płaci dywidend, więc tamta strona zostaje
  nietknięta; fundusz płaci, więc tę trzeba korygować. Tych dwóch dróg się nie miesza.
- **Dwa zagraniczne wiersze niosą kurs.** ETF-y Nasdaq i Hang Seng są notowane w juanach, więc
  waluta jest już w środku — to właśnie dostał posiadacz z kontynentu.
- **Początki się różnią.** Najwcześniejszy wiersz zaczyna się w 2012, a fundusz towarowy dopiero w
  2019. Wiersza, który jeszcze nie wszedł, nie ma — nie stoi na 0,00%.
- **Ustawienie rynku tu nie rządzi**: wszystkie osiem jest notowanych na kontynencie. Mniej niż
  dwanaście miesięcy jest odrzucane.
""",
    "cs": """Jeden řádek na třídu aktiv a řádek je **co držení vyneslo** — ne kotace. Všech osm jsou fondy
kotované na kontinentální burze, koupené za stejné peníze, takže je lze srovnávat přímo.

- **Dividendy jsou zpět započteny, a štěpení také.** Dluhopis a fond peněžního trhu platí téměř
  celou výnosem: cena fondu peněžního trhu šla za třináct let ze 100,161 na 100,901, což je bez
  úpravy +0,0 % — a nakreslilo by na konec tabule jediný řádek, který nikdy neklesl. Fond po
  štěpení podílů je ještě výraznější: ETF Nasdaq má bez úpravy +136 %, zatímco index, který sleduje,
  ve stejném desetiletí vzrostl šestinásobně.
- **Záměrně opak závodu indexů.** Index nevyplácí dividendu, takže tamta stránka zůstává bez úprav;
  fond vyplácí, takže tato se upravovat musí. Ty dvě cesty se nemíchají.
- **Dva zahraniční řádky nesou kurz.** ETF Nasdaq a Hang Seng jsou kotovány v jüanech, takže měna je
  už uvnitř — přesně to, co držitel z pevniny skutečně dostal.
- **Začátky se liší.** Nejstarší řádek začíná v roce 2012 a komoditní fond až v roce 2019. Řádek,
  který ještě nenastoupil, chybí — nestojí na 0,00 %.
- **Nastavení trhu tuto stránku neřídí**: všech osm je kotováno na pevnině. Méně než dvanáct měsíců
  je odmítnuto.
""",
    "ru": """Одна строка на класс активов, и строка — это **что принесло владение**, а не котировка. Все восемь —
фонды, котируемые на материковой бирже и купленные на одни и те же деньги, поэтому их можно
сравнивать напрямую.

- **Дивиденды возвращены в ряд, и дробления тоже.** Облигация и фонд денежного рынка платят почти
  целиком доходом: цена биржевого фонда денежного рынка прошла за тринадцать лет от 100,161 до
  100,901, что без поправки есть +0,0% — и нарисовало бы внизу доски единственную строку, которая
  ни разу не падала. Фонд, дробивший паи, ещё показательнее: ETF Nasdaq без поправки даёт +136%,
  тогда как индекс, за которым он следует, за то же десятилетие вырос в шесть раз.
- **Намеренно противоположно гонке индексов.** Индекс не платит дивидендов, поэтому та страница
  оставлена как есть; фонд платит, поэтому эту нужно корректировать. Два пути не смешиваются.
- **Две зарубежные строки несут курс.** ETF Nasdaq и Hang Seng котируются в юанях, поэтому валюта
  уже внутри — именно это материковый держатель реально и получил.
- **Начала различаются.** Самая ранняя строка начинается в 2012 году, а товарный фонд — лишь в 2019.
  Строка, которая ещё не вышла на доску, отсутствует, а не стоит в 0,00%.
- **Настройка рынка этой страницей не управляет**: все восемь котируются на материке. Меньше
  двенадцати месяцев отклоняется.
""",
    "tr": """Her varlık sınıfı için bir satır ve satır, **onu tutmanın kazandırdığıdır** — kotasyonu değil.
Sekizi de anakara borsasında işlem gören fonlar ve aynı parayla alınır, bu yüzden doğrudan
karşılaştırılabilir.

- **Temettüler geri konur, pay bölünmeleri de.** Bir tahvil ve bir para piyasası fonu neredeyse
  tamamen getiri öder: para piyasası ETF'sinin fiyatı on üç yılda 100,161'den 100,901'e gitti ve
  düzeltilmezse bu +0,0%'dir — burada hiç düşmemiş tek satırı tablonun dibine çizerdi. Payını bölen
  bir fon daha da çarpıcıdır: Nasdaq ETF düzeltilmeden +136%, oysa izlediği endeks aynı on yılda
  altı katına çıktı.
- **Bilerek endeks yarışının tersi.** Bir endeks temettü ödemez, o sayfa olduğu gibi bırakılır; bir
  fon öder, bu sayfanın düzeltilmesi gerekir. İki yol karışmaz.
- **İki yabancı satır kuru taşır.** Nasdaq ve Hang Seng ETF'leri yuan cinsindendir, yani kur zaten
  içindedir — anakara yatırımcısının gerçekten aldığı budur.
- **Başlangıçlar farklı.** En eski satır 2012'de başlar, emtia fonu ancak 2019'da. Henüz katılmamış
  bir satır yoktur, %0,00'de durmaz.
- **Piyasa ayarı bu sayfayı yönetmez**: sekizi de anakarada işlem görür. On iki aydan kısa dönemler
  reddedilir.
""",
}


def main():
    for tag, title in TITLES.items():
        path = HELP / f"help-{tag}.md"

        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")
        lines = text.replace("\r\n", "\n").split("\n")

        want = f"## {title}"

        # Idempotent: drop the chapter wherever it already sits, then put it back in place.
        if want in lines:
            at = lines.index(want)

            heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
            after = [i for i in heads if i > at]
            end = after[0] if after else len(lines)

            while end > at and lines[end - 1].strip() == "":
                end -= 1

            del lines[at:end]

        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(heads) < AFTER + 2:
            raise AssertionError(f"{tag}: only {len(heads)} chapters")

        at = heads[AFTER + 1]

        block = [want, ""] + BODIES[tag].rstrip("\n").split("\n") + [""]

        lines[at:at] = block

        out = "\n".join(lines)

        if not out.endswith("\n"):
            out += "\n"

        path.write_bytes(b"\xef\xbb\xbf" + out.encode("utf-8"))

        chapters = sum(1 for line in out.split("\n") if line.startswith("## "))

        print(f"{tag}: inserted after chapter {AFTER + 1}, now {chapters} chapters")


if __name__ == "__main__":
    main()
