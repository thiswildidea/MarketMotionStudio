# -*- coding: utf-8 -*-
r"""注入「订阅」这一套界面文案，14 语言。

**为什么这些句子只能有一处写。** 订阅买下的是两件事——导出视频、去掉水印——而这两件事在
三处被讲述：界面（resw）、手册（help-*.md）、商店（store-listing.md）。三处各手写一遍的下场
是「两边都通顺、讲的却是两种意思」，而且两边单独看都发现不了。所以这里只写一种，商店与
手册各自按路径来取。

**为什么写给界面看的这部分非要手写不可。** 商店与手册那两句各自按路径从这里 upstream 取走，`port-subscription-help.py`
与 `port-store-listing-1060.py` 都不再写第二套 —— 三处只剩这一处是人要写的，写一次就够了。

**这个脚本只写那 16 个键，一个字都不碰别处。** 第一版它还顺手改了
`SettingsWatermarkHint.Text`（那句「关掉则画面上什么都不加」现在要说明订阅），但那**不是它的键**：
`port-watermark-resw.py` 每次运行都会把这个键整行重写回它自己那份话，于是两个脚本抢一个键、
谁最后跑谁赢 —— 而失败的样子是「那句话悄悄变回旧的语法」，两边单独看都通顺。所以那句话改在
**键的主人那里**（`port-watermark-resw.py` 的 `HINT`），这里只留这一条注释说明为什么不在。

**它只做一件事**：

1. **新增 16 个键**（设置页订阅卡片、订阅对话框、状态行、还有水印开关下面那句「为什么搬不动」）。
   键不存在就插在 `</root>` 前；已存在就替换值 —— 幂等，可以随时复跑修正某一句。

写回**照原样**：resw 是 LF 且**必须带 BOM**。

用法：python tools\port-subscription-resw.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

# 每个键在各语言里的一段話。写的时候按这一顺序排布，缺一个语言就 assert 而不是留空。
KEYS = [
    "SettingsSubscriptionLabel.Text",
    "SettingsSubscriptionNote.Text",
    "SettingsSubscriptionActive",
    "SettingsSubscriptionInactive",
    "SettingsSubscriptionRenews",
    "SettingsSubscriptionPrice",
    "SettingsSubscriptionUnavailable",
    "SettingsSubscriptionFailed",
    "SettingsSubscriptionRestoreMissing",
    "SettingsWatermarkLockedNote.Text",
    "SubscriptionSubscribe.Content",
    "SubscriptionRestore.Content",
    "SubscriptionManage.Content",
    "SubscriptionOfferTitle",
    "SubscriptionOfferBody",
    "SubscriptionPerMonth",
]

# 顺序与 KEYS 一致。占位符 {0} 必须对得上 —— 少一个是 FormatException，多一个是白写的钱。
TEXT = {
    "en-US": [
        "Subscription",
        "Everything on screen stays free: fetching data, playing the animation, saving a cover image. Writing the video — and taking the watermark off it — takes a monthly subscription, which can be cancelled at any time.",
        "Subscribed",
        "Not subscribed",
        "Renews on {0}",
        "{0} a month",
        "The subscription could not be reached, so there is nothing here to buy just now. Check that Microsoft Store is signed in and try again.",
        "The Store reported the purchase as done without granting it. Nothing is unlocked until the licence agrees — try again in a moment.",
        "No subscription was found under this Microsoft account. If it was bought with a different one, sign in with that account and restore again.",
        "Until you subscribe, every frame carries the watermark and at full strength. This page draws the frames exactly as they are written, so what you see here is what a video will contain.",
        "Subscribe",
        "Restore purchase",
        "Manage subscription",
        "Exporting a video takes a subscription",
        "Every page here fetches its data, plays its animation and saves its cover image without paying — all of that stays free. Writing the video is what the subscription buys, along with taking the watermark off it.",
        "{0} a month, cancelled any time.",
    ],
    "de": [
        "Abonnement",
        "Alles auf dem Bildschirm bleibt kostenlos: Daten laden, Animation abspielen, Titelbild speichern. Das Video zu schreiben — und das Wasserzeichen zu entfernen — verlangt ein monatliches Abonnement, das jederzeit kündbar ist.",
        "Abonniert",
        "Nicht abonniert",
        "Verlängert sich am {0}",
        "{0} pro Monat",
        "Das Abonnement war nicht erreichbar, es gibt hier also gerade nichts zu kaufen. Prüfen Sie, ob der Microsoft Store angemeldet ist, und versuchen Sie es erneut.",
        "Der Store meldete den Kauf als abgeschlossen, ohne ihn zu gewähren. Nichts wird freigeschaltet, solange die Lizenz nicht zustimmt — versuchen Sie es in einem Moment erneut.",
        "Unter diesem Microsoft-Konto wurde kein Abonnement gefunden. Wurde es mit einem anderen gekauft, melden Sie sich mit jenem Konto an und stellen Sie es erneut wieder her.",
        "Bis Sie abonnieren, trägt jedes Bild das Wasserzeichen, und zwar mit voller Stärke. Diese Seite zeichnet die Bilder genau so, wie sie geschrieben werden: Was Sie hier sehen, enthält auch ein Video.",
        "Abonnieren",
        "Kauf wiederherstellen",
        "Abonnement verwalten",
        "Ein Video zu exportieren verlangt ein Abonnement",
        "Jede Seite hier lädt ihre Daten, spielt ihre Animation und speichert ihr Titelbild, ohne dass jemand zahlt — all das bleibt kostenlos. Das Video zu schreiben ist es, was das Abonnement kauft, zusammen mit dem Entfernen des Wasserzeichens.",
        "{0} pro Monat, jederzeit kündbar.",
    ],
    "es": [
        "Suscripción",
        "Todo lo que ves en pantalla sigue siendo gratis: descargar datos, reproducir la animación, guardar la portada. Escribir el vídeo — y quitarle la marca de agua — requiere una suscripción mensual que puedes cancelar cuando quieras.",
        "Suscrito",
        "Sin suscripción",
        "Se renueva el {0}",
        "{0} al mes",
        "No se pudo alcanzar la suscripción, así que aquí no hay nada que comprar por ahora. Comprueba que Microsoft Store haya iniciado sesión y vuelve a intentarlo.",
        "La Store informó de la compra como realizada sin concederla. Nada se desbloquea hasta que la licencia lo confirme: inténtalo de nuevo en un momento.",
        "No se encontró ninguna suscripción en esta cuenta Microsoft. Si se compró con otra, inicia sesión con esa cuenta y restaura de nuevo.",
        "Hasta que te suscribas, cada fotograma lleva la marca de agua y con toda su intensidad. Esta página dibuja los fotogramas tal y como se escriben: lo que ves aquí es lo que contendrá el vídeo.",
        "Suscribirse",
        "Restaurar compra",
        "Gestionar suscripción",
        "Exportar un vídeo requiere suscripción",
        "Todas las páginas descargan sus datos, reproducen su animación y guardan su portada sin cobrar nada: todo eso sigue siendo gratis. Escribir el vídeo es lo que compra la suscripción, junto con quitar la marca de agua.",
        "{0} al mes, cancela cuando quieras.",
    ],
    "fr": [
        "Abonnement",
        "Tout ce qui s'affiche reste gratuit : charger les données, lire l'animation, enregistrer une image de couverture. Écrire la vidéo — et retirer le filigrane — demande un abonnement mensuel, résiliable à tout moment.",
        "Abonné",
        "Non abonné",
        "Se renouvelle le {0}",
        "{0} par mois",
        "L'abonnement n'a pas pu être atteint : il n'y a donc rien à acheter ici pour l'instant. Vérifiez que le Microsoft Store est connecté et réessayez.",
        "Le Store a signalé l'achat comme effectué sans l'accorder. Rien ne se débloque tant que la licence n'est pas d'accord — réessayez dans un instant.",
        "Aucun abonnement n'a été trouvé sous ce compte Microsoft. S'il a été acheté avec un autre, connectez-vous avec celui-ci et restaurez à nouveau.",
        "Jusqu'à votre abonnement, chaque image porte le filigrane, et à pleine intensité. Cette page dessine les images exactement comme elles seront écrites : ce que vous voyez ici est ce que contiendra une vidéo.",
        "S'abonner",
        "Restaurer l'achat",
        "Gérer l'abonnement",
        "Exporter une vidéo demande un abonnement",
        "Chaque page ici charge ses données, lit son animation et enregistre son image de couverture sans rien payer — tout cela reste gratuit. Écrire la vidéo est ce que l'abonnement achète, avec le retrait du filigrane.",
        "{0} par mois, résiliable à tout moment.",
    ],
    "it": [
        "Abbonamento",
        "Tutto ciò che vedi resta gratuito: scaricare i dati, riprodurre l'animazione, salvare l'immagine di copertina. Scrivere il video — e togliere il marchio — richiede un abbonamento mensile, annullabile in qualsiasi momento.",
        "Abbonato",
        "Non abbonato",
        "Si rinnova il {0}",
        "{0} al mese",
        "Non è stato possibile raggiungere l'abbonamento, quindi qui non c'è nulla da acquistare per ora. Controlla che il Microsoft Store sia connesso e riprova.",
        "Lo Store ha segnalato l'acquisto come riuscito senza concederlo. Nulla si sblocca finché la licenza non concorda — riprova tra un attimo.",
        "Nessun abbonamento trovato sotto questo account Microsoft. Se è stato acquistato con un altro, accedi con quell'account e ripristina di nuovo.",
        "Finché non ti abboni, ogni fotogramma porta il marchio, e alla massima intensità. Questa pagina disegna i fotogrammi esattamente come verranno scritti: ciò che vedi qui è ciò che conterrà un video.",
        "Abbonati",
        "Ripristina l'acquisto",
        "Gestisci l'abbonamento",
        "Esportare un video richiede un abbonamento",
        "Ogni pagina qui scarica i propri dati, riproduce la propria animazione e salva la propria copertina senza far pagare nulla — tutto questo resta gratuito. Scrivere il video è ciò che compra l'abbonamento, insieme al togliere il marchio.",
        "{0} al mese, annullabile in qualsiasi momento.",
    ],
    "pl": [
        "Subskrypcja",
        "Wszystko na ekranie pozostaje darmowe: pobieranie danych, odtwarzanie animacji, zapisanie okładki. Zapisanie filmu — i zdjęcie znaku wodnego — wymaga miesięcznej subskrypcji, którą można anulować w każdej chwili.",
        "Subskrypcja aktywna",
        "Brak subskrypcji",
        "Odnawia się {0}",
        "{0} miesięcznie",
        "Nie udało się połączyć z subskrypcją, więc nie ma tu teraz nic do kupienia. Sprawdź, czy Microsoft Store jest zalogowany, i spróbuj ponownie.",
        "Sklep zgłosił zakup jako dokonany, ale nie przyznał go. Nic nie zostanie odblokowane, dopóki licencja się nie zgodzi — spróbuj ponownie za chwilę.",
        "Nie znaleziono subskrypcji na tym koncie Microsoft. Jeśli kupiono ją na inne konto, zaloguj się tam i przywróć ponownie.",
        "Dopóki nie wykupisz subskrypcji, każda klatka nosi znak wodny, i to w pełnym natężeniu. Ta strona rysuje klatki dokładnie tak, jak zostaną zapisane: to, co tu widzisz, znajdzie się w filmie.",
        "Subskrybuj",
        "Przywróć zakup",
        "Zarządzaj subskrypcją",
        "Eksport filmu wymaga subskrypcji",
        "Każda strona tu pobiera dane, odtwarza animację i zapisuje okładkę bez żadnej opłaty — to pozostaje darmowe. Zapisanie filmu jest tym, co kupuje subskrypcja, wraz ze zdjęciem znaku wodnego.",
        "{0} miesięcznie, anulujesz w każdej chwili.",
    ],
    "pt-BR": [
        "Assinatura",
        "Tudo o que aparece na tela continua gratuito: buscar dados, reproduzir a animação, salvar a imagem de capa. Gravar o vídeo — e tirar a marca d'água — exige uma assinatura mensal, que pode ser cancelada a qualquer momento.",
        "Assinante",
        "Sem assinatura",
        "Renova em {0}",
        "{0} por mês",
        "Não foi possível alcançar a assinatura, então não há nada para comprar aqui agora. Verifique se a Microsoft Store está conectada e tente novamente.",
        "A Store informou a compra como concluída sem concedê-la. Nada é liberado até que a licença concorde — tente novamente em instantes.",
        "Nenhuma assinatura foi encontrada nesta conta Microsoft. Se foi comprada em outra, entre com aquela conta e restaure novamente.",
        "Até você assinar, cada quadro leva a marca d'água, e na intensidade máxima. Esta página desenha os quadros exatamente como serão gravados: o que você vê aqui é o que um vídeo conterá.",
        "Assinar",
        "Restaurar compra",
        "Gerenciar assinatura",
        "Exportar um vídeo exige assinatura",
        "Todas as páginas buscam seus dados, reproduzem sua animação e salvam sua imagem de capa sem cobrar nada — tudo isso continua gratuito. Gravar o vídeo é o que a assinatura compra, junto com tirar a marca d'água.",
        "{0} por mês, cancele quando quiser.",
    ],
    "cs": [
        "Předplatné",
        "Vše na obrazovce zůstává zdarma: načtení dat, přehrání animace, uložení titulního obrázku. Zápis videa — a odebrání vodoznaku — vyžaduje měsíční předplatné, které lze kdykoli zrušit.",
        "Předplaceno",
        "Bez předplatného",
        "Obnovuje se {0}",
        "{0} měsíčně",
        "Předplatné nebylo možné dosáhnout, takže tu teď není co koupit. Zkontrolujte, že je Microsoft Store přihlášen, a zkuste to znovu.",
        "Store nahlásil nákup jako provedený, aniž by ho udělil. Nic se neodemkne, dokud licence nesouhlasí — zkuste to za chvíli znovu.",
        "Pod tímto účtem Microsoft nebylo nalezeno žádné předplatné. Pokud bylo koupeno na jiný účet, přihlaste se k němu a obnovte znovu.",
        "Dokud si předplatné nepořídíte, nese každý snímek vodoznak, a to v plné síle. Tato stránka kreslí snímky přesně tak, jak budou zapsány: co vidíte tady, to bude obsahovat i video.",
        "Předplatit",
        "Obnovit nákup",
        "Spravovat předplatné",
        "Export videa vyžaduje předplatné",
        "Každá stránka tu načte svá data, přehraje animaci a uloží titulní obrázek bez placení — to vše zůstává zdarma. Zápis videa je tím, co předplatné kupuje, spolu s odebráním vodoznaku.",
        "{0} měsíčně, lze kdykoli zrušit.",
    ],
    "tr": [
        "Abonelik",
        "Ekrandaki her şey ücretsiz kalır: veri çekmek, animasyonu oynatmak, kapak görselini kaydetmek. Videoyu yazmak — ve filigranı kaldırmak — her zaman iptal edilebilen aylık bir abonelik gerektirir.",
        "Abone",
        "Abone değil",
        "{0} tarihinde yenilenir",
        "Aylık {0}",
        "Aboneliğe ulaşılamadı, bu yüzden şu an burada satın alınacak bir şey yok. Microsoft Store'un oturum açtığını kontrol edip yeniden deneyin.",
        "Store, satın almayı tanımadığı halde tamamlandı olarak bildirdi. Lisans onaylamadıkça hiçbir şey açılmaz — birazdan yeniden deneyin.",
        "Bu Microsoft hesabında abonelik bulunamadı. Başka bir hesapla satın alındıysa o hesapla oturum açıp yeniden geri yükleyin.",
        "Abonelik başlayana kadar her kare filigranı taşır ve yoğunluk da en yüksek değerde kalır. Bu sayfa kareleri tam olarak yazıldıkları gibi çizer: burada gördüğünüz şey videonun içereceği şeydir.",
        "Abone ol",
        "Satın almayı geri yükle",
        "Aboneliği yönet",
        "Video dışa aktarmak abonelik gerektirir",
        "Buradaki her sayfa verisini çeker, animasyonunu oynatır ve kapak görselini ücret almadan kaydeder — hepsi ücretsiz kalır. Aboneliğin satın aldığı şey videoyu yazmaktır, filigranı kaldırmakla birlikte.",
        "Aylık {0}, dilediğiniz zaman iptal edin.",
    ],
    "ru": [
        "Подписка",
        "Всё на экране остаётся бесплатным: загрузка данных, воспроизведение анимации, сохранение обложки. Запись видео — и снятие водяного знака — требуют ежемесячной подписки, которую можно отменить в любой момент.",
        "Подписка активна",
        "Нет подписки",
        "Продление: {0}",
        "{0} в месяц",
        "До подписки не удалось достучаться, поэтому здесь сейчас нечего покупать. Проверьте, что в Microsoft Store выполнен вход, и попробуйте снова.",
        "Store сообщил, что покупка выполнена, но не предоставил её. Ничто не откроется, пока лицензия не подтвердит это — попробуйте через минуту снова.",
        "Под этой учётной записью Microsoft подписка не найдена. Если она куплена на другую, войдите в неё и восстановите снова.",
        "Пока вы не оформите подписку, каждый кадр несёт водяной знак, причём максимальной плотности. Эта страница рисует кадры ровно так, как они будут записаны: что вы видите здесь, то и будет в видео.",
        "Подписаться",
        "Восстановить покупку",
        "Управлять подпиской",
        "Экспорт видео требует подписки",
        "Каждая страница здесь загружает данные, проигрывает анимацию и сохраняет обложку без оплаты — всё это остаётся бесплатным. Подписка покупает запись видео и вместе с ней снятие водяного знака.",
        "{0} в месяц, отмена в любой момент.",
    ],
    "ja": [
        "サブスクリプション",
        "画面に表示されるものはすべて無料のままです。データの取得、アニメーションの再生、カバー画像の保存までは課金されません。動画の書き出し——そしてウォーターマークの解除——には、いつでも解約できる月額サブスクリプションが必要です。",
        "契約中",
        "未契約",
        "次回更新日：{0}",
        "月額 {0}",
        "サブスクリプションに接続できなかったため、ここでは購入できるものがありません。Microsoft Store にサインインしているか確認して、もう一度お試しください。",
        "ストアは購入を完了と報告しましたが、権利を付与していません。ライセンスが一致するまで何も解放されません。しばらくしてもう一度お試しください。",
        "この Microsoft アカウントにサブスクリプションは見つかりませんでした。別のアカウントで購入した場合は、そのアカウントでサインインして再度復元してください。",
        "サブスクリプションに加入するまで、すべてのフレームにウォーターマークが入り、濃度も最大になります。このページは書き出されるとおりにフレームを描くため、ここで見えているものが動画に入るものです。",
        "購入する",
        "購入の復元",
        "サブスクリプションの管理",
        "動画の書き出しにはサブスクリプションが必要です",
        "どのページも、データの取得、アニメーションの再生、カバー画像の保存までは無料で、今後も無料のままです。サブスクリプションで購入する対象は動画の書き出しと、ウォーターマークの解除です。",
        "月額 {0}、いつでも解約できます。",
    ],
    "ko": [
        "구독",
        "화면에서 보이는 모든 것은 무료입니다. 데이터 불러오기, 애니메이션 재생, 커버 이미지 저장에는 비용이 들지 않습니다. 동영상 내보내기——그리고 워터마크 제거——에는 언제든 해지할 수 있는 월간 구독이 필요합니다.",
        "구독 중",
        "미구독",
        "{0}에 갱신",
        "월 {0}",
        "구독에 접속할 수 없어 지금은 여기서 살 수 있는 것이 없습니다. Microsoft Store에 로그인되어 있는지 확인하고 다시 시도하세요.",
        "스토어는 구매가 완료되었다고 보고했지만 권한을 부여하지 않았습니다. 라이선스가 확인될 때까지 아무것도 열리지 않습니다. 잠시 후 다시 시도하세요.",
        "이 Microsoft 계정에서는 구독을 찾지 못했습니다. 다른 계정으로 구매했다면 그 계정으로 로그인해 다시 복원하세요.",
        "구독하기 전까지 모든 프레임에 워터마크가 들어가고, 농도도 최대로 고정됩니다. 이 페이지는 파일로 쓰이는 그대로 프레임을 그리므로, 여기서 보이는 것이 동영상에 담기는 것입니다.",
        "구독하기",
        "구매 복원",
        "구독 관리",
        "동영상 내보내기에는 구독이 필요합니다",
        "모든 페이지가 데이터를 불러오고 애니메이션을 재생하고 커버 이미지를 저장하는 것은 무료이며, 앞으로도 무료입니다. 구독이 구매하는 것은 동영상 저장과 워터마크 제거입니다.",
        "월 {0}, 언제든 해지할 수 있습니다.",
    ],
    "zh-Hans": [
        "订阅",
        "屏幕上的一切仍然免费：取数、播放动画、保存封面图。导出视频与去掉水印需要按月订阅，可随时取消。",
        "已订阅",
        "未订阅",
        "{0} 续订",
        "每月 {0}",
        "无法联系到订阅，这里暂时没有可购买的内容。请确认 Microsoft Store 已登录并重试。",
        "商店报告购买已完成，但没有授予权限。许可证确认之前什么都不会解锁，请稍后重试。",
        "这个 Microsoft 账户下没有找到订阅。如果是用另一个账户买的，请用那个账户登录后再恢复。",
        "未订阅时每一帧都带水印，而且浓度拉满。本页绘制的帧与写进文件的完全一致——这里看到的就是视频里会有的。",
        "订阅",
        "恢复购买",
        "管理订阅",
        "导出视频需要订阅",
        "这里每个页面的取数、播放动画、保存封面图都不收费，今后也仍然免费。订阅买下的是导出视频，以及去掉水印。",
        "每月 {0}，可随时取消。",
    ],
    "zh-Hant": [
        "訂閱",
        "螢幕上的一切仍然免費：取數、播放動畫、儲存封面圖。匯出影片與移除浮水印需要按月訂閱，可隨時取消。",
        "已訂閱",
        "未訂閱",
        "{0} 續訂",
        "每月 {0}",
        "無法聯繫到訂閱，這裡暫時沒有可購買的內容。請確認 Microsoft Store 已登入並重試。",
        "商店回報購買已完成，但未授予權限。授權確認之前什麼都不會解鎖，請稍後再試。",
        "這個 Microsoft 帳戶下找不到訂閱。若是用其他帳戶購買的，請改用那個帳戶登入後再還原。",
        "未訂閱時每一格畫面都帶浮水印，濃度也拉滿。本頁繪製的畫面與寫入檔案的完全一致——這裡看到的就是影片裡會有的。",
        "訂閱",
        "還原購買",
        "管理訂閱",
        "匯出影片需要訂閱",
        "這裡每個頁面的取數、播放動畫、儲存封面圖都不收費，今後也仍然免費。訂閱買下的是匯出影片，以及移除浮水印。",
        "每月 {0}，可隨時取消。",
    ],
}


def insert_or_replace(text: str, key: str, value: str) -> tuple[str, str]:
    """把一个键写进 resw。返回 (新文本, 动了什么)。"""
    if _read(text, key) == value:
        return text, "same"

    row = '  <data name="%s"><value>%s</value></data>' % (key, _escape(value))

    pattern = re.compile(
        r'  <data name="%s"><value>.*?</value></data>' % re.escape(key), re.S)

    if pattern.search(text):
        return pattern.sub(lambda _: row, text, count=1), "replaced"

    return text.replace("</root>", row + "\n</root>"), "inserted"


def _read(text: str, key: str) -> str | None:
    pattern = re.compile(
        r'<data name="%s"><value>(.*?)</value>' % re.escape(key), re.S)
    found = pattern.search(text)
    return found.group(1) if found else None


def _escape(value: str) -> str:
    # resw 是 XML。这些句子里没有尖括号，但 '&' 会出现 —— 只转义必须转义的，其余保持原样
    # 「照原样」：一句espanol译文里平白多出 &amp; 是另一个人看不懂的东西。
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# 这两个键各替一个数字进去：少一个占位符是运行时的 FormatException，多一个是那句报错
# 永远说不完自己的钱。
FORMATTED = ("SettingsSubscriptionRenews", "SettingsSubscriptionPrice", "SubscriptionPerMonth")


def main() -> int:
    tally: dict[str, int] = {}

    for tag in sorted(TEXT):
        rows = TEXT[tag]

        if len(rows) != len(KEYS):
            print("%-9s %d rows for %d keys" % (tag, len(rows), len(KEYS)))
            return 1

        path = ROOT / tag / "Resources.resw"

        if not path.exists():
            print("missing: %s" % path)
            return 1

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig").lstrip("\ufeff")

        for key, value in zip(KEYS, rows):
            if key in FORMATTED and "{0}" not in value:
                print("%-9s %s has no {0} to put anything in" % (tag, key))
                return 1

            if key not in FORMATTED and "{0}" in value:
                print("%-9s %s takes no argument but carries a {0}" % (tag, key))
                return 1

            text, how = insert_or_replace(text, key, value)
            tally[how] = tally.get(how, 0) + 1

        if "\r\n" in text:
            print("%-9s the file came back with CRLF endings" % tag)
            return 1

        if not had_bom:
            print("%-9s the file has lost its BOM" % tag)
            return 1

        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

        print("%-9s written" % tag)

    print("\n14 languages: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(tally.items())))

    return 0


if __name__ == "__main__":
    sys.exit(main())
