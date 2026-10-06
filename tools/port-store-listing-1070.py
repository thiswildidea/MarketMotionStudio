# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.7.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是「订阅买不成时不再
一声不响」——那件事在 1.0.6.0 已经上架了，接着往后加只会让这一栏自相矛盾。

本版要说的一件事是：**订阅买不成这件事现在可以排查了**。上一版把话说出来了（不再安静），
但只留一句「商店没有可买的加载项」，说不出为什么；而「商店真没给」和「查询失败了」和
「给了别的名字」是三种修法。本版把它们分开，并且不再只按 Durable 去找订阅——**假如那只加载项
在合作伙伴中心被建成了别的类型，本版会直接找到它**，这是这一版唯一有可能把订阅变成可买的改动。

**不在这里写第十五套「十七个图表页」。** 那句话已经在说明段里长期成立，写进「新增功能」会让
人以为页面数是本版变的。末尾那句「其余照旧」说的是订阅的范围没变，不是页面数。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

用法：python tools\\port-store-listing-1070.py      （跑第二遍应当是「改了 0 条」）
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

# 本版那一句。十四种语言同一种说法：**以前只说「没有」，现在说得出是哪种「没有」**。
NEWS = {
    "zh-Hans":
        "本版让「订阅买不成」这件事可以排查。以前只留下一句「商店没有可买的加载项」，说不出为什么；"
        "现在查询失败会单独记一行并带上错误码，商店返回了别的加载项时会把它连名字和类型一起列出来，"
        "本应用也不再只按一种类型去找订阅——假如那只加载项在商店里被建成了别的类型，本版会直接找到它。"
        "其余照旧：十七个图表页的取数、播放动画、保存封面图依旧免费，订阅买下的仍然只是导出视频与去掉水印这两件。",
    "zh-Hant":
        "本版讓「訂閱買不成」這件事可以排查。以前只留下一句「商店沒有可買的附加元件」，說不出為什麼；"
        "現在查詢失敗會單獨記一行並帶上錯誤碼，商店回傳了別的附加元件時會把它連名字和類型一起列出來，"
        "本應用也不再只按一種類型去找訂閱——假如那個附加元件在商店裡被建成了別的類型，本版會直接找到它。"
        "其餘照舊：十七個圖表頁的取數、播放動畫、儲存封面圖依舊免費，訂閱買下的仍然只是匯出影片與移除浮水印這兩件。",
    "en-US":
        "This version makes a subscription that cannot be bought diagnosable. What used to be a "
        "single line - the Store handed out nothing to buy - gave no reason, while \"the Store has "
        "nothing\", \"the query failed\" and \"it goes by another name\" are three different "
        "repairs. Now a failed query gets a line of its own with its error code, whatever the Store "
        "did return is listed with its name and kind, and the app no longer looks for the "
        "subscription under one add-on kind only, so an add-on created under a different kind is "
        "found outright. Nothing else changed: fetching data, playing the animation and saving a "
        "cover image stay free on all seventeen chart pages, and the subscription still buys only "
        "two things, exporting a video and removing the watermark.",
    "ja":
        "このバージョンは、購読を買えないときに原因を辿れるようにします。以前は「ストアに買える"
        "ものがない」という一行だけで理由が分かりませんでしたが、「ストアにない」「問い合わせが"
        "失敗した」「別の名前で登録されている」はそれぞれ直し方が違います。今は問い合わせが失敗"
        "すればエラーコード付きで別の行が残り、ストアが返したものは名前と種類が並び、さらに一種類の"
        "アドオンだけを探すのをやめたので、別の種類として作られたアドオンも見つかります。他は変わり"
        "ません。十七のチャートページでのデータ取得、アニメーションの再生、表紙画像の保存は引き続き"
        "無料で、購読で買うのは動画の書き出しと透かしの削除の二つだけです。",
    "ko":
        "이 버전은 구독을 살 수 없을 때 원인을 좇을 수 있게 합니다. 이전에는 '스토어에 살 수 있는 "
        "항목이 없다'는 한 줄뿐이어서 이유를 알 수 없었지만, '스토어에 없음', '조회 실패', "
        "'다른 이름으로 등록됨'은 서로 다른 수정이 필요합니다. 이제 조회가 실패하면 오류 코드와 함께 "
        "별도의 줄이 남고, 스토어가 반환한 항목은 이름과 종류가 함께 나열되며, 한 가지 종류의 추가 "
        "기능만 찾지도 않으므로 다른 종류로 만들어진 추가 기능도 그대로 찾습니다. 다른 것은 그대로"
        "입니다. 열일곱 개 차트 페이지의 데이터 가져오기, 애니메이션 재생, 표지 이미지 저장은 계속 "
        "무료이며, 구독으로 살 수 있는 것은 동영상 내보내기와 워터마크 제거 두 가지뿐입니다.",
    "de":
        "Diese Version macht ein Abonnement, das sich nicht kaufen lässt, nachvollziehbar. Früher "
        "stand dort nur eine Zeile – der Store hat nichts zu kaufen herausgegeben – ohne Grund, "
        "dabei sind „der Store hat nichts“, „die Abfrage ist fehlgeschlagen“ und „es heißt anders“ "
        "drei verschiedene Reparaturen. Jetzt bekommt eine fehlgeschlagene Abfrage eine eigene "
        "Zeile mit ihrem Fehlercode, was der Store zurückgegeben hat, wird mit Namen und Art "
        "aufgelistet, und die App sucht das Abonnement nicht mehr unter einer einzigen Add-on-Art, "
        "sodass ein als andere Art angelegtes Add-on direkt gefunden wird. Sonst bleibt alles wie "
        "es ist: Daten abrufen, Animation abspielen und Titelbild speichern bleiben auf allen "
        "siebzehn Diagrammseiten kostenlos, und das Abonnement kauft weiterhin nur zwei Dinge, das "
        "Exportieren eines Videos und das Entfernen des Wasserzeichens.",
    "fr":
        "Cette version rend un abonnement impossible à acheter explicable. Auparavant, une seule "
        "ligne indiquait que le Store n'avait rien à vendre, sans en donner la raison, alors que "
        "« le Store n'a rien », « la requête a échoué » et « il porte un autre nom » sont trois "
        "réparations differentes. Désormais une requête qui échoue laisse sa propre ligne avec son "
        "code d'erreur, ce que le Store a renvoyé est listé avec son nom et son type, et "
        "l'application ne cherche plus l'abonnement sous un seul type de module, si bien qu'un "
        "module créé sous un autre type est trouvé directement. Rien d'autre ne change : la "
        "récupération des données, la lecture de l'animation et l'enregistrement de l'image de "
        "couverture restent gratuits sur les dix-sept pages de graphiques, et l'abonnement n'achète "
        "toujours que deux choses, l'exportation d'une vidéo et la suppression du filigrane.",
    "it":
        "Questa versione rende comprensibile un abbonamento che non si riesce ad acquistare. Prima "
        "restava una sola riga - lo Store non ha fornito nulla da acquistare - senza motivo, mentre "
        "«lo Store non ha nulla», «la query non è riuscita» e «si chiama in un altro modo» sono tre "
        "riparazioni diverse. Ora una query non riuscita lascia una riga propria con il suo codice "
        "di errore, ciò che lo Store ha restituito viene elencato con nome e tipo, e l'app non "
        "cerca più l'abbonamento sotto un solo tipo di componente, così un componente creato con un "
        "altro tipo viene trovato direttamente. Nient'altro cambia: il recupero dei dati, la "
        "riproduzione dell'animazione e il salvataggio dell'immagine di copertina restano gratuiti "
        "su tutte le diciassette pagine di grafici, e l'abbonamento continua a comprare solo due "
        "cose, l'esportazione di un video e la rimozione della filigrana.",
    "es":
        "Esta versión hace que una suscripción que no se puede comprar sea explicable. Antes quedaba "
        "una sola línea —la Store no entregó nada que comprar— sin motivo, aunque «la Store no tiene "
        "nada», «la consulta falló» y «tiene otro nombre» son tres arreglos distintos. Ahora una "
        "consulta fallida deja su propia línea con su código de error, lo que la Store devolvió se "
        "enumera con su nombre y tipo, y la aplicación ya no busca la suscripción bajo un único tipo "
        "de complemento, de modo que un complemento creado con otro tipo se encuentra directamente. "
        "Nada más cambia: la obtención de datos, la reproducción de la animación y el guardado de la "
        "imagen de portada siguen siendo gratuitos en las diecisiete páginas de gráficos, y la "
        "suscripción sigue comprando solo dos cosas, exportar un vídeo y quitar la marca de agua.",
    "pt-BR":
        "Esta versão torna explicável uma assinatura que não pode ser comprada. Antes restava uma "
        "única linha — a Store não forneceu nada para comprar — sem motivo, embora «a Store não tem "
        "nada», «a consulta falhou» e «tem outro nome» sejam três correções diferentes. Agora uma "
        "consulta que falha deixa sua própria linha com o código de erro, o que a Store devolveu é "
        "listado com nome e tipo, e o aplicativo não procura mais a assinatura sob um único tipo de "
        "complemento, de modo que um complemento criado com outro tipo é encontrado diretamente. "
        "Nada mais muda: a busca de dados, a reprodução da animação e o salvamento da imagem de capa "
        "continuam gratuitos nas dezessete páginas de gráficos, e a assinatura continua comprando "
        "apenas duas coisas, exportar um vídeo e remover a marca d'água.",
    "pl":
        "Ta wersja sprawia, że subskrypcji, której nie można kupić, da się wyjaśnić. Wcześniej "
        "zostawała jedna linia — Sklep nie udostępnił niczego do kupienia — bez powodu, choć „Sklep "
        "nie ma niczego”, „zapytanie się nie powiodło” i „nazywa się inaczej” to trzy różne naprawy. "
        "Teraz nieudane zapytanie zostawia własną linię z kodem błędu, to, co Sklep zwrócił, jest "
        "wypisane z nazwą i rodzajem, a aplikacja nie szuka już subskrypcji tylko w jednym rodzaju "
        "dodatku, więc dodatek utworzony jako inny rodzaj zostanie znaleziony bezpośrednio. Nic "
        "więcej się nie zmienia: pobieranie danych, odtwarzanie animacji i zapisywanie obrazu "
        "okładki pozostają bezpłatne na siedemnastu stronach wykresów, a subskrypcja nadal kupuje "
        "tylko dwie rzeczy, eksport wideo i usunięcie znaku wodnego.",
    "cs":
        "Tato verze dělá předplatné, které nelze koupit, vysvětlitelným. Dříve zůstával jediný "
        "řádek – Store nevydal nic k zakoupení – bez důvodu, přestože „Store nic nemá“, „dotaz selhal“ "
        "a „jmenuje se jinak“ jsou tři různé opravy. Nyní neúspěšný dotaz zanechá vlastní řádek s "
        "chybovým kódem, to, co Store vrátil, je vypsáno s názvem a druhem, a aplikace již nehledá "
        "předplatné pouze v jednom druhu doplňku, takže doplněk vytvořený jako jiný druh je nalezen "
        "přímo. Nic jiného se nemění: načítání dat, přehrávání animace a ukládání titulního obrázku "
        "zůstávají na sedmnácti stranách grafů zdarma a předplatné nadále kupuje jen dvě věci, export "
        "videa a odstranění vodoznaku.",
    "ru":
        "Эта версия делает понятной подписку, которую невозможно купить. Раньше оставалась одна "
        "строка — магазин не выдал ничего для покупки — без причины, хотя «в магазине ничего нет», "
        "«запрос не удался» и «она называется иначе» — это три разных исправления. Теперь "
        "неудачный запрос оставляет отдельную строку с кодом ошибки, то, что вернул магазин, "
        "перечисляется с именем и типом, и приложение больше не ищет подписку только среди одного "
        "типа надстройки, поэтому надстройка, созданная с другим типом, будет найдена сразу. Ничего "
        "другого не меняется: получение данных, воспроизведение анимации и сохранение обложки "
        "остаются бесплатными на семнадцати страницах диаграмм, а подписка по-прежнему покупает "
        "только две вещи — экспорт видео и удаление водяного знака.",
    "tr":
        "Bu sürüm, satın alınamayan bir aboneliği açıklanabilir kılıyor. Eskiden yalnızca tek bir "
        "satır kalıyordu — Mağaza satın alınacak bir şey vermedi — ve hiçbir neden belirtilmiyordu; "
        "oysa «Mağazada hiçbir şey yok», «sorgu başarısız oldu» ve «adı farklı» üç ayrı onarım. "
        "Artık başarısız bir sorgu hata koduyla kendi satırını bırakıyor, Mağaza'nın döndürdüğü "
        "şeyler adı ve türüyle listeleniyor ve uygulama aboneliği yalnızca tek bir eklenti türünde "
        "aramıyor, böylece başka bir tür olarak oluşturulmuş bir eklenti doğrudan bulunuyor. Başka "
        "hiçbir şey değişmiyor: on yedi grafik sayfasının tamamında veri alma, animasyonu oynatma ve "
        "kapak görselini kaydetme ücretsiz kalıyor ve abonelik yalnızca iki şeyi satın alıyor: video "
        "dışa aktarma ve filigranı kaldırma.",
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
