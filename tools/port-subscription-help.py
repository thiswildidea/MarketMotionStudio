# -*- coding: utf-8 -*-
r"""给 14 份帮助手册补上「订阅」这一件事。

**为什么非写不可，以及为什么是这三处。** 订阅买下的是两件事——导出视频、去掉水印——它们落在两章里，
而「去掉」后来又分出了两半：搬开关、和把浓度从上限调下来。

* **「视频」章**：导出被拦了一次。不看说明，用户只看到一个点了会弹对话框的按钮。这儿要写进去的
  是「订阅之前免费到哪一步」——没有这句话，「预览明明能播、为什么导不出来」会被当成 bug 报上来。
* **「动画背景」章**：水印那个开关现在拨不动了。既有那一整条还在说「留空则回到默认——
  什么都不加就把开关关掉」。这句话单独看依然通顺，和旁边那个搬不动的开关放在一起，就是把
  用户引向一个不存在的开关 —— 正是前面几轮反复记下的那类失效。所以新条目**紧贴在那一条
  后面**，而不是贴在章末。

**第三条为什么也写在这一本脚本里。** 浓度随后也进了订阅（未订阅时钉在上限、拨不动），而它在
手册上的落点是「水印长什么样」那一条的下游：那条写着「默认 10%」，此时只对订阅者成立，却摆
在所有人面前。三句回答的是同一个问题（订阅买下的是什么），放进三个文件就容易各说各的。同理
**不去改那一条本身**——它对订阅者仍然句句属实，改了反倒让一段话同时对着两拨读者。

**按那里锁定**：草稿的那句要靠已有脚本定，自己不再写第二个版本。

**为什么定位语句是从别处读来的，不是抄的。** 这两处的定位句已经写好在
`port-title-wrap-help.py`（HEADING / ENTRY）与 `port-watermark-help.py`（CHAPTER / WATERMARK）
里，每种语言一句。抄一份到本文件，就是同一句话在两处各写一版 —— 将来改了一处，另一处不会
跟着走，而两边单独看都通顺。按路径加载，副本的数量是零。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在 diff 里
表现为首行多一个看不见的字符，肉眼查不出来。

用法：python tools\port-subscription-help.py
"""

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP


def load(name, filename):
    """把一个 port 脚本当模块读进来，只为拿它已经写好的那一句。"""
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VIDEO = load("port_title_wrap_help", "port-title-wrap-help.py")
BACKDROP = load("port_watermark_help", "port-watermark-help.py")
LOOK = load("port_watermark_look_help", "port-watermark-look-help.py")

# 「视频」章：订阅之前免费到哪一步、付费点落在哪一处。
EXPORTING = {
    "en-US": "- Everything up to the last step is free: fetching data, playing the animation, "
             "saving a cover image. **Export** is the one place that asks for a monthly "
             "subscription, and pressing it says what that buys and what it costs. It renews "
             "until you cancel it in Microsoft Store.",

    "de": "- Alles bis zum letzten Schritt ist kostenlos: Daten laden, Animation abspielen, "
          "Titelbild speichern. **Exportieren** ist die eine Stelle, die ein monatliches "
          "Abonnement verlangt, und ein Klick darauf sagt, was das kauft und was es kostet. Es "
          "verlängert sich, bis Sie es im Microsoft Store kündigen.",

    "es": "- Todo hasta el último paso es gratis: descargar datos, reproducir la animación, "
          "guardar la portada. **Exportar** es el único sitio que pide una suscripción mensual, y "
          "al pulsarlo se dice qué compra y cuánto cuesta. Se renueva hasta que la canceles en "
          "Microsoft Store.",

    "fr": "- Tout est gratuit jusqu'à la dernière étape : charger les données, lire l'animation, "
          "enregistrer une image de couverture. **Exporter** est le seul endroit qui demande un "
          "abonnement mensuel, et un clic dit ce qu'il achète et ce qu'il coûte. Il se renouvelle "
          "jusqu'à ce que vous le résiliiez dans le Microsoft Store.",

    "it": "- Tutto fino all'ultimo passaggio è gratuito: scaricare i dati, riprodurre l'animazione, "
          "salvare l'immagine di copertina. **Esporta** è il solo punto che chiede un abbonamento "
          "mensile, e premendolo si legge cosa compra e quanto costa. Si rinnova finché non lo "
          "annulli nel Microsoft Store.",

    "pl": "- Wszystko aż do ostatniego kroku jest darmowe: pobieranie danych, odtwarzanie animacji, "
          "zapisanie okładki. **Eksport** to jedyne miejsce, które prosi o miesięczną subskrypcję; "
          "po kliknięciu wyjaśnia, co ona kupuje i ile kosztuje. Odnawia się, dopóki nie anulujesz "
          "jej w Microsoft Store.",

    "pt-BR": "- Tudo até o último passo é gratuito: buscar dados, reproduzir a animação, salvar a "
             "imagem de capa. **Exportar** é o único lugar que pede uma assinatura mensal, e ao "
             "tocá-lo ele diz o que compra e quanto custa. Ela renova até você cancelá-la na "
             "Microsoft Store.",

    "cs": "- Vše až do posledního kroku je zdarma: načtení dat, přehrání animace, uložení titulního "
          "obrázku. **Export** je jediné místo, které žádá měsíční předplatné, a po stisku vysvětlí, "
          "co kupuje a kolik stojí. Obnovuje se, dokud ho v Microsoft Storu nezrušíte.",

    "tr": "- Son adıma kadar her şey ücretsiz: veri çekmek, animasyonu oynatmak, kapak görselini "
          "kaydetmek. **Dışa aktar**, aylık abonelik isteyen tek yerdir; düğmeye basıldığında ne "
          "satın aldığı ve ne kadara mal olduğu söylenir. Microsoft Store'da iptal edene kadar "
          "yenilenir.",

    "ru": "- Всё до последнего шага бесплатно: загрузка данных, воспроизведение анимации, сохранение "
          "обложки. **Экспорт** — единственное место, которое просит ежемесячную подписку; при "
          "нажатии там сказано, что она покупает и сколько стоит. Она продлевается, пока вы не "
          "отмените её в Microsoft Store.",

    "ja": "- 最後の一歩までは無料です。データの取得、アニメーションの再生、カバー画像の保存はいずれも"
          "課金されません。月額サブスクリプションを求めるのは**書き出し**の一か所だけで、そこを押せば"
          "それが買うものと値段が書かれています。Microsoft Store で解約するまで更新されます。",

    "ko": "- 마지막 단계까지는 모두 무료입니다. 데이터 불러오기, 애니메이션 재생, 커버 이미지 저장에는 "
          "비용이 들지 않습니다. 월간 구독을 요구하는 곳은 **내보내기** 한 군데뿐이며, 누르면 그것이 "
          "무엇을 사는 것인지와 비용이 적혀 있습니다. Microsoft Store에서 해지할 때까지 갱신됩니다.",

    "zh-Hans": "- 最后一步之前全部免费：取数、播放动画、保存封面图都不收费。按月订阅只在**导出**"
               "这一处开口，点下去会说明它买下的是什么、要多少钱。它在 Microsoft Store 里按月续订，"
               "直到你在那里取消。",

    "zh-Hant": "- 最後一步之前全部免費：取數、播放動畫、儲存封面圖都不收費。按月訂閱只在**匯出**"
               "這一處開口，按下去會說明它買下的是什麼、要多少錢。它在 Microsoft Store 裡按月續訂，"
               "直到你在那裡取消。",
}

# 紧跟在水印那一条后面 —— 既有那条说「什么都不加就把开关关掉」，这一条说「那个开关搬不动了」。
SWITCH = {
    "en-US": "- Taking the mark off is one of the two things a subscription buys. Until one exists "
             "the switch stays on and cannot be moved — which is also exactly what every frame "
             "will carry, so the preview and the file never disagree.",

    "de": "- Das Wasserzeichen abzuschalten ist eines der beiden Dinge, die ein Abonnement kauft. "
          "Solange keines besteht, bleibt der Schalter an und lässt sich nicht bewegen — und genau "
          "das trägt dann auch jedes Bild, damit Vorschau und Datei niemals widersprechen.",

    "es": "- Quitar la marca de agua es una de las dos cosas que compra la suscripción. Mientras no "
          "la haya, el interruptor se queda encendido y no se puede mover — y eso es exactamente lo "
          "que llevará cada fotograma, así que la vista previa y el archivo nunca discrepan.",

    "fr": "- Retirer le filigrane est l'une des deux choses que l'abonnement achète. Tant qu'il n'y "
          "en a pas, l'interrupteur reste activé et ne peut pas être déplacé — et c'est exactement "
          "ce que portera chaque image, si bien que l'aperçu et le fichier ne se contredisent "
          "jamais.",

    "it": "- Togliere il marchio è una delle due cose che compra l'abbonamento. Finché non c'è, "
          "l'interruttore resta acceso e non si muove — ed è esattamente ciò che porterà ogni "
          "fotogramma, così anteprima e file non sono mai in disaccordo.",

    "pl": "- Zdjęcie znaku wodnego to jedna z dwóch rzeczy, które kupuje subskrypcja. Dopóki jej nie "
          "ma, przełącznik zostaje włączony i nie da się go ruszyć — i dokładnie to będzie nosić "
          "każda klatka, więc podgląd i plik nigdy się nie różnią.",

    "pt-BR": "- Tirar a marca d'água é uma das duas coisas que a assinatura compra. Enquanto não "
             "houver uma, o interruptor fica ligado e não se move — e é exatamente isso que cada "
             "quadro levará, então a prévia e o arquivo nunca discordam.",

    "cs": "- Odebrání vodoznaku je jedna ze dvou věcí, které předplatné kupuje. Dokud neexistuje, "
          "přepínač zůstává zapnutý a nejde s ním pohnout — a přesně to ponese každý snímek, takže "
          "se náhled a soubor nikdy nerozejdou.",

    "tr": "- Filigranı kaldırmak, aboneliğin satın aldığı iki şeyden biridir. Abonelik olmadığı "
          "sürece anahtar açık kalır ve oynatılamaz — ki bu, her karenin taşıdığı şeyle de aynıdır; "
          "önizleme ile dosya hiçbir zaman çelişmez.",

    "ru": "- Снятие водяного знака — одна из двух вещей, которые покупает подписка. Пока её нет, "
          "переключатель остаётся включённым и не двигается — и именно это будет нести каждый кадр, "
          "поэтому предпросмотр и файл никогда не расходятся.",

    "ja": "- ウォーターマークを外すのは、サブスクリプションで買う二つのもののうちひとつです。"
          "購入するまではスイッチはオンのまま動かず、それはそのまま各フレームが帯びるものでもあります。"
          "プレビューとファイルが食い違うことはありません。",

    "ko": "- 워터마크를 없애는 것은 구독이 구매하는 두 가지 중 하나입니다. 구독이 없으면 스위치는 켜진 "
          "채 움직일 수 없고, 그것은 그대로 모든 프레임이 담는 것이기도 합니다. 미리보기와 파일이 "
          "어긋나는 일은 없습니다.",

    "zh-Hans": "- 去掉水印是订阅买下的两件事之一。订阅之前，开关固定为开、搬不动——这也正是每一帧"
               "画面会带着的东西，所以预览与文件永远不会不一致。",

    "zh-Hant": "- 移除浮水印是訂閱買下的兩件事之一。訂閱之前，開關固定為開、搬不動——這也正是每一格"
               "畫面會帶著的東西，所以預覽與檔案永遠不會不一致。",
}

# 紧跟在「水印长什么样」那一条后面 —— 那一条写着「默认 10%、最高 40%」，而这句话说的正是
# 未订阅时那 10% 根本轮不上：浓度钉在上限，拨不动。
#
# **不改写那一条，而在它后面补一条。** 那一条对订阅者仍然句句属实（读过这一条再读它，语序也顺）；
# 把它改成「未订阅时 40%」则让一段话同时承担两拨读者。放在它后面等于先答「现在为什么是 40」，
# 再答「订阅后为什么是 10%」。
STRENGTH = {
    "en-US": "- **Until there is a subscription, that slider stays at 40%.** Turning the mark down "
             "goes with taking it off: an unsubscribed app writes every frame at full strength and "
             "the slider cannot be moved off it. The 10% above is where it starts once there is one.",

    "de": "- **Solange kein Abonnement besteht, bleibt dieser Regler bei 40 %.** Das Zeichen leiser "
          "zu stellen gehört zum Abschalten dazu: Eine nicht abonnierte App schreibt jedes Bild mit "
          "voller Stärke, und der Regler lässt sich nicht davon wegbewegen. Die 10 % oben sind der "
          "Wert, mit dem es beginnt, sobald eines besteht.",

    "es": "- **Hasta que haya suscripción, ese control se queda en el 40 %.** Bajar la intensidad va "
          "junto con quitar la marca: una app sin suscripción dibuja cada fotograma a plena "
          "intensidad y el control no se puede mover de ahí. El 10 % de arriba es el valor con el "
          "que empieza una vez que la hay.",

    "fr": "- **Tant qu'il n'y a pas d'abonnement, ce curseur reste à 40 %.** Baisser l'intensité va "
          "avec le retrait de la marque : une application non abonnée dessine chaque image à pleine "
          "intensité et le curseur ne peut pas en bouger. Les 10 % plus haut sont la valeur de "
          "départ une fois l'abonnement en place.",

    "it": "- **Finché non c'è un abbonamento, quella barra resta al 40%.** Abbassare l'intensità va "
          "insieme al togliere il segno: un'app senza abbonamento disegna ogni fotogramma alla "
          "massima intensità e la barra non si può spostare. Il 10% qui sopra è il valore da cui "
          "parte una volta che c'è.",

    "pl": "- **Dopóki nie ma subskrypcji, ten suwak zostaje na 40%.** Przyciszenie znaku idzie w "
          "parze z jego zdjęciem: aplikacja bez subskrypcji rysuje każdą klatkę z pełną mocą, a "
          "suwaka nie da się z tego miejsca ruszyć. Powyższe 10% to wartość, od której zaczyna się, "
          "gdy subskrypcja już jest.",

    "pt-BR": "- **Enquanto não houver assinatura, essa barra fica em 40%.** Baixar a intensidade vai "
             "junto com remover a marca: um app sem assinatura desenha cada quadro com intensidade "
             "máxima e a barra não sai daí. Os 10% acima são o valor com que ela começa quando houver "
             "uma.",

    "cs": "- **Dokud neexistuje předplatné, tento posuvník zůstává na 40 %.** Ztlumení značky patří "
          "k jejímu odebrání: aplikace bez předplatného kreslí každý snímek plnou silou a z této "
          "hodnoty posuvník nejde pohnout. Uvedených 10 % je hodnota, od které začíná, jakmile "
          "předplatné existuje.",

    "tr": "- **Abonelik olmadığı sürece bu kaydırıcı %40'ta kalır.** İşareti kısmak, onu kaldırmakla "
          "birlikte gelir: aboneliksiz uygulama her kareyi tam yoğunlukta çizer ve kaydırıcı oradan "
          "oynatılamaz. Yukarıdaki %10, bir abonelik olduğunda işin başlayacağı değerdir.",

    "ru": "- **Пока подписки нет, этот ползунок остаётся на 40 %.** Сделать знак тише — то же, что "
          "снять его: приложение без подписки рисует каждый кадр с полной насыщенностью, и сдвинуть "
          "ползунок нельзя. Указанные выше 10 % — значение, с которого он начинается, когда подписка "
          "появится.",

    "ja": "- **購読があるまで、このスライダーは 40% のままです。** 透かしを薄くするのは外すのと"
          "同じ扱いで、購読前のアプリは各フレームを常に最大の濃さで描き、スライダーはそこから"
          "動かせません。上の 10% は、購読したときに出発点となる値です。",

    "ko": "- **구독이 있을 때까지 이 슬라이더는 40%에 머뭅니다.** 워터마크를 옅게 하는 것은 없애는 "
          "것과 같은 취급이어서, 구독 전의 앱은 모든 프레임을 가장 진하게 그리고 슬라이더는 그 자리에서 "
          "움직이지 않습니다. 위의 10%는 구독했을 때 시작하는 값입니다.",

    "zh-Hans": "- **没有订阅的时候，这个滑块停在 40%。** 把水印调淡和去掉水印是同一件事的两面：未"
               "订阅时每一帧都按最高浓度写出去，滑块也就停在那儿挪不动；上面那句「默认 10%」说的是"
               "订阅之后它从哪儿起步。",

    "zh-Hant": "- **沒有訂閱的時候，這個滑桿停在 40%。** 把浮水印調淡和移除浮水印是同一件事的兩面："
               "未訂閱時每一格畫面都按最高濃度寫出去，滑桿也就停在那裡挪不動；上面那句「預設 10%」"
               "說的是訂閱之後它從哪裡起步。",
}


def lines_of(tag):
    path = ROOT / f"help-{tag}.md"
    raw = path.read_bytes()
    lines = raw.decode("utf-8-sig").lstrip("\ufeff").replace("\r\n", "\n").split("\n")
    return path, raw, lines


def bounds(lines, heading=None, index=None):
    """某一章的正文范围。给标题文本就按标题认（要求恰好命中一章）；给序号就按序号认。"""
    heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

    if heading is not None:
        found = [i for i, line in enumerate(lines) if line.strip() == heading]
        assert len(found) == 1, f"{heading}: matched {len(found)} chapters, expected one"
        start = found[0]
    else:
        assert 0 <= index < len(heads), f"chapter {index} is not in a manual of {len(heads)}"
        start = heads[index]

    after = [i for i in heads if i > start]

    return start, (after[0] if after else len(lines))


def insert(tag, body, heading=None, index=None, anchor=None):
    """把一条 `- ` 插进某一章。`anchor` 给出时紧贴在那一句之后，否则贴在章末最后一条之后。"""
    path, raw, lines = lines_of(tag)

    if any(line.strip() == body.strip() for line in lines):
        return False

    start, end = bounds(lines, heading=heading, index=index)

    if anchor is not None:
        at = [i for i in range(start, end) if lines[i].strip() == anchor[tag].strip()]
        assert len(at) == 1, f"{tag}: the anchor sentence matched {len(at)} lines"
        at = at[0] + 1
    else:
        bullets = [i for i in range(start, end) if lines[i].startswith("- ")]
        assert bullets, f"{tag}: that chapter holds no bullets"
        at = bullets[-1] + 1

    lines[at:at] = ["", body]

    rebuilt = "\n".join(lines)

    if b"\r\n" in raw:
        rebuilt = rebuilt.replace("\n", "\r\n")

    path.write_bytes((b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"")
                     + rebuilt.encode("utf-8"))

    return True


def main() -> int:
    for tag in lt.LANGS:
        video = insert(tag, EXPORTING[tag], heading=VIDEO.HEADING[tag])
        backdrop = insert(tag, SWITCH[tag], anchor=BACKDROP.WATERMARK, index=BACKDROP.CHAPTER)
        strength = insert(tag, STRENGTH[tag], anchor=LOOK.LOOK, index=LOOK.CHAPTER)

        print("%-9s %s / %s / %s" % (tag,
                                     "video +1" if video else "already there",
                                     "backdrop +1" if backdrop else "already there",
                                     "strength +1" if strength else "already there"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
