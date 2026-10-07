# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.10.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是市值历程那一页。
它说的没错，但那件事已经上架；接着往后加，这一栏就成了两件事各说一半。

本版不是一个新页面，是一次**修复**。要说的一件事：**订阅买下就当场生效，不用重启；已有订阅时
那张写着续订日期、能管理与恢复订阅的卡片不再消失。**

上一版脚本的文档头写着「不谈订阅，那件事上一版说完了」。这回又谈订阅，是因为这就是本版的内容，
而且用户真会撞上：买完之后要重启才生效，或者重启后卡片不见了。商店这一栏写的是「这个版本有什么
不同」，而用户能感知到的不同就是这两条 —— 修复写在这里不是降格。

**不提实现方式。** 读本机许可证还是查商店目录、中间抛的是哪一种异常，那是代码的事；用户看到的
只是「要不要重启」和「卡片在不在」。把内部那条出错的路径写进商店文案，等于让用户替我们查错。

**重音字母照写。** 德语的 ü/ä、法语的 é/ç、捷克的 ř/ž、波兰语的 ł/ż、土耳其语的 ğ/ı 是这个字
的一部分，不是装饰；为了「保险」把它们写成 u/a/e/c/r/z/l/g/i 等于在商店里挂一句拼错的德语。
文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

**脚本名由 manifest 的版本号算出 `10100`，不是取巧写成 `1100`。** `verify-docs.py` 把四段版本
号**全拼**当作文件名（`1.0.10.0` → 四段拼起来是 `10100`，第三段进位之后就是这样），算不出/找不到
就大声失败。写成 1100 会让它通过不了，而那正是它存在的理由。

用法：python tools\\port-store-listing-10100.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。一句话远够不着，但每次换文案都要算一遍最长的那一种语言 —— 上限是
# 按字符算的，德/法/意语一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**订阅买下就当场生效，不用重启；已有订阅时那张写着续订
# 日期、能管理或恢复订阅的卡片不再消失。两个症状同一个错——答案本该读本机的许可证，却去问
# 联网才拿得到的商店目录；改成读本机之后都不会再发生。**
NEWS = {
    "zh-Hans":
        "本版修正订阅状态：买下之后当场生效，不必重启应用；已有订阅时，设置页那张写着续订日期、"
        "可以管理或恢复订阅的卡片也不会再消失。两个症状出自同一个错：「这个人买没买」本该读本机"
        "已经拿到的许可证，却跑去问商店的商品目录——那是要联网才拿得到的东西。改成读本机之后，"
        "两者都不会再发生；购买之后稍等一下再看一遍，也补上了商店记下付款到下发许可证之间的"
        "那一小段间隔。",
    "zh-Hant":
        "本版修正訂閱狀態：買下之後當場生效，不必重新啟動應用程式；已有訂閱時，設定頁那張寫著續訂"
        "日期、可以管理或恢復訂閱的卡片也不會再消失。兩個症狀出自同一個錯：「這個人買了沒」本該讀"
        "本機已經拿到的授權，卻跑去問商店的商品目錄——那是要連網才拿得到的東西。改成讀本機之後，"
        "兩者都不會再發生；購買之後稍等一下再看一遍，也補上了商店記下付款到核發授權之間的那一小段"
        "間隔。",
    "en-US":
        "New in this version: a subscription takes effect the moment it is bought - no restarting the "
        "app - and once you have one, the card in Settings that shows its renewal date and lets you "
        "manage or restore it no longer disappears. Both symptoms came from one mistake: the answer "
        "to \"has this person paid\" was taken from the Store's catalogue, which has to be fetched, "
        "when the licence was already on this machine and could simply be read there. It is read "
        "locally now, and neither can happen. A short wait and a second look after the purchase also "
        "cover the gap between the Store recording a payment and granting the licence.",
    "ja":
        "今バージョンでは購読の扱いを修正しました。購入した瞬間に反映され、アプリの再起動は要り"
        "ません。また、購読中の場合に設定画面のカード——更新日を示し、購読の管理や復元を行うもの"
        "——が消えてしまうこともなくなりました。二つの症状は同じ間違いから来ています。「その人が"
        "支払ったか」という答えを、すでにこの端末にあるライセンスからではなく、取得に通信が必要な"
        "ストアのカタログから得ていました。今はローカルのライセンスを読むため、どちらも起こり"
        "ません。購入後に少し待ってからもう一度確認することで、ストアが支払いを記録してから"
        "ライセンスを付与するまでのわずかな開きも埋めます。",
    "ko":
        "이 버전에서는 구독 상태를 고쳤습니다. 결제하면 즉시 적용되어 앱을 다시 시작할 필요가 없고, "
        "구독 중이라면 갱신일을 보여 주고 구독을 관리하거나 복원하는 설정의 카드가 사라지지도 "
        "않습니다. 두 증상은 같은 실수에서 왔습니다. 「이 사람이 결제했는가」라는 답을 이미 이 기기에 "
        "들어 있는 라이선스에서 읽지 않고, 내려받아야 하는 스토어 카탈로그에서 가져왔습니다. 이제는 "
        "로컬 라이선스를 읽으므로 두 가지 모두 일어나지 않으며, 결제 후 잠시 기다렸다 한 번 더 "
        "확인하여 스토어가 결제를 기록한 뒤 라이선스를 내려주는 사이의 짧은 간격도 메웁니다.",
    "de":
        "Neu in dieser Version: Ein Abonnement gilt ab dem Moment des Kaufs - die App muss nicht neu "
        "gestartet werden -, und wer eines hat, für den bleibt die Karte in den Einstellungen "
        "erhalten, die das Verlängerungsdatum zeigt und das Verwalten oder Wiederherstellen erlaubt. "
        "Beide Fehler kamen aus derselben Verwechslung: Die Antwort auf \"hat diese Person bezahlt\" "
        "wurde aus dem Katalog des Stores geholt, der erst geladen werden muss, obwohl die Lizenz "
        "längst auf diesem Gerät liegt und sich dort lesen lässt. Sie wird nun dort gelesen, und "
        "beides ist unmöglich geworden. Ein kurzes Warten und ein zweiter Blick nach dem Kauf "
        "überbrückt auch die Spanne zwischen dem Verbuchen der Zahlung im Store und dem Erteilen der "
        "Lizenz.",
    "fr":
        "Nouveau dans cette version : l'abonnement prend effet dès l'achat, sans relancer "
        "l'application, et une fois abonné, la carte des paramètres qui affiche la date de "
        "renouvellement et permet de gérer ou de restaurer l'abonnement ne disparaît plus. Les deux "
        "symptômes venaient de la même erreur : la réponse à « cette personne a-t-elle payé » était "
        "cherchée dans le catalogue du Store, qu'il faut télécharger, alors que la licence est déjà "
        "sur la machine et peut y être lue. Elle est désormais lue localement, et ni l'un ni l'autre "
        "ne peut plus arriver. Une courte attente puis un second contrôle après l'achat comblent "
        "aussi l'écart entre l'enregistrement du paiement par le Store et l'octroi de la licence.",
    "it":
        "Novità di questa versione: l'abbonamento vale dal momento dell'acquisto, senza riavviare "
        "l'app, e una volta attivo la scheda delle impostazioni che mostra la data di rinnovo e "
        "permette di gestire o ripristinare l'abbonamento non scompare più. Entrambi i sintomi "
        "venivano dallo stesso errore: la risposta a \"questa persona ha pagato\" era presa dal "
        "catalogo dello Store, che va scaricato, mentre la licenza è già sul dispositivo e si può "
        "leggere lì. Ora si legge in locale e nessuno dei due può più accadere. Una breve attesa e un "
        "secondo controllo dopo l'acquisto coprono anche l'intervallo fra la registrazione del "
        "pagamento nello Store e la concessione della licenza.",
    "es":
        "Novedad de esta versión: la suscripción surte efecto en el momento de la compra, sin "
        "reiniciar la aplicación, y una vez suscrito la tarjeta de ajustes que muestra la fecha de "
        "renovación y permite gestionar o restaurar la suscripción ya no desaparece. Ambos síntomas "
        "venían del mismo error: la respuesta a «¿esta persona ha pagado?» se tomaba del catálogo de "
        "la Store, que hay que descargar, cuando la licencia ya está en el equipo y puede leerse "
        "allí. Ahora se lee en local y ninguno de los dos puede ocurrir. Una breve espera y una "
        "segunda comprobación tras la compra cubren también el intervalo entre el registro del pago "
        "en la Store y la concesión de la licencia.",
    "pt-BR":
        "Novo nesta versão: a assinatura passa a valer no momento da compra, sem reiniciar o "
        "aplicativo, e, depois de assinante, o cartão de configurações que mostra a data de renovação "
        "e permite gerenciar ou restaurar a assinatura não desaparece mais. Os dois sintomas vinham "
        "do mesmo erro: a resposta para \"esta pessoa pagou\" era buscada no catálogo da Store, que "
        "precisa ser baixado, quando a licença já está na máquina e pode ser lida ali. Agora ela é "
        "lida localmente e nenhum dos dois pode acontecer. Uma breve espera e uma segunda verificação "
        "depois da compra cobrem também o intervalo entre o registro do pagamento pela Store e a "
        "concessão da licença.",
    "pl":
        "Nowość w tej wersji: subskrypcja działa od razu po zakupie, bez ponownego uruchamiania "
        "aplikacji, a gdy już jest, karta w ustawieniach pokazująca datę odnowienia i pozwalająca "
        "zarządzać subskrypcją lub ją przywrócić nie znika. Oba objawy brały się z tego samego błędu: "
        "odpowiedź na pytanie „czy ta osoba zapłaciła” brano z katalogu sklepu, który trzeba pobrać, "
        "choć licencja jest już na tym urządzeniu i można ją tam odczytać. Teraz jest odczytywana "
        "lokalnie i żaden z nich nie może się zdarzyć. Krótkie oczekiwanie i ponowne sprawdzenie po "
        "zakupie pokrywają też odstęp między zarejestrowaniem płatności przez sklep a przyznaniem "
        "licencji.",
    "cs":
        "Novinkou této verze je oprava předplatného: platí ihned po zakoupení, bez restartu aplikace, "
        "a když je aktivní, karta v nastavení, která ukazuje datum obnovení a umožňuje předplatné "
        "spravovat nebo obnovit, nezmizí. Oba příznaky pramenily ze stejné chyby: odpověď na otázku "
        "„zaplatil tento člověk” se brala z katalogu obchodu, který je třeba stáhnout, přestože "
        "licence je už v tomto zařízení a lze ji tam přečíst. Nyní se čte místně a ani jedno se "
        "nemůže stát. Krátké čekání a druhý pohled po nákupu pokrývají i mezeru mezi zaznamenáním "
        "platby v obchodě a udělením licence.",
    "ru":
        "Новое в этой версии: подписка начинает действовать сразу после покупки, без перезапуска "
        "приложения, а когда она есть, карточка в настройках, показывающая дату продления и "
        "позволяющая управлять подпиской или восстановить её, больше не исчезает. Оба симптома шли "
        "из одной ошибки: ответ на вопрос «этот человек заплатил» брали из каталога магазина, "
        "который нужно загружать, хотя лицензия уже лежит на этом устройстве и читается там. Теперь "
        "она читается локально, и ни то ни другое произойти не может. Небольшая пауза и повторная "
        "проверка после покупки закрывают и промежуток между тем, как магазин записал платёж, и тем, "
        "как выдал лицензию.",
    "tr":
        "Bu sürümde abonelik düzeltildi: satın aldığınız anda geçerli olur, uygulamayı yeniden "
        "başlatmanız gerekmez; aboneliğiniz varken ayarlardaki, yenileme tarihini gösteren ve "
        "aboneliği yönetmenizi ya da geri yüklemenizi sağlayan kart da kaybolmaz. İki belirti de "
        "aynı hatadan geliyordu: «bu kişi ödeme yaptı mı» sorusunun yanıtı, bu cihazda zaten duran ve "
        "burada okunabilen lisans yerine, indirilmesi gereken mağaza kataloğunda aranıyordu. Artık "
        "yerelde okunuyor ve ikisi de gerçekleşemez. Satın almadan sonra kısa bir bekleme ve ikinci "
        "bir bakış, mağazanın ödemeyi kaydetmesiyle lisansı vermesi arasındaki kısa aralığı da "
        "kapatıyor.",
}


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # 各文件保持自己的行尾：store-listing.md 是 CRLF。
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    if sorted(NEWS) != sorted(LANGS):
        print("× 文案漏了语言：%s" % sorted(set(LANGS) - set(NEWS)))
        return 1

    changed = 0

    for n, lang in enumerate(LANGS):
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            print(f"× {lang}: 只数到 {len(subs)} 个小标题")
            return 1

        at = subs[1] + 1       # 「此版本的新增功能」下面的正文

        while at < end and not lines[at].strip():
            at += 1

        text = NEWS[lang]

        if lines[at] == text:
            print(f"· {lang}: （已是本版，{len(text)} 字）")
            continue

        lines[at] = text
        changed += 1
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: 「{lines[subs[1]][4:]}」改写（{len(text)} 字）")

    if changed:
        LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))

    longest = max((len(NEWS[l]), l) for l in LANGS)
    over = [(l, len(NEWS[l])) for l in LANGS if len(NEWS[l]) > LIMIT]

    if over:
        print(f"\n！超过商店 {LIMIT} 字上限：{over}")
        return 1

    print(f"\n最长的 {longest[1]} {longest[0]} 字，都在 {LIMIT} 以内")
    print(f"改了 {changed} 条（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
