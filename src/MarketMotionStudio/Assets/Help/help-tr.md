# Market Motion Studio

Bu uygulama A hisse piyasasının göstergelerini telefon için dikey videolara dönüştürür. Bir dönem seçer, iyi okunana kadar ön izlemeye bakar ve MP4 olarak verirsiniz. Başka hiçbir şey kurmanız gerekmez.

## Piyasa seçimi

Ayarlarda uygulamanın hangi piyasadan fiyat aldığı seçilir; varsayılan A hisseleri. Değişiklik uygulama yeniden başlatıldıktan sonra geçerli olur.

- **A hisseleri**: sekiz sayfanın tümü kullanılabilir.
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

- **Kendi listeniz.** Menünün son girdisi, sizin tuttuğunuz listedir — endeksler ve hisseler yan
  yana, dört roster tablosuyla paylaşılır. Yalnızca anakara kodları toplanabilir: işlem hacmi her
  piyasanın kendi para biriminde bildirilir, bu yüzden Hong Kong veya New York adı dışarıda kalır
  ve durum satırı kaç tane olduğunu söyler. Bir gün, *herhangi bir* üye işlem gördüyse eksende
  yer alır; o güne ait satırı olmayan üye — işleme kapatılmış ya da henüz listelenmemiş — hiçbir
  şey eklemez. Bu, yukarıdaki tabloların kuralının kasıtlı olarak tersidir: bir endeks asla
  kapatılmaz, bir hisse kapatılır ve günü atmak, kapatılmayı hiçbir yerde işlem olmayan bir gün
  gibi gösterirdi. Bu tablo girdilerini **toplar**; bir adı tıklamak onu toplama katar ya da
  dışarıda bırakır ve yalnızca **ilk** girdiyle açılır. Liste genellikle sıralama tabloları için
  kurulur; orada bir düzine ad olağandır ve toplamları kimseye dair bir sayı değildir.
- **Sepetin altındaki değişim**, her üyenin kendi önceki kapanışına göre ölçülen günlük
  değişimlerinin eşit ağırlıklı ortalamasıdır. Eşit ağırlıklıdır, çünkü bir liste portföy değildir:
  ağırlıklandıracak bir pozisyon büyüklüğü yoktur.
- **Tek bir seans, dakika dakika.** Üçüncü biçim ayrı bir sorgudur: tek bir günün açılıştan
  kapanışa kadar biriken toplamı. Kaynak yalnızca son beş seansı saklar, bu yüzden aralık
  sunulmaz — kare, çizdiği günü adlandırır. Eğri 15:00'te durur, çünkü uç noktanın sonra eklediği
  yarım saat, günlük rakamın da içermediği seans sonrası işlemlerdir. Dört kart, günün toplamı ile
  sabah, öğleden sonra ve son yarım saatin payıdır — para*ın ne zaman* hareket ettiğinin grafiği,
  bu yüzden dörtten üçü tutar değil paydır. BSE 50, işlem hacmi sütunu olmadan dakika bildiren tek
  tablodur ve hiç sayılmak yerine reddedilir.

## Mum grafiği

Bir enstrümanın mumları: günlük, haftalık veya aylık — ya da tek bir işlem günü için dakika mumları — dört farklı şekilde çizilir; altında ortalamaları ve hacmi.

- **Aralık**, bir mumun ne kadar piyasa zamanını kapsadığını belirler: bir gün, bir hafta veya bir ay. Bunu değiştirmek yeniden veri çeker, çünkü kaynakta üçü ayrı serilerdir.
- **1, 5 ve 15 dakika** tek bir işlem gününü çizer: açılıştan kapanışa seans, saate göre kurulan ve hiç işlem geçmeyen doksan dakikayı dışarıda bırakan bir eksende; öğleden önce ve sonra, resmin üçte birini boş bırakmak yerine ince bir çizgide buluşur. Kaynak dakika mumlarını yalnızca Şanghay ve Shenzhen için ve yalnızca son birkaç seans için tutar — bir dakikada yaklaşık dört gün, beşte on yedi, on beşte elli — bu yüzden **İşlem günü** bir takvim değil, hâlâ elinde olan günlerin listesidir. Başka bir günü seçmek yalnızca yeniden çizer.
- **Çizim türü**, aynı dört fiyatın nasıl çizileceğini belirler: mumlar, OHLC çubukları, kapanış çizgisi veya kapanış alanı. Aralarında geçiş yapmak hiçbir şey yeniden çekmez.
- **Animasyon**, mumların tek tek gelip tüm aralığı çizmesi ya da ilerleyen sabit bir penceredir. İkincisi, mumu uzun bir aralıkta okunacak kadar geniş tutan şeydir ve bu genişlik **Pencere** ayarıdır.
- MA5, MA10 ve MA20 hareketli ortalamaları mumların üzerine bindirilebilir; alttaki hacim paneli kapatılabilir ve fiyat paneli o alanı geri alır.
- Henüz bitmemiş bir hafta veya ay dışarıda bırakılır. Üç günden oluşan bir mum bir hafta değildir.
- Her piyasa düzeltilmiş serisinden okunur, bu yüzden bir bölünme günü düşüş olarak çizilmez; temettü de çizilmez.
- **Aralık** periyoda göre değişir: günlükte 3, 6 veya 12 ay ya da 3, 5 veya 10 yıl; haftalıkta 1, 3, 5 veya 10 yıl; aylıkta 3, 5 veya 10 yıl ya da kaynağın sunduğu en uzun aralık (yaklaşık 13). Bir istek yaklaşık 640 günlük mum getirir ve sayfa geriye doğru sayfa sayfa ilerler, bu yüzden on yıl — yaklaşık 2.500 mum — sınırın içinde kalır.

## Hacim ve devir

Bir hissenin işlem miktarı ile devir hızı, üst üste iki panel halinde.

- İşlem günleri boyunca işlem miktarı ile devir hızı oranlıdır, dolayısıyla iki panel neredeyse aynı biçimi alır. Tek bir gün içinde dakikalık miktar ile birikimli devir gerçekten farklı görünür ve daha ilgi çekici olan resim budur.
- Gün içi kaynağı yalnızca son birkaç işlem gününü tutar; bu yüzden o kip rastgele bir tarih değil, o günleri sunar.
- Dakikalık veri yalnızca A hisseleri ve Hong Kong için sunulur; ABD’de bu mod sunulmaz.
- Günlük veride aralık 1, 3, 6, 12 veya 24 ay ya da kendi belirlediğiniz başlangıç ve bitiş tarihidir; özel aralık yaklaşık 900 takvim gününde durur — bir isteğin döndürdüğü kadar — ve tarih seçiciler de orada durur. Gün içi modu, o birkaç işlem günü arasından bir gün seçmenizi sağlar.

## Sektör yarışı

![Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.](media/sector-race.png)

Bir grup sektör veya hissenin yatay çubuklarla çizimi; çubuklar birbirini geçer, sıralama son kareye kadar değişir.

- İki ölçüt: dönemin yüzde değişimi ve yüz milyonlarca yuan cinsinden işlem hacmi. Ölçütü değiştirmek aynı veriyi yeniden renklendirir, tekrar veri çekmez.
- Dört liste: Shenwan 1. seviye sektörler, popüler temalar, özel (kutucukları işaretle) ve tekil hisseler (arama ile ekle). Özel liste başlangıçta Shenwan 1. seviye sektörlerle dolar.
- Yerleşik listeler piyasaya göre değişir: A hisseleri için Shenwan 1. düzey sektörler ve güncel temalar, Hong Kong için dört Hang Seng alt endeksi, ABD için on SPDR sektör ETF'i. Özel liste ve hisse listesi her piyasada vardır.
- Dönem 1, 3, 6, 12 veya 24 ay ya da özel başlangıç ve bitiş tarihi olabilir. Kendi aralığınız yaklaşık 900 güne ulaşır — bir isteğin kapsadığı kadar — ve tarih seçiciler orada durur.
- Bir listenin en az ve en fazla sayıda kalemi vardır — çok az çubuk yarış olmaz, çok fazlası yığılır.




## Piyasa değeri yarışı

Bir piyasanın en büyük on beş şirketi, piyasa değerine göre sıralanmış yatay çubuklar olarak;
sıralama son kareye kadar değişir. Örnekleme aylıktır.

- **Sıralama her dönemde yeniden hesaplanır.** Veri çekilirken önce kaynaktan güncel piyasa değeri
  sıralaması istenir, ilk iki yüz aday olarak alınır ve bir zamanlar listede olup düşen ağır
  hisseler eklenir; her dönem bu kadro içinden en büyük on beşi gösterir. Üyeler gerçekten girer ve
  çıkar — 2016'da petrol ve bankalardı, 2026'da 茅台, 宁德时代 ve 工业富联 eklendi. Programa
  yazılmış bir kadro, halka açılıp hemen zirveye oturan bir şirketi kaçırdı; artık kadro
  hatırlanmıyor, soruluyor.
- **Geçmiş piyasa değeri hesaplanır**: bugünkü piyasa değeri çarpı dönemin düzeltilmiş fiyat oranı.
  Bedelsiz sermaye artırımları ve bölünmeler düzeltilmiş seride birbirini götürür; temettüler
  götürmez — yeniden yatırılır, bu yüzden çok temettü veren bir şirketin geçmiş değeri düşük çıkar.
  Doğrudan kaynaktan gelen tek sayı son kareninkidir.
- **Henüz halka açılmamış şirket sıfırdan büyür**: 2018'de işlem görmeye başlayan hisseler, önceden
  yer tutmak yerine girdikleri gün taban çizgisinden yükselir.
- **Aralık gün değil ay**: on yılda yüz yirmi dönem, bir yılda on iki ve karenin başlığı ay sayısını
  yazar. Piyasa değeri sıralaması yavaş bir değişkendir ve aylık örnekleme tüm geçmişi tek istekte
  alır.
- **Her piyasanın kendi on beşi var.** Üçü asla karıştırılmaz: paraları aynı para değildir.
- Aralık son 12 ay, 3, 5 veya 10 yıl ya da **En uzun** seçeneğidir — bir istek 180 aylık dönemin tamamını, yani yaklaşık on beş yılı döndürür ve bu seçenek orada biter. Kendi başlangıç ve bitiş tarihlerinizi de yazabilirsiniz.
  Hong Kong ve New York sabit kadro kullanır, çünkü bu uygulamanın erişebildiği bir sıralama
  onlara hizmet etmiyor.





## A/H primi

İki tarafta da kote olan şirketler için, karadaki kotasyonun Hong Kong kotasyonundan ne kadar
pahalı olduğu — ay ay, birbirini geçen çubuklar olarak.

- **Prim = A fiyatı ÷ (H fiyatı × HKD/CNY) − 1.** Burada hiçbir şey türetilmiyor: iki bacak da aynı
  anda gerçekten ödenen fiyatlar, bu yüzden yalnızca bu sayfa **düzeltilmemiş** fiyat çeker. Geriye
  dönük düzeltilmiş seri son fiyatları şişirir ve ayrı ayrı düzeltilmiş iki piyasa
  karşılaştırılamaz — ICBC'nin A hissesi ekranda 8,28 iken düzeltilmiş seri 13,34 der: +26%'lık
  prim +245% olur.
- **Aynı fark iki yönde yazılır.** Bu sayfa, sektörde alışıldığı gibi A'yı H'ye göre verir: +194%,
  karadaki hissenin Hong Kong hissesinin neredeyse üç katı olduğu anlamına gelir. Bazı servisler
  aynı sayıyı ters yönde (溢价(H/A)) gösterir ve 新华制药 için aynı gün −66% yazar. Bu aynı
  gerçektir (1 ÷ (1 − 0,66) − 1 = 1,94); ne başka bir fiyat ne de hesap hatası.
- **Çizilen, primi en yüksek on beş çift**, bu yüzden çubuklar sağa büyür — on beşinci bile
  yüzde yirmiyi aşıyordu. Altmış dokuz çiftin yalnızca ikisi ters yönde, H hissesi A hissesinin
  üstünde, ve ikisi de listenin sonunda, karenin ulaşmadığı yerde.
- **Dönem uzadıkça giren şirket azalır.** Aday, tanıdık altmış dokuz çift kotasyondur; ancak iki
  bacağı da dönemin tamamını kapsayan çift çizilir: Hong Kong kotesi iki yıldan genç olan düşer.
- **Örnekleme aylık.** "En uzun" yaklaşık dokuz yıldır ve sınır, yalnızca 2016'ya uzanan kur
  serisidir. Üç bacak ayı farklı günlerde kapatır; bu yüzden tarihe göre kesişim alınmaz, takvim
  ayına göre gruplanır ve ayın son fiyatı alınır.
- **Liste gömülüdür.** İki kaynağın hiçbiri "hangi karadaki kotasyonun Hong Kong'da da kotasyonu
  var" sorusunu yanıtlamaz. Buna karşılık doğrulanabilir: her çift 2026-10-02'de kaynaktan yeniden
  okundu ve 海通证券 tam da bu kontrolün çıkardığı şirkettir (国泰海通 birleşmesinden sonra H
  hisseleri işlemden kaldırıldı).

## Aşırı günler

Tek bir enstrüman ve en çok hareket ettiği günler — büyüklüğe göre sıralanmış yatay
çubuklar. **Bu tablonun satırları şirket değil gündür**, buradaki başka hiçbir sayfa bunu yapmaz:
bir satırın değeri, o günün önceki işlem gününün kapanışına göre hareketidir ve o gün geçtiğinde
değer bir daha değişmez.

- **Hareket, düzeltilmiş kapanıştaki değişimdir.** Düzeltilmiş, çünkü temettü düşüm günü bir çöküş
  değildir: o sabah fiyat temettü kadar düşer ve düzeltilmemiş seri bu günü tarihin en büyük
  düşüşlerinin başına koyardı — oysa elinde tutan kimse bir şey kaybetmemiştir.
- **İşarete göre değil büyüklüğe göre sıralanır.** −%7,7 ile +%8,1 aynı büyüklükte hareketlerdir,
  bu yüzden yan yana dururlar; işaretli değere göre sıralamak her düşüşü her yükselişin altına
  koyardı. Çubuklar bu yüzden iki yana büyür: **yükseliş sağa, kırmızı; düşüş sola, yeşil**.
- **Bir gün ancak gerçekleştiğinde sıralamaya girer.** Dönemin en büyük yirmi dört hareketi
  adaydır, kare bunların en büyük on beşini çizer; bir gün kendi tarihi gelmeden sıralamaya katılmaz,
  bu yüzden tablo baştan dolu olmak yerine yıllar geçtikçe dolar.
- **Piyasanın kotasyon verdiği her enstrüman, sadece geniş endeksler değil.** Arama kutusuna bir
  kod, bir ad veya pinyin yazın: tek bir hisse ve borsada işlem gören bir fon bu tabloya bir endeks
  kadar uyar, alttaki liste ise yalnızca alışılmış olanlara bir kısayoldur. Piyasa değiştirmek
  listeyi değiştirir ve başka bir piyasanın enstrümanını geride bırakır; enstrüman veya aralık
  seçmek yalnızca bir tercih kaydeder — 取数'e basılana kadar hiçbir şey çekilmez.
- **En uzun dönem yaklaşık otuz beş yıldır**, bu kaynağın sınırıdır: bir istek yaklaşık 640 günlük
  bar taşır ve geriye yürüme en çok yirmi kez yapılır. Altmış işlem gününden kısa dönemler
  reddedilir — sakin bir ayın en büyük günü tabloya değer bir olgu değildir.
- **Karenin üstündeki tarih zaman eksenidir**, altındaki çubuk ilerlemedir. Başlık satırı dönemi,
  işlem günü sayısını ve aday gün sayısını taşır.

## Döviz koridorları

Her parite için bir satır, ve **satırın kendisi koridordur**: bir ucu paritenin seçilen
dönemde gördüğü en düşük seviye, diğeri en yüksek, işaret ise bugünkü kur. Bu tablo diğerlerine
benzemez — başka yerlerde çubuğun uzunluğu *ne kadar* der, burada satır her karede tüm genişliği
kaplar; hareket eden işaret ve çevresindeki koridordur.

- **Koridor genişler.** Duvarları tüm dönemin değil, **şimdiye kadarki** en düşük ve en yüksektir.
  Önceki tüm aylardan ileri giden bir ay duvarlardan birini dışa iter ve %100'deki bir parite bir
  sınırda değil, şimdiye kadarki en pahalı yerindedir.
- **Her parite kendi aralığıyla ölçülür.** USD/JPY'de 157,92 ile EUR/USD'de 1,1245 aynı ölçeğin
  üzerinde iki nokta değildir; altı pariteyi tek bir görüntüye sığdıran şey normalizasyondur. Bedeli,
  dar bir koridorla geniş bir koridorun aynı görünmesidir — bu yüzden iki uç her satırın altına
  yazılır.
- **Aylık mumlar, düzeltilmemiş.** Bir para biriminin düzeltilecek temettüsü veya bölünmesi yoktur ve
  sayfa kaynağa AH sayfasının gittiği ham yoldan gider.
- **Kapsam farklı, bu yüzden iki liste var**: USD/CNY 2005'e, diğer beş renminbi paritesi 2016'ya
  kadar uzanır; ana çaprazların hepsi 2005-07'de başlar ve 325 ay taşır. Tek tabloda okunacak şey,
  kaynağın her pariteyi ne zaman kotlamaya başladığı olurdu.
- **Piyasa ayarı burada geçmez**: bir para birimi çifti hiçbir borsaya ait değildir ve tablo, hangi
  piyasa seçilmiş olursa olsun aynıdır.
- En uzun dönem yaklaşık yirmi yıldır; bu kaynağın aylık kapsamıdır. On iki aydan kısa dönemler
  reddedilir — bu bir koridor değil, birkaç haftalık harekettir.

## Endeks yarışı

Her endeks için bir satır ve satır, **o endeksin aralıktaki kendi ilk ayından bu yana ne kadar
yol aldığıdır** — seviyesi değil. Shanghai Composite'ta 3.800 ile S&P 500'de 5.700 aynı ölçeğin iki
noktası değildir; seviyeleri çizmek, hangi endeksin saymaya nereden başladığı üzerine bir tablo
olurdu.

- **Geç gelen bir endeks, gelene kadar tabloda yoktur.** S&P 1950'ye, Dow yalnızca 2009'a uzanır ve
  Hang Seng Teknoloji endeksi 2020'de başlar. %0,00'de durmaz, hiç yoktur — orada dursaydı şimdiye
  kadar düşmüş her endeksin üstünde sıralanır ve 'hiçbir şey olmayan bir piyasa' gibi okunurdu.
- **Aylık, ve artık düzeltilmiş.** Bir endeks hiçbir şey dağıtmaz, ama bir hisse temettü öder ve
  paylarını böler: Apple on yılda düzeltilmemiş +193 %, düzeltilmiş +1183 % okur, çünkü
  düzeltilmemiş çizgi hiçbir yatırımcının düşmediği uçurumlar taşır. Endeksler bundan etkilenmez —
  düzeltme istendiğinde kaynak bir endekse her zamanki satırlarla yanıt verir ve on ikisi de iki
  yolda birebir aynı çıktı. Tablonun şimdi taşıdığı şey saklanacak değil söylenecek bir farktır:
  bir endeks satırı **fiyat** getirisidir, çünkü endeks bir pozisyon değildir; bir hisse satırı ise
  temettüleri ve bölünmeleri içine alan **toplam** getiridir.
- **Piyasa ayarı bu sayfayı yönetmez**: üç piyasayı birlikte okur, piyasa değişse de o değişmez.
  Anakaranın altısı, Hong Kong'un üçü, New York'un üçü veya on ikisi birden seçilebilir.
- En uzun dönem, kaynağın aylık tavanıyla sınırlıdır — 430 mum, yaklaşık otuz beş yıl; on iki aydan
  kısa dönemler reddedilir: bu uzun koşu değil, kısa mesafedir.
- **Ya da kendi listeniz.** Menünün son grubu kendi listenizdir: bir tane eklemek için kod, ad
  veya pinyin yazın; anakara, Hong Kong ve New York değerleri birlikte durabilir — bu tablo piyasa
  ayarını hiç sormaz. Dört tablo için tek liste: buraya eklenen bir hisse, varlık yarışında,
  geri çekilmelerde ve tutma başarısında da sunulur. Üçün altında çekme reddedilir.

## Varlık sınıfları

Her varlık sınıfı için bir satır ve satır, **onu tutmanın kazandırdığıdır** — kotasyonu değil.
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
- **Ya da kendi listeniz.** Menünün son grubu kendi listenizdir: bir tane eklemek için kod, ad
  veya pinyin yazın; üç piyasa burada karıştırılabilir. Dört tablo için tek liste: buraya eklenen
  bir hisse diğer üçünde de sunulur; sekiz fonla tamamen aynı şekilde düzeltilmiş çekilir, yani
  temettüler ve pay bölünmeleri sayının içindedir. Üçün altında çekme reddedilir.

## Tahvil piyasası

Her tahvil endeksi için bir satır ve çubuk bir **fiyat değişimi** — bu, elde tutmanın kazandırdığı
ile aynı şey değil.

- **Kupon sayıda yok.** Dokuz satır da endeks ve kaynak bir endeks için düzeltme parametresini
  yoksayıyor, dolayısıyla dönen şey kotasyon. Bir tahvil getirisinin çoğunu kupon olarak öder ve
  kupon hiçbir zaman kotasyonda görünmez: elinde tutan, bu tablonun gösterdiğinden fazlasını
  kazandı, hem de her satırda farklı bir tutarla.
- **Bilerek varlık sınıfı yarışının tersi.** O tablo, fon dağıttığı için düzeltilmiş seriden
  çizilir; bu tabloya dokunulmaz, çünkü endeks dağıtmaz. İki tablo birbirine karşı okunamaz.
- **Dokuz satır ve liste yerleşik**, sizin tuttuğunuz bir liste değil. CSI «tüm tahviller» endeksi
  istendi ve bu kaynakta yok: ona benzeyen kod Şanghay ayrılabilir tahvil endeksi ve aylık serisi
  Ağustos 2015'te duruyor; tüm endeks kod uzayının taranması da hiçbir toplam tahvil endeksi
  bulamadı. Bu yerler kaynağın yanıt verdiği en derin kredi endekslerine gitti.
- **Başlangıçlar farklı.** En eski satır 2003-02'de başlıyor, Shenzhen dönüştürülebilir endeksi ise
  ancak 2014-08'de; yani on yıllık tabloya beş yıl geç katılıyor. Henüz başlamamış bir satır yoktur,
  %0,00'de durmaz.
- **Aylık**, ayda bir çubuk, ve pazar ayarı bu sayfayı yönetmez. On iki aydan kısa dönemler
  reddedilir.
- **Aralıktaki ilk tam ayla başlar.** Kaynak yalnızca tam aylarla yanıt verir ve aylık çubuk *o* tam
  aydır: aralık ayın ortasında başlarsa bu eksik ay sayılmaz — tablo ondan sonraki tam ayla başlar.
  «Son 10 yıl»ın 120 değil 119 ay çizmesinin nedeni budur: eksik olan aralığın dışındadır.
  Başlıktaki iki tarih, gerçek başlangıç ve bitiş tarihleridir.
- **Üç grup**: dokuzu da, dönüştürülebilirler olmadan altı düz tahvil ve üç dönüştürülebilir.

## Düşüşler

Bir satır, **bir varlığın kendi zirvesinin ne kadar altında olduğudur** — ne kazandığı değil, onu
kazanmanın neye mal olduğu. Varlık sınıfları yarışındaki sekiz varlığın aynısı, ama birbirine karşı
değil kendine göre ölçülüyor.

- **Önemli olan eğri.** Bu uygulamanın geri kalanında bir değer uzunluk olarak çizilir ve uzunluk
  ancak o anda suyun ne kadar derin olduğunu söyleyebilir. Derinlik zaman içindeki bir biçimdir:
  dip ve ondan çıkış, eğrinin üzerindeki iki yerdir ve kare boyunca aralarındaki mesafe, arada geçen
  ay sayısıdır.
- **İki sayı birlikte artmaz.** Son on yılda Nasdaq fonu %25,52 düştü ve altı ayda yeniden eşit
  duruma geldi; CSI 500 fonu %56,07 düştü ve seksen altı ay sürdü. Tek sayı olarak basıldığında
  ikincisi, birincisinin ağırlaştırılmış hâli gibi görünür — ve değildir.
- **Tüm tablo için tek derinlik ölçeği.** Her satırı kendi en kötü anına göre ölçeklemek, para piyasası
  fonunun %0,2'sini CSI 500'ün %56'sı büyüklüğünde bir uçurum olarak çizerdi — oysa bu tablonun varlık
  sebebi tam olarak bu ikisinin karşılaştırılamayacağını söylemektir. Bu yüzden o satır, kendi zirve
  çizgisine yapışık düz bir çizgidir ve **o düzlük onun söylediği şeydir**.
- **Düzeltilmiş, aylık ve her varlığın kendi ilk ayından**, varlık sınıflarının verdiği gerekçelerle:
  bir fonun dağıtımları fiyatında hiç görünmez ve 2019'da katılan bir varlık, sahip olmadığı bir
  zirveye göre ölçülmez.
- **Satırlar hâlâ yarışıyor.** Kendi zirvelerinin ne kadar altında olduklarına göre sıralanırlar —
  zirvesine en yakın olan en üstte — ve aylar geçtikçe yer değiştirirler.
- **Altın ve emtia fonu ölçüm yapıldığında hâlâ suyun altındaydı** — tablo bu tür düşüşü açık olarak
  bildirir, çünkü aralık onarılmadan önce sona ermiştir.
- **Ya da kendi listeniz.** Menünün son grubu kendi listenizdir: bir tane eklemek için kod, ad
  veya pinyin yazın; üç piyasa burada karıştırılabilir. Dört tablo için tek liste: buraya eklenen
  bir hisse diğer üçünde de sunulur; sekiz fonla tamamen aynı şekilde düzeltilmiş çekilir, yani
  temettüler ve pay bölünmeleri sayının içindedir. Üçün altında çekme reddedilir.

Piyasa ayarına bağlı değil: sekizi de anakara borsasında kote. Aralıkta on iki aydan az varsa reddedilir.

## Tutma oranı

Bir satır, **kazançla biten tamamlanmış girişlerin payı** — aynı süre boyunca girilip tutulabilecek
tüm ayların içinde, artıda bitenlerin oranı. Varlık sınıfları yarışı ve düşüş tablosundaki aynı
sekiz varlık; puan, ne kadar kazandırdığına değil, elde tutmanın işe yarayıp yaramadığına göre
veriliyor.

- **Bir giriş şanstır; seksen dördü bir orandır.** Aralıktaki her ay bir giriştir ve hepsi aynı süre
  tutulur, dolayısıyla on yıl içindeki üç yıllık tutuş satır başına seksen dört giriştir, bir değil.
  Ayları paylaşırlar ve mesele tam olarak budur: onları üç bağımsız girişe indirmek, içinde üç
  gözlem olan bir oran bırakırdı.
- **Bir giriş, bittiği aydan itibaren sayılır.** Aralığın son üç yılında alınan henüz bitmemiştir;
  bitmemiş bir girişi zarar saymak, her satırı sonunda sırf takvim yüzünden aşağı büker. Bu yüzden
  tablo, bir girişin bitebileceği ilk ayda açılır.
- **Altı giriş tamamlandığında satır katılır.** Bir giriş ya %0 ya %100'dür ve bu iki sayıdan hangisi
  sıralamanın bir ucunda durursa dursun, o uç hak edilmiş bir uç değildir.
- **Düzeltilmiş, aylık ve her varlığın kendi ilk ayından**, varlık sınıflarının verdiği gerekçelerle:
  bir fonun dağıtımları fiyatında hiç görünmez ve 2019'da kurulan bir fonun kazanıp kaybedebileceği
  2016 girişi yoktur.
- **Tutma süresi bu tablonun tek yeni seçimi.** Aynı on yıl için bir yıl ile beş yıl farklı sorulardır
  ve farklı cevapları vardır; sekiz satır ikisi arasında yeniden sıralanır.
- **Satırlar hâlâ yarışıyor.** Oranlarına göre dizilirler — en sık artıda biten üstte — ve aylar
  geçtikçe yer değiştirirler.
- **Ya da kendi listeniz.** Menünün son grubu kendi listenizdir: bir tane eklemek için kod, ad
  veya pinyin yazın; üç piyasa burada karıştırılabilir. Dört tablo için tek liste: buraya eklenen
  bir hisse diğer üçünde de sunulur; sekiz fonla tamamen aynı şekilde düzeltilmiş çekilir, yani
  temettüler ve pay bölünmeleri sayının içindedir. Üçün altında çekme reddedilir.

Son on yılda üç yıllık tutuşla ölçüldüğünde: Nasdaq fonu seksen dört girişinin tamamında öndeydi,
Hong Kong fonu ise bunların yüzde kırkında — varlık sınıfları yarışının on yıllık toplam getiriyle
ayırdığı iki satırı bu tablo, "içeri girmek işe yaradı mı" ile ayırıyor.

Piyasa ayarına bağlı değil: sekizi de anakara borsasında kote. Aralıkta on iki aydan az varsa
reddedilir.

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
- 3, 5 ve 10 yıl ile en uzun aralığın dışında **Özel** de seçilebilir: başlangıç ve bitiş tarihini verip verileri alın. Yaklaşık 35 yıl geriye gidilebilir — kaynak istek başına yaklaşık 640 takvim günü veriyor ve tarama en çok yirmi istek yapıyor.

## Pozisyon Getirisi

![Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.](media/position.png)

Tek alım, uzun süre elde tutma — 2015'ten beri aynı varlıktan bir milyon — yılların değere ve getiriye ne yaptığını gösteren bir animasyon. Birkaç pozisyon aynı kareyi paylaşabilir: her birine bir çizgi, ucunda o anki kâr.

- Pozisyonlar **kendi listenizden** gelir; diğer tabloların da paylaştığı liste: bir kod ya da ad arayıp ekleyin, her chip'in anahtarı o pozisyonun bu karede olup olmadığını belirler, × ise onu paylaşılan listeden (ve dolayısıyla diğer tablolardan) çıkarır. Tek dokunuş satırı piyasaya göre değişir — ana kara için 中国平安 ve 贵州茅台, Hong Kong için 腾讯, 汇丰 ve 盈富基金, New York için Apple, Berkshire ve SPY — ve bir dokunuş o adı ekleyip hemen çizer.
- **Tek karede 2 ile 6 pozisyon.** Her biri aynı tutarla, kendi ilk işlem gününde bir kez alınır; böylece çizgiler doğrudan karşılaştırılabilir ve ikisi arasındaki mesafe her tarihte "parayı nereye koymak daha iyiydi" sorusunun cevabıdır. Tarih ekseni günlerinin birleşimidir: sonra işlem görmeye başlayan varlık yalnızca daha sonra başlar ve öncesinde maliyet çizgisi boyunca düz çizilmek yerine hiç görünmez. Sınır altıdır — üstünde getirme, birkaçını sessizce çizmek yerine reddeder — ve başka bir piyasadan pozisyon dışarıda kalır, çünkü buradaki tutarlar geçerli piyasanın para birimidir.
- **Sayı çizgiyle birlikte gider.** Her pozisyonun ucundaki etiket onu adlandırır ve o andaki kâr tutarını verir; animasyonla birlikte hareket eder — çubuğu çekin, çizgiyle birlikte gider. Tek pozisyonda ortadaki büyük sayı yine yüzde getiridir; birkaç pozisyonda **öndeki**nin kâr tutarına dönüşür, altında o varlığın adı yazar ve kapanış kartları tek bir varlığı anlatan dört sayı yerine her pozisyon için birer kart olur.
- Başlangıç sermayesi ve elde tutma süresi size ait; süre üç, beş veya on yıl olabilir, ya da verilerin yettiği kadar (yaklaşık on üç yıl).
- Getiri geriye düzeltilmiş kapanışlarla — temettüler yeniden yatırıldı, ücretsiz — hesaplanır. Geriye düzeltme halka arzın ilk gününe demir atar ve temettüleri ileriye biriktirir, böylece cömert bir ödeyicinin ilk yılları asla negatif olmaz; ileriye düzeltmede bu olabilir.
- Aynı **Özel** aralık elde tutma için de geçerlidir: iki tarih verip verileri alın. Araç belirttiğiniz tarihten sonra işlem görmeye başladıysa, elde tutma ilk işlem gününde başlar.
- **İki ilerleme biçimi.** *Aralığın tamamı* tüm dönemi bir anda serer; eğrinin ekrandaki biçimi, zamandaki biçimidir. *Kayan pencere* sabit sayıda işlem gününden oluşan bir pencereyi aralığın başından sonuna kadar yürütür — uzun bir günlük serinin dalgalanmalarını okunur tutmanın tek yolu budur, çünkü on iki yıla yayılmış üç aylık bir düşüş iki pikseldir. Pencere yalnızca kaydırırken anlam taşır ve iki biçim de **aynı fiyatları** okur — geçiş yeniden veri çekmez.

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

- Opaklık kaydırıcısı iki rengin ne kadarının kullanılacağını belirler: %100'de kare seçilen ikilinin kendisidir, altında sayfanın kendi koyu gradyanı alttan görünür. Açık bir ikiliyi okunur tutan şey budur.

- Resim seçmek pencere arka planındaki gibi işler: bilgisayarınızdan bir resim ya da Windows ile gelen bir duvar kağıdı. Seçtiğiniz resim uygulamanın klasörüne kopyalanır.

- Resim kareyi doldurur, artan kısım kırpılır; oranları asla bozulmaz.

- Karartma sürgüsü, resmin sayfanın kendi arka planına ne kadar geri çekileceğini belirler: %20 ile %95 arası.

## Veri ve söylemeyecekleri

Fiyatlar Tencent Finance'in herkese açık uç noktalarından gelir ve kare kaynağı her zaman belirtir. Bu videolar zaten gerçekleşmiş işlemleri anlatır. Yalnızca bilgi amaçlıdır ve yatırım tavsiyesi değildir.

- İşlem hacmi yüz milyon yuan birimine çevrilir ve sayılar gerektirdiğinde işlem miktarı daha büyük bir birime geçer, böylece eksen okunabilir kalır.
- Tutarlar yüz milyonlara çevrilir — anakara ve Hong Kong’da yuan, ABD’de dolar. Her piyasa kendi para birimini korur.
- Bir isteğin döndürebileceğinden uzun bir aralık sessizce kısaltılmaz, reddedilir: günlükte yaklaşık 900 takvim günü, sayfa sayfa geri giden mum sayfasında yaklaşık on beş yıl ve aylıkta tüm geçmiş. Sessizce kısaltmak en kötü sonuçtur — eksilen kısım **başlangıçtır** ve ilk yılları çıkmış bir grafik, tamamen normal görünen daha kısa bir grafiktir.

## Güncelleme

Microsoft Store'da daha yeni bir sürüm olduğunda gezinti bölmesinde Ayarlar'ın yanında bir **Güncelle** düğmesi görünür; tek tıkla kurulur.

- Yalnızca Store'da gerçekten daha yeni bir sürüm varsa görünür. Geliştirme veya yandan yüklenmiş bir derlemede hiç görünmez, bu normaldir.
- Yükleme sırasında uygulama kapanır ve yeni sürümle yeniden başlar, düğme kaybolur. Dışa aktarma sürüyorsa önce sorar.
- Kurulamazsa nedenini söyler — yalnızca Wi-Fi, pil çok düşük — ve güncelleme Microsoft Store'dan da kurulabilir.

## Bir sorun mu var?

gaqo@outlook.com adresine yazın ve ne yaptığınızı, bunun yerine ne beklediğinizi belirtin. Sürüm numarası ayarlar sayfasındadır.
