# Market Motion Studio

Bu uygulama A hisse piyasasının göstergelerini telefon için dikey videolara dönüştürür. Bir dönem seçer, iyi okunana kadar ön izlemeye bakar ve MP4 olarak verirsiniz. Başka hiçbir şey kurmanız gerekmez.

## Piyasa seçimi

Ayarlarda uygulamanın hangi piyasadan fiyat aldığı seçilir; varsayılan A hisseleri. Değişiklik uygulama yeniden başlatıldıktan sonra geçerli olur.

- **A hisseleri**: yedi sayfanın tümü kullanılabilir.
- **Hong Kong**: getiri matrisi ve takvim çalışır; sektör yarışı dört Hang Seng alt endeksiyle koşulur; **tüm piyasa için veri yok, bu yüzden o sayfa gizlenir**.
- **ABD**: getiri matrisi ve takvim çalışır; sektör yarışı on SPDR sektör ETF'i ile koşulur; hacim sayfasında yalnızca günlük mod kalır, çünkü dakikalık uç nokta ABD verisi sunmaz; **tutarlar dolar cinsindendir ve tüm piyasa hacmi sayfası gizlenir**.



## Sayfalar arasında gezinme

Başlık çubuğunun solundaki iki düğme, tıpkı bir tarayıcı gibi, ziyaret ettiğiniz sayfalarda geri ve ileri gider: **Alt+Sol ok** ve **Alt+Sağ ok** ya da farenin yan düğmeleri.

- Sayfa bıraktığınız hâliyle korunur, bu yüzden bir sayfaya dönmek seçili aralığı ve önizlemeyi olduğu gibi geri getirir; yeniden açılmış bir sayfa değildir.
- Tarayıcıdaki gibi, yeni bir sayfa seçmek önünüzdekini siler.
- Gezinme bölmesi katlanmışken de çalışırlar; önizlemenin genişliğe en çok ihtiyaç duyduğu an da budur.

## Piyasa işlem hacmi

Tüm piyasanın günlük işlem hacmi: Şanghay ve Şenzen bileşik endekslerinin tutarları toplanır, her işlem günü için bir çubuk.

- Yalnızca dahil edilen tüm piyasaların işlem gördüğü günler tutulur; böylece tek bir piyasanın tatili toplamın çöktüğü izlenimini veremez.
- Hâlâ süren bir seans dışarıda bırakılır. Bitmemiş bir gün yalnızca açılış seansını içerir ve eksene yapışık bir çubuk olarak çizilirdi.
- Ya da yalnızca bir pazara bakın: her iki borsa, her ana pazar, STAR, ChiNext. Ana pazarlar borsa toplamından büyüme pazarının düşülmesiyle bulunur; BSE 50 hâlâ bileşen bazlı bir ölçüdür.
- Tüm piyasa için toplamı yalnızca A hisseleri verir. Hong Kong veya ABD seçildiğinde sayfa gezinmeden çıkarılır.

## Hacim ve devir

Bir hissenin işlem miktarı ile devir hızı, üst üste iki panel halinde.

- İşlem günleri boyunca işlem miktarı ile devir hızı oranlıdır, dolayısıyla iki panel neredeyse aynı biçimi alır. Tek bir gün içinde dakikalık miktar ile birikimli devir gerçekten farklı görünür ve daha ilgi çekici olan resim budur.
- Gün içi kaynağı yalnızca son birkaç işlem gününü tutar; bu yüzden o kip rastgele bir tarih değil, o günleri sunar.
- Dakikalık veri yalnızca A hisseleri ve Hong Kong için sunulur; ABD’de bu mod sunulmaz.

## Sektör yarışı

![Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.](media/sector-race.png)

Bir grup sektör veya hissenin yatay çubuklarla çizimi; çubuklar birbirini geçer, sıralama son kareye kadar değişir.

- İki ölçüt: dönemin yüzde değişimi ve yüz milyonlarca yuan cinsinden işlem hacmi. Ölçütü değiştirmek aynı veriyi yeniden renklendirir, tekrar veri çekmez.
- Dört liste: Shenwan 1. seviye sektörler, popüler temalar, özel (kutucukları işaretle) ve tekil hisseler (arama ile ekle). Özel liste başlangıçta Shenwan 1. seviye sektörlerle dolar.
- Yerleşik listeler piyasaya göre değişir: A hisseleri için Shenwan 1. düzey sektörler ve güncel temalar, Hong Kong için dört Hang Seng alt endeksi, ABD için on SPDR sektör ETF'i. Özel liste ve hisse listesi her piyasada vardır.
- Dönem 1, 3, 6 veya 12 ay ya da özel başlangıç ve bitiş tarihi olabilir.
- Bir listenin en az ve en fazla sayıda kalemi vardır — çok az çubuk yarış olmaz, çok fazlası yığılır.

## Getiri matrisi

![Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.](media/monthly-matrix.png)

Aylık çubuklar bir ızgaraya dizilir: yıl modu bir aracın on yıllık mevsimselliğini, karşılaştırma modu birkaç aracı yan yana dizerek rotasyonu gösterir.

- Yıl modu: bir araç seçin (arama veya ön tanımlı geniş endeks); aralık 1–10 yıl veya tümü. Tek istek on yıllık aylık çubuğu getirir.
- Karşılaştırma modu: bir listeden (1. seviye sektörler / temalar / geniş endeksler / özel / hisseler) 2–14 aracı yan yana, 6–48 ay aralıkla.
- Izgara zaman sırasıyla hücre hücre yanar; sonda aralıktaki en güçlü ve en zayıf ay ile diğer istatistikler verilir.
- Aylık veriler bir seferde on yılı kapsar, bu yüzden günlük gün sınırı yoktur — ama çok fazla araç çerçeveyi aşar.

## Yükseliş-düşüş takvimi

![Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.](media/gain-calendar.png)

Herhangi bir Çin hissesi veya endeksi, günlük yükseliş veya düşüşü aylık takvim hücrelerine dizilir: yükselişte kırmızı, düşüşte yeşil.

- Kod, ad veya pinyin ile arayın; ön tanımlılar geniş endekslerdir. Yalnızca seçtiğiniz piyasanın enstrümanları desteklenir.
- Favori listesi uygulamanın hisse sayfasıyla paylaşılır — iki yerden birinde eklenen favori her ikisinde görünür.
- Dönem 1, 3, 6 veya 12 ay ya da özeldir; tek bir araç yine de yaklaşık 640 takvim günü sınırına tabidir.
- Son istatistikler yükselen ve düşen işlem günü sayısını verir.

## DCA Planı

![Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.](media/dca-plan.png)

Sabit tutarla sabit aralıklarla bir varlık almak — her işlem günü, her hafta veya her ay — ve disiplinin neye dönüştüğünü animasyonla görmek.

- Tek dokunuşla seçilen varlıklar piyasayı izler: A hisselerinde geniş ve altın ETF'ler, Hong Kong takip fonları, ABD'de SPY, QQQ ve GLD.
- Tutarı ve sıklığı siz belirlersiniz; süre üç, beş veya on yıl, ya da verinin geldiği en eski tarihe kadar (yaklaşık on üç yıl).
- Getiri geriye düzeltilmiş kapanış fiyatları üzerinden, ücretsiz hesaplanır. Sonuç fiyat serisinin bir tarifi, kimsenin aynen uygulayabileceği bir fatura değildir.

## Pozisyon Getirisi

![Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.](media/position.png)

Tek bir alım, yıllarca tutulan — örneğin 2015'te 中国平安'a bir milyon — değer ve getirinin ne yaptığının animasyonu.

- Önerilen isimler pazara göre değişir: Çin'de insanların gerçekten "tutmuştum" dediği hisseler (Ping An, Moutai, CMB…), Hong Kong'da Tencent, HSBC ve Tracker Fund, ABD'de Apple, Berkshire ve SPY.
- Başlangıç sermayesi ve elde tutma süresi size ait; süre üç, beş veya on yıl olabilir, ya da verilerin yettiği kadar (yaklaşık on üç yıl).
- Getiri geriye düzeltilmiş kapanışlarla — temettüler yeniden yatırıldı, ücretsiz — hesaplanır. Geriye düzeltme halka arzın ilk gününe demir atar ve temettüleri ileriye biriktirir, böylece cömert bir ödeyicinin ilk yılları asla negatif olmaz; ileriye düzeltmede bu olabilir.

## Video

Kare her zaman 9:16'dır. Geri kalan her şeyi siz belirlersiniz.

- Süre, animasyonu kesmek yerine tempoyu değiştirir: açılış, çubukların büyümesi ve kapanıştaki istatistikler seçtiğiniz uzunluğa yeniden paylaştırılır.
- Kenar boşlukları 1080×1920 karesine göre yazılır ve dışa verme çözünürlüğüne oranlanır; bir kez ayarlanan yerleşim her boyutta geçerlidir. Sol kenar boşluğu ayrıca eksen etiketlerinin nereye düşeceğini belirler: çok küçükse sayılar kareden çıkar.
- Güvenli alan kılavuzları, bir telefon uygulamasının kendi arayüzüyle kapattığı yeri gösterir. Ön izlemede çizilir, dosyaya hiç girmez.

## Videolar nereye gider

Dışa verilenler, seçiciyle belirlediğiniz bir klasöre yazılır. Belirlenmediği sürece ilk dışa verme sorar ve sonra hatırlar; ayarlardan değiştirilebilir ya da unutturulabilir.

## Arka plan resmi

Ayarlar sayfası, pencerenin arkasına karartılmış bir resim koyabilir. Kartlar ve paneller opak kalır, gezinti bölmesi yalnızca biraz geçirir — resim asıl olarak çevrelerinde görünür. Video önizlemesinin kendi opak arka planı vardır ve etkilenmez.

- Bilgisayarınızdan bir resim seçin ya da Windows ile gelen duvar kağıtlarını ve kilit ekranı resimlerini doğrudan kullanın.
- Seçilen resim uygulamanın kendi klasörüne kopyalanır; özgün dosyayı taşımak veya silmek arka planı etkilemez.
- Maske yoğunluğu kaydırıcısı, resmin ne kadar karartılacağını %30–95 arasında belirler.
- Yüksek karşıtlık açıkken arka plan resmi gösterilmez.
## Animasyon arka planı

Ayarlar sayfasında animasyonun neyin üzerine çizileceğini değiştirebilirsiniz: yerleşik geçiş, kendi seçtiğiniz iki renk veya bir resim. Önizleme, dışa aktarılan video ve kapak görseli için geçerlidir — üçünü de aynı oluşturucu çizer, yani "önizlemede güzel, dosyada farklı" diye bir şey yoktur.

- Renk seçtiğinizde üst ve alt için birer ton verirsiniz ve kare ikisi arasında geçer. Koyu renkler daha uygundur: tüm metin tonları açıktır ve açık arka plan sayıları okumayı zorlaştırır.

- Resim seçmek pencere arka planındaki gibi işler: bilgisayarınızdan bir resim ya da Windows ile gelen bir duvar kağıdı. Seçtiğiniz resim uygulamanın klasörüne kopyalanır.

- Resim kareyi doldurur, artan kısım kırpılır; oranları asla bozulmaz.

- Karartma sürgüsü, resmin sayfanın kendi arka planına ne kadar geri çekileceğini belirler: %20 ile %95 arası.

## Veri ve söylemeyecekleri

Fiyatlar Tencent Finance'in herkese açık uç noktalarından gelir ve kare kaynağı her zaman belirtir. Bu videolar zaten gerçekleşmiş işlemleri anlatır. Yalnızca bilgi amaçlıdır ve yatırım tavsiyesi değildir.

- İşlem hacmi yüz milyon yuan birimine çevrilir ve sayılar gerektirdiğinde işlem miktarı daha büyük bir birime geçer, böylece eksen okunabilir kalır.
- Tutarlar yüz milyonlara çevrilir — anakara ve Hong Kong’da yuan, ABD’de dolar. Her piyasa kendi para birimini korur.
- Yaklaşık 640 takvim gününden uzun bir dönem, sessizce kısaltılmak yerine reddedilir; çünkü kaynağa yapılan tek bir istek ancak bu kadarını döndürür.

## Güncelleme

Microsoft Store'da daha yeni bir sürüm olduğunda gezinti bölmesinde Ayarlar'ın yanında bir **Güncelle** düğmesi görünür; tek tıkla kurulur.

- Yalnızca Store'da gerçekten daha yeni bir sürüm varsa görünür. Geliştirme veya yandan yüklenmiş bir derlemede hiç görünmez, bu normaldir.
- Yükleme sırasında uygulama kapanır ve yeni sürümle yeniden başlar, düğme kaybolur. Dışa aktarma sürüyorsa önce sorar.
- Kurulamazsa nedenini söyler — yalnızca Wi-Fi, pil çok düşük — ve güncelleme Microsoft Store'dan da kurulabilir.

## Bir sorun mu var?

gaqo@outlook.com adresine yazın ve ne yaptığınızı, bunun yerine ne beklediğinizi belirtin. Sürüm numarası ayarlar sayfasındadır.
