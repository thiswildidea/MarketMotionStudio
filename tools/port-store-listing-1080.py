# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.8.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是「订阅买不成可以排查了」
——那件事本身已经上架，接着往后加只会让这一栏自相矛盾。

本版要说的一件事是：**订阅认的是商店里那只真正的按月订阅**。之前认的那一只在合作伙伴中心被
建成了「Microsoft Store 托管的易耗品」，也就是买一次永久有效、不会续费的一次性买断——它和
「订阅」不是同一个东西，而产品的类型保存之后不能改、已发布的加载项名称也不能复用，所以只能
新建一只并改指向。

**这一栏不谈价格也不谈「现在能买了」。** 那只加载项发布到什么程度不归本版决定（改加载项配置
不需要重新上传应用），本版说的是「认对了哪一只」；写「现已开放订阅」等于替商店那一头承诺。
末尾那句「其余照旧」说的是订阅的范围没变，不是页面数。

**不在这里写第十五套「十七个图表页」。** 那句话已经在说明段里长期成立。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

用法：python tools\\port-store-listing-1080.py      （跑第二遍应当是「改了 0 条」）
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

# 本版那一句。十四种语言同一种说法：**以前认的是一次性买断，现在认的是按月订阅**。
NEWS = {
    "zh-Hans":
        "本版起，订阅认的是商店里那只真正的按月订阅。之前认的那一只在商店里被建成了一次性买断："
        "买一次永久有效、不会按月续费，和「订阅」不是同一个东西；而产品的类型一经保存就不能修改，"
        "已发布的加载项名称也无法复用，因此改为新建的那一只。等那一只在商店中发布并关联到本应用，"
        "设置页就会显示订阅的价格，买下的仍然是导出视频与去掉水印这两件事。其余照旧：十七个图表页"
        "的取数、播放动画、保存封面图依旧免费。",
    "zh-Hant":
        "本版起，訂閱認的是商店裡那個真正的按月訂閱。之前認的那一個在商店裡被建成了一次性買斷："
        "買一次永久有效、不會按月續費，和「訂閱」不是同一個東西；而產品的類型一經儲存就不能修改，"
        "已發佈的附加元件名稱也無法重複使用，因此改為新建的那一個。等那一個在商店中發佈並關聯到"
        "本應用程式，設定頁就會顯示訂閱的價格，買下的仍然是匯出影片與移除浮水印這兩件事。其餘照舊："
        "十七個圖表頁的取數、播放動畫、儲存封面圖依舊免費。",
    "en-US":
        "From this version the subscription points at the add-on in the Store that really is a "
        "monthly one. The add-on it used to ask for was created as a one-time purchase: bought once, "
        "it stays valid forever and never renews, which is not what a subscription is. A product's "
        "type cannot be changed once it has been saved and a published add-on name cannot be reused, "
        "so this version asks for the newly created one instead. Once that add-on is published and "
        "associated with this app, the settings page shows the subscription's price, and it still "
        "buys the same two things: exporting a video and removing the watermark. Nothing else "
        "changed - fetching data, playing the animation and saving a cover image stay free on all "
        "seventeen chart pages.",
    "ja":
        "このバージョンから、購読はストアにある本当の月額購読を指します。以前が指していたのは"
        "一回きりの買い切りとして作られたもので、一度買うと期限なく有効なまま更新もされず、"
        "購読とは別のものでした。製品の種類は保存すると変更できず、公開済みのアドオン名も再利用"
        "できないため、新しく作られたものを指すようにしました。それがストアで公開されこのアプリに"
        "関連付けられれば、設定ページに購読の価格が表示されます。購読で買えるのは今までどおり"
        "動画の書き出しと透かしの削除の二つです。他は変わりません。十七のチャートページでの"
        "データ取得、アニメーションの再生、表紙画像の保存は引き続き無料です。",
    "ko":
        "이 버전부터 구독은 스토어에 있는 진짜 월간 구독을 가리킵니다. 이전에 가리키던 것은 일회성 "
        "구매로 만들어진 것으로, 한 번 사면 기한 없이 유효하고 갱신되지 않으므로 구독과는 다른 "
        "것이었습니다. 제품 종류는 저장하면 변경할 수 없고 이미 게시된 추가 기능 이름도 다시 쓸 수 "
        "없으므로, 새로 만든 것을 가리키도록 했습니다. 그것이 스토어에 게시되고 이 앱에 연결되면 "
        "설정 페이지에 구독 가격이 표시됩니다. 구독으로 살 수 있는 것은 여전히 동영상 내보내기와 "
        "워터마크 제거 두 가지입니다. 다른 것은 그대로입니다. 열일곱 개 차트 페이지의 데이터 가져오기, "
        "애니메이션 재생, 표지 이미지 저장은 계속 무료입니다.",
    "de":
        "Ab dieser Version zeigt das Abonnement auf das Add-on im Store, das wirklich ein monatliches "
        "ist. Das Add-on, nach dem zuvor gefragt wurde, war als Einmalkauf angelegt: einmal gekauft "
        "bleibt es dauerhaft gültig und verlängert sich nie, was etwas anderes ist als ein "
        "Abonnement. Der Produkttyp lässt sich nach dem Speichern nicht ändern und ein "
        "veröffentlichter Add-on-Name nicht wiederverwenden, daher fragt diese Version nach dem neu "
        "angelegten. Sobald dieses Add-on veröffentlicht und dieser App zugeordnet ist, zeigt die "
        "Einstellungsseite den Preis des Abonnements, und es kauft weiterhin dieselben zwei Dinge: "
        "das Exportieren eines Videos und das Entfernen des Wasserzeichens. Sonst bleibt alles wie es "
        "ist: Daten abrufen, Animation abspielen und Titelbild speichern bleiben auf allen siebzehn "
        "Diagrammseiten kostenlos.",
    "fr":
        "À partir de cette version, l'abonnement pointe vers le module du Store qui est réellement "
        "mensuel. Celui qu'il demandait auparavant avait été créé comme un achat unique : acheté une "
        "fois, il reste valable indéfiniment et ne se renouvelle jamais, ce qui n'est pas un "
        "abonnement. Le type d'un produit ne peut pas être modifié après l'enregistrement et un nom "
        "de module publié ne peut pas être réutilisé ; cette version demande donc le module nouvellement "
        "créé. Une fois ce module publié et associé à cette application, la page des paramètres "
        "affiche le prix de l'abonnement, qui achète toujours les deux mêmes choses : l'exportation "
        "d'une vidéo et la suppression du filigrane. Rien d'autre ne change : la récupération des "
        "données, la lecture de l'animation et l'enregistrement de l'image de couverture restent "
        "gratuits sur les dix-sept pages de graphiques.",
    "it":
        "Da questa versione l'abbonamento punta al componente dello Store che è davvero mensile. "
        "Quello che chiedeva prima era stato creato come acquisto una tantum: comprato una volta "
        "resta valido per sempre e non si rinnova mai, che non è un abbonamento. Il tipo di un "
        "prodotto non può essere modificato dopo il salvataggio e il nome di un componente pubblicato "
        "non può essere riutilizzato, quindi questa versione chiede quello appena creato. Una volta "
        "che tale componente sarà pubblicato e associato a questa app, la pagina delle impostazioni "
        "mostrerà il prezzo dell'abbonamento, che continua a comprare le stesse due cose: "
        "l'esportazione di un video e la rimozione della filigrana. Nient'altro cambia: il recupero "
        "dei dati, la riproduzione dell'animazione e il salvataggio dell'immagine di copertina restano "
        "gratuiti su tutte le diciassette pagine di grafici.",
    "es":
        "A partir de esta versión, la suscripción apunta al complemento de la Store que sí es mensual. "
        "El que pedía antes se creó como una compra única: al comprarlo una vez sigue siendo válido "
        "para siempre y nunca se renueva, que no es lo mismo que una suscripción. El tipo de un "
        "producto no se puede cambiar una vez guardado y el nombre de un complemento publicado no se "
        "puede reutilizar, por lo que esta versión pide el recién creado. Cuando ese complemento esté "
        "publicado y asociado a esta aplicación, la página de configuración mostrará el precio de la "
        "suscripción, que sigue comprando las mismas dos cosas: exportar un vídeo y quitar la marca de "
        "agua. Nada más cambia: la obtención de datos, la reproducción de la animación y el guardado "
        "de la imagen de portada siguen siendo gratuitos en las diecisiete páginas de gráficos.",
    "pt-BR":
        "A partir desta versão, a assinatura aponta para o complemento da Store que realmente é "
        "mensal. O que era pedido antes foi criado como uma compra única: comprado uma vez, permanece "
        "válido para sempre e nunca renova, o que não é uma assinatura. O tipo de um produto não pode "
        "ser alterado depois de salvo e o nome de um complemento publicado não pode ser reutilizado; "
        "por isso esta versão pede o recém-criado. Quando esse complemento estiver publicado e "
        "associado a este aplicativo, a página de configurações mostrará o preço da assinatura, que "
        "continua comprando as mesmas duas coisas: exportar um vídeo e remover a marca d'água. Nada "
        "mais muda: a busca de dados, a reprodução da animação e o salvamento da imagem de capa "
        "continuam gratuitos nas dezessete páginas de gráficos.",
    "pl":
        "Od tej wersji subskrypcja wskazuje ten dodatek w Sklepie, który naprawdę jest miesięczny. "
        "Ten, o który pytano wcześniej, został utworzony jako zakup jednorazowy: kupiony raz pozostaje "
        "ważny na zawsze i nigdy się nie odnawia, co nie jest subskrypcją. Typu produktu nie można "
        "zmienić po zapisaniu, a nazwy opublikowanego dodatku nie można użyć ponownie, dlatego ta "
        "wersja pyta o nowo utworzony. Gdy ten dodatek zostanie opublikowany i powiązany z tą "
        "aplikacją, strona ustawień pokaże cenę subskrypcji, która nadal kupuje te same dwie rzeczy: "
        "eksport wideo i usunięcie znaku wodnego. Nic więcej się nie zmienia: pobieranie danych, "
        "odtwarzanie animacji i zapisywanie obrazu okładki pozostają bezpłatne na siedemnastu "
        "stronach wykresów.",
    "cs":
        "Od této verze předplatné ukazuje na ten doplněk ve Storu, který je skutečně měsíční. Ten, "
        "který se ptal dříve, byl vytvořen jako jednorázový nákup: po jednou zakoupení zůstává "
        "platný navždy a nikdy se neobnovuje, což předplatné není. Typ produktu nelze po uložení "
        "změnit a název publikovaného doplňku nelze znovu použít, proto tato verze žádá o nově "
        "vytvořený. Jakmile bude tento doplněk publikován a přidružen k této aplikaci, stránka "
        "nastavení zobrazí cenu předplatného, které nadále kupuje tytéž dvě věci: export videa a "
        "odstranění vodoznaku. Nic jiného se nemění: načítání dat, přehrávání animace a ukládání "
        "titulního obrázku zůstávají na sedmnácti stranách grafů zdarma.",
    "ru":
        "Начиная с этой версии подписка указывает на ту надстройку в магазине, которая действительно "
        "ежемесячная. Та, которую она запрашивала раньше, была создана как разовая покупка: купленная "
        "один раз, она остаётся действительной навсегда и никогда не продлевается, а это не подписка. "
        "Тип продукта нельзя изменить после сохранения, а имя опубликованной надстройки нельзя "
        "использовать повторно, поэтому эта версия запрашивает созданную заново. Когда эта надстройка "
        "будет опубликована и связана с этим приложением, на странице настроек появится цена подписки, "
        "которая по-прежнему покупает те же две вещи: экспорт видео и удаление водяного знака. Ничего "
        "другого не меняется: получение данных, воспроизведение анимации и сохранение обложки "
        "остаются бесплатными на семнадцати страницах диаграмм.",
    "tr":
        "Bu sürümden itibaren abonelik, Mağaza'daki gerçekten aylık olan eklentiyi gösteriyor. "
        "Önceden istenen eklenti tek seferlik satın alma olarak oluşturulmuştu: bir kez satın "
        "alındığında süresiz geçerli kalır ve hiç yenilenmez, ki bu abonelik değildir. Bir ürünün "
        "türü kaydedildikten sonra değiştirilemez ve yayımlanmış bir eklenti adı yeniden "
        "kullanılamaz; bu nedenle bu sürüm yeni oluşturulanı istiyor. Bu eklenti yayımlanıp bu "
        "uygulamayla ilişkilendirildiğinde, ayarlar sayfası aboneliğin fiyatını gösterecek ve "
        "abonelik yine aynı iki şeyi satın alacak: video dışa aktarma ve filigranı kaldırma. Başka "
        "hiçbir şey değişmiyor: on yedi grafik sayfasının tamamında veri alma, animasyonu oynatma ve "
        "kapak görselini kaydetme ücretsiz kalıyor.",
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
