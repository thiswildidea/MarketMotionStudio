# -*- coding: utf-8 -*-
"""Adds the portfolio page's strings to all fourteen resource files.

The page is the first one here whose bookkeeping is the reader's own data, so it needs
strings for three surfaces at once: the page, the holdings dialog, the import dialog —
and, in the renderer, the words that are drawn into the video.

Run it again after editing a translation: it removes the keys it owns and appends them
in order, so the file never accumulates two copies and the fourteen files never drift
apart in key order.
"""
import codecs
import hashlib
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src", "MarketMotionStudio", "Strings")

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "es", "it", "pl", "pt-BR", "cs", "ru", "tr"]

# Key, then one value per language in LANGS order.
ENTRIES = [
    ("NavPortfolioPnl.Content", (
        "实时持仓收益", "即時持倉收益", "Live portfolio P&L", "リアルタイム保有損益", "실시간 보유 손익",
        "Depot live", "P&L en direct", "P&L en vivo", "P&L in tempo reale", "Wynik na żywo",
        "P&L ao vivo", "Výsledek živě", "Портфель онлайн", "Canlı portföy")),

    ("PortfolioPnlPageTitle.Text", (
        "实时持仓收益", "即時持倉收益", "Live portfolio P&L", "リアルタイム保有損益", "실시간 보유 손익",
        "Depot live", "P&L en direct", "P&L en vivo", "P&L in tempo reale", "Wynik na żywo",
        "P&L ao vivo", "Výsledek živě", "Портфель онлайн", "Canlı portföy")),

    ("PortfolioPnlPageSubtitle.Text", (
        "当天 9:30 到收盘的持仓收益曲线，逐分钟刷新；持仓可手工维护，成交记录每天导入",
        "當天 9:30 到收盤的持倉收益曲線，逐分鐘刷新；持倉可手動維護，成交紀錄每天匯入",
        "Your holdings' profit and loss from 09:30 to the close, minute by minute — kept by hand, updated by importing each day's filled orders",
        "当日 9:30 から大引けまでの保有損益を1分ごとに表示。保有銘柄は手入力、約定履歴は毎日取り込みます",
        "당일 9:30부터 장 마감까지 보유 손익을 1분 단위로 표시합니다. 보유 종목은 직접 관리하고 체결 내역은 매일 가져옵니다",
        "Der Gewinn Ihrer Positionen von 09:30 bis zum Schluss, Minute für Minute – von Hand gepflegt, täglich um die Ausführungen ergänzt",
        "Le résultat de vos positions de 09:30 à la clôture, minute par minute — tenu à la main, complété chaque jour par les exécutions",
        "El resultado de sus posiciones desde las 09:30 hasta el cierre, minuto a minuto: a mano, con las ejecuciones de cada día",
        "Il risultato delle tue posizioni dalle 09:30 alla chiusura, minuto per minuto: a mano, con le esecuzioni di ogni giorno",
        "Wynik Twoich pozycji od 09:30 do zamknięcia, minuta po minucie — prowadzony ręcznie, uzupełniany codziennie transakcjami",
        "O resultado das suas posições das 09:30 ao fechamento, minuto a minuto — mantido à mão e completado pelas execuções de cada dia",
        "Výsledek vašich pozic od 09:30 do zavření, minutu po minutě — vedený ručně a doplňovaný denními obchody",
        "Результат ваших позиций с 09:30 до закрытия, минута за минутой — ведётся вручную и пополняется сделками за день",
        "09:30'dan kapanışa kadar pozisyonlarınızın kârı, dakika dakika — elle tutulur, her gün işlemlerle güncellenir")),

    ("PortfolioPnlSection.Text", (
        "持仓", "持倉", "Holdings", "保有銘柄", "보유 종목",
        "Bestand", "Positions", "Posiciones", "Posizioni", "Pozycje",
        "Posições", "Pozice", "Позиции", "Pozisyonlar")),

    ("PortfolioPnlEmpty.Text", (
        "还没有持仓。点「管理持仓」，按代码添加一只。",
        "還沒有持倉。點「管理持倉」，按代碼新增一檔。",
        "No holdings yet. Open Manage holdings and add one by code.",
        "まだ保有銘柄がありません。「保有銘柄の管理」からコードで追加してください。",
        "아직 보유 종목이 없습니다. '보유 종목 관리'에서 코드로 추가하세요.",
        "Noch keine Positionen. Über „Bestand verwalten“ eine per Kennung hinzufügen.",
        "Aucune position. Ouvrez « Gérer les positions » et ajoutez-en une par code.",
        "Aún no hay posiciones. Abra «Gestionar posiciones» y añada una por código.",
        "Nessuna posizione. Apri «Gestisci posizioni» e aggiungine una per codice.",
        "Brak pozycji. Otwórz „Zarządzaj pozycjami” i dodaj jedną po kodzie.",
        "Ainda não há posições. Abra «Gerenciar posições» e adicione uma por código.",
        "Zatím žádné pozice. Otevřete „Spravovat pozice“ a přidejte ji podle kódu.",
        "Позиций пока нет. Откройте «Управление позициями» и добавьте по коду.",
        "Henüz pozisyon yok. «Pozisyonları yönet» ile kodla ekleyin.")),

    ("PortfolioPnlManage.Content", (
        "管理持仓", "管理持倉", "Manage holdings", "保有銘柄の管理", "보유 종목 관리",
        "Bestand verwalten", "Gérer les positions", "Gestionar posiciones", "Gestisci posizioni",
        "Zarządzaj pozycjami", "Gerenciar posições", "Spravovat pozice", "Управление позициями",
        "Pozisyonları yönet")),

    ("PortfolioPnlImport.Content", (
        "导入成交", "匯入成交", "Import trades", "約定を取り込む", "체결 내역 가져오기",
        "Ausführungen importieren", "Importer des exécutions", "Importar ejecuciones",
        "Importa esecuzioni", "Importuj transakcje", "Importar execuções", "Importovat obchody",
        "Импорт сделок", "İşlemleri içe aktar")),

    ("PortfolioPnlAutoRefresh.Content", (
        "开盘时自动刷新", "開盤時自動刷新", "Refresh while open", "取引時間中は自動更新",
        "장중 자동 새로고침", "In der Sitzung aktualisieren", "Actualiser en séance",
        "Actualizar en sesión", "Aggiorna in seduta", "Odświeżaj w sesji", "Atualizar no pregão",
        "Obnovovat v seanci", "Обновлять в сессию", "Seans içinde yenile")),

    ("PortfolioPnlNote.Text", (
        "收益按「昨收 → 现价」计算，含当日已成交部分，不含手续费；港股按即时汇率折算成人民币。",
        "收益按「昨收 → 現價」計算，含當日已成交部分，不含手續費；港股按即時匯率折算成人民幣。",
        "Profit is measured from yesterday's close to the live price, includes today's filled trades and excludes fees. Hong Kong holdings are converted to yuan at the live rate.",
        "損益は「前日終値 → 現在値」で計算し、当日の約定分を含みます。手数料は含みません。香港銘柄はリアルタイムのレートで人民元に換算します。",
        "손익은 '전일 종가 → 현재가'로 계산하며 당일 체결분을 포함하고 수수료는 제외합니다. 홍콩 종목은 실시간 환율로 위안화 환산합니다.",
        "Der Gewinn wird vom Vortagsschluss bis zum aktuellen Kurs gemessen, enthält die heutigen Ausführungen und keine Gebühren. Hongkong-Positionen werden zum aktuellen Kurs in Yuan umgerechnet.",
        "Le résultat est mesuré de la clôture de la veille au cours actuel, inclut les exécutions du jour et exclut les frais. Les positions de Hong Kong sont converties en yuan au taux du jour.",
        "El resultado se mide del cierre de ayer al precio actual, incluye las ejecuciones del día y excluye las comisiones. Las posiciones de Hong Kong se convierten a yuanes al tipo actual.",
        "Il risultato è misurato dalla chiusura di ieri al prezzo attuale, include le esecuzioni del giorno ed esclude le commissioni. Le posizioni di Hong Kong sono convertite in yuan al cambio corrente.",
        "Wynik liczony jest od wczorajszego zamknięcia do bieżącej ceny, obejmuje dzisiejsze transakcje i nie obejmuje opłat. Pozycje z Hongkongu przeliczane są na juany po bieżącym kursie.",
        "O resultado é medido do fechamento de ontem ao preço atual, inclui as execuções do dia e exclui as taxas. As posições de Hong Kong são convertidas para yuan pela taxa atual.",
        "Výsledek se měří od včerejšího zavření k aktuální ceně, zahrnuje dnešní obchody a nezahrnuje poplatky. Pozice z Hongkongu se přepočítávají na jüany aktuálním kurzem.",
        "Результат считается от вчерашнего закрытия до текущей цены, включает сегодняшние сделки и не включает комиссии. Позиции Гонконга пересчитываются в юани по текущему курсу.",
        "Kâr, dünkü kapanıştan güncel fiyata göre ölçülür; günün gerçekleşen işlemlerini içerir, komisyonları içermez. Hong Kong pozisyonları güncel kurdan yuan cinsine çevrilir.")),

    ("PortfolioPnlRowDetail", (
        "{0} 股 · 成本 {1}", "{0} 股 · 成本 {1}", "{0} shares · cost {1}", "{0} 株 · 取得単価 {1}",
        "{0}주 · 단가 {1}", "{0} Stück · Einstand {1}", "{0} titres · prix de revient {1}",
        "{0} títulos · coste {1}", "{0} titoli · costo {1}", "{0} szt. · koszt {1}",
        "{0} ações · custo {1}", "{0} ks · cena {1}", "{0} шт. · стоимость {1}", "{0} adet · maliyet {1}")),

    ("PortfolioPnlRowClosed", (
        "休市", "休市", "Closed", "休場", "휴장", "Geschlossen", "Clôturé", "Cerrado", "Chiuso",
        "Zamknięte", "Fechado", "Zavřeno", "Закрыто", "Kapalı")),

    ("PortfolioPnlFetched", (
        "{0} · {1} 个分钟点 · 收益 {2}", "{0} · {1} 個分鐘點 · 收益 {2}",
        "{0} · {1} minute points · P&L {2}", "{0} · {1} 分足 · 損益 {2}", "{0} · {1}개 분봉 · 손익 {2}",
        "{0} · {1} Minutenpunkte · P&L {2}", "{0} · {1} points minute · P&L {2}",
        "{0} · {1} puntos por minuto · P&L {2}", "{0} · {1} punti minuto · P&L {2}",
        "{0} · {1} punktów minutowych · wynik {2}", "{0} · {1} pontos por minuto · P&L {2}",
        "{0} · {1} minutových bodů · výsledek {2}", "{0} · {1} минутных точек · результат {2}",
        "{0} · {1} dakika noktası · P&L {2}")),

    ("PortfolioPnlFetchFailed", (
        "取数失败：{0}", "取數失敗：{0}", "Fetch failed: {0}", "取得に失敗しました：{0}",
        "데이터를 가져오지 못했습니다: {0}", "Abruf fehlgeschlagen: {0}", "Échec de la récupération : {0}",
        "Error al obtener: {0}", "Recupero non riuscito: {0}", "Nie udało się pobrać: {0}",
        "Falha ao obter: {0}", "Načtení selhalo: {0}", "Не удалось получить: {0}",
        "Getirme başarısız: {0}")),

    ("PortfolioPnlUpdated", (
        "最后更新 {0}", "最後更新 {0}", "Updated {0}", "最終更新 {0}", "마지막 갱신 {0}",
        "Zuletzt aktualisiert {0}", "Mis à jour {0}", "Actualizado {0}", "Aggiornato {0}",
        "Zaktualizowano {0}", "Atualizado {0}", "Aktualizováno {0}", "Обновлено {0}", "Güncellendi {0}")),

    ("PortfolioPnlImported", (
        "已导入 {0} 笔成交（重复 {1} 笔，无对应持仓 {2} 笔）",
        "已匯入 {0} 筆成交（重複 {1} 筆，無對應持倉 {2} 筆）",
        "Imported {0} trades ({1} duplicates, {2} without a position)",
        "{0} 件の約定を取り込みました（重複 {1} 件、保有なし {2} 件）",
        "체결 {0}건을 가져왔습니다(중복 {1}건, 보유 없음 {2}건)",
        "{0} Ausführungen importiert ({1} Duplikate, {2} ohne Position)",
        "{0} exécutions importées ({1} doublons, {2} sans position)",
        "{0} ejecuciones importadas ({1} duplicadas, {2} sin posición)",
        "{0} esecuzioni importate ({1} duplicate, {2} senza posizione)",
        "Zaimportowano {0} transakcji ({1} duplikatów, {2} bez pozycji)",
        "{0} execuções importadas ({1} duplicadas, {2} sem posição)",
        "Importováno {0} obchodů ({1} duplicit, {2} bez pozice)",
        "Импортировано сделок: {0} (дубликатов {1}, без позиции {2})",
        "{0} işlem içe aktarıldı ({1} yinelenen, {2} pozisyonsuz)")),

    ("PortfolioPnlTitle", (
        "实时持仓收益", "即時持倉收益", "Live portfolio P&L", "リアルタイム保有損益", "실시간 보유 손익",
        "Depot live", "P&L en direct", "P&L en vivo", "P&L in tempo reale", "Wynik na żywo",
        "P&L ao vivo", "Výsledek živě", "Портфель онлайн", "Canlı portföy")),

    ("PortfolioPnlSubtitle", (
        "{0} · {1} 只持仓", "{0} · {1} 檔持倉", "{0} · {1} holdings", "{0} · {1} 銘柄",
        "{0} · {1}종목", "{0} · {1} Positionen", "{0} · {1} positions", "{0} · {1} posiciones",
        "{0} · {1} posizioni", "{0} · {1} pozycji", "{0} · {1} posições", "{0} · {1} pozic",
        "{0} · позиций: {1}", "{0} · {1} pozisyon")),

    ("PortfolioPnlTradesLine", (
        "截至 {0} · 成交 {1} 笔", "截至 {0} · 成交 {1} 筆", "to {0} · {1} trades",
        "{0} 時点 · 約定 {1} 件", "{0} 기준 · 체결 {1}건", "bis {0} · {1} Ausführungen",
        "jusqu'à {0} · {1} exécutions", "hasta {0} · {1} ejecuciones", "fino alle {0} · {1} esecuzioni",
        "do {0} · {1} transakcji", "até {0} · {1} execuções", "do {0} · {1} obchodů",
        "до {0} · сделок: {1}", "{0} itibarıyla · {1} işlem")),

    ("PortfolioPnlValueLine", (
        "市值 {0}", "市值 {0}", "value {0}", "評価額 {0}", "평가액 {0}", "Wert {0}", "valeur {0}",
        "valor {0}", "valore {0}", "wartość {0}", "valor {0}", "hodnota {0}", "стоимость {0}",
        "değer {0}")),

    ("PortfolioPnlStatReturn", (
        "收益率", "收益率", "Return", "収益率", "수익률", "Rendite", "Rendement", "Rentabilidad",
        "Rendimento", "Stopa zwrotu", "Retorno", "Výnos", "Доходность", "Getiri")),

    ("PortfolioPnlStatValue", (
        "持仓市值", "持倉市值", "Position value", "保有評価額", "보유 평가액", "Depotwert",
        "Valeur des positions", "Valor de la cartera", "Valore posizioni", "Wartość pozycji",
        "Valor da carteira", "Hodnota pozic", "Стоимость портфеля", "Pozisyon değeri")),

    ("PortfolioPnlStatHigh", (
        "最高", "最高", "High", "最高", "최고", "Hoch", "Plus haut", "Máximo", "Massimo",
        "Szczyt", "Máxima", "Maximum", "Максимум", "En yüksek")),

    ("PortfolioPnlStatLow", (
        "最低", "最低", "Low", "最低", "최저", "Tief", "Plus bas", "Mínimo", "Minimo",
        "Dno", "Mínima", "Minimum", "Минимум", "En düşük")),

    ("PortfolioPnlNoon", (
        "午间休市", "午間休市", "Lunch break", "昼休み", "점심 휴장", "Mittagspause",
        "Pause de midi", "Pausa del mediodía", "Pausa pranzo", "Przerwa południowa",
        "Pausa do almoço", "Polední pauza", "Обеденный перерыв", "Öğle arası")),

    ("PortfolioPnlRateNote", (
        "港股按 1 HKD = {0} CNY 折算", "港股按 1 HKD = {0} CNY 折算",
        "HKD converted at 1 HKD = {0} CNY", "香港株は 1 HKD = {0} CNY で換算",
        "홍콩 종목은 1 HKD = {0} CNY로 환산", "HKD umgerechnet mit 1 HKD = {0} CNY",
        "HKD converti à 1 HKD = {0} CNY", "HKD convertido a 1 HKD = {0} CNY",
        "HKD convertito a 1 HKD = {0} CNY", "HKD przeliczone po 1 HKD = {0} CNY",
        "HKD convertido a 1 HKD = {0} CNY", "HKD přepočteno 1 HKD = {0} CNY",
        "HKD пересчитан: 1 HKD = {0} CNY", "HKD 1 HKD = {0} CNY ile çevrildi")),

    ("PortfolioEmpty", (
        "还没有持仓：先在「管理持仓」里添加一只。",
        "還沒有持倉：先在「管理持倉」裡新增一檔。",
        "No holdings yet — add one in Manage holdings.",
        "まだ保有銘柄がありません。「保有銘柄の管理」から追加してください。",
        "아직 보유 종목이 없습니다. '보유 종목 관리'에서 추가하세요.",
        "Noch keine Positionen — über „Bestand verwalten“ hinzufügen.",
        "Aucune position — ajoutez-en une dans « Gérer les positions ».",
        "Aún no hay posiciones: añada una en «Gestionar posiciones».",
        "Nessuna posizione: aggiungine una in «Gestisci posizioni».",
        "Brak pozycji — dodaj ją w „Zarządzaj pozycjami”.",
        "Ainda não há posições — adicione uma em «Gerenciar posições».",
        "Zatím žádné pozice — přidejte ji ve „Spravovat pozice“.",
        "Позиций пока нет — добавьте в «Управлении позициями».",
        "Henüz pozisyon yok — «Pozisyonları yönet» ile ekleyin.")),

    ("PortfolioNoSession", (
        "行情源没有返回任何交易会话，稍后再试。",
        "行情源沒有回傳任何交易時段，稍後再試。",
        "The source returned no trading session. Try again later.",
        "取引セッションが取得できませんでした。しばらくしてからお試しください。",
        "거래 세션을 가져오지 못했습니다. 잠시 후 다시 시도하세요.",
        "Die Quelle lieferte keine Handelssitzung. Später erneut versuchen.",
        "La source n'a renvoyé aucune séance. Réessayez plus tard.",
        "La fuente no devolvió ninguna sesión. Inténtelo más tarde.",
        "La fonte non ha restituito alcuna sessione. Riprova più tardi.",
        "Źródło nie zwróciło sesji. Spróbuj później.",
        "A fonte não retornou nenhuma sessão. Tente mais tarde.",
        "Zdroj nevrátil žádnou seanci. Zkuste to později.",
        "Источник не вернул ни одной сессии. Повторите позже.",
        "Kaynak hiç seans döndürmedi. Sonra tekrar deneyin.")),

    ("PortfolioFxFailed", (
        "取不到港元汇率，无法把港股持仓折成人民币。",
        "取不到港元匯率，無法把港股持倉折成人民幣。",
        "The HKD rate could not be read, so Hong Kong holdings cannot be converted to yuan.",
        "香港ドルのレートが取得できず、香港銘柄を人民元に換算できません。",
        "홍콩 달러 환율을 가져오지 못해 홍콩 종목을 위안화로 환산할 수 없습니다.",
        "Der HKD-Kurs war nicht abrufbar; Hongkong-Positionen lassen sich nicht in Yuan umrechnen.",
        "Le taux HKD est indisponible : les positions de Hong Kong ne peuvent pas être converties en yuan.",
        "No se pudo leer el tipo HKD, así que las posiciones de Hong Kong no se pueden convertir a yuanes.",
        "Il cambio HKD non è disponibile: le posizioni di Hong Kong non possono essere convertite in yuan.",
        "Nie udało się odczytać kursu HKD, więc pozycji z Hongkongu nie można przeliczyć na juany.",
        "Não foi possível ler a taxa do HKD, então as posições de Hong Kong não podem ser convertidas para yuan.",
        "Kurz HKD se nepodařilo načíst, takže pozice z Hongkongu nelze přepočítat na jüany.",
        "Курс HKD недоступен, поэтому позиции Гонконга нельзя пересчитать в юани.",
        "HKD kuru okunamadı; Hong Kong pozisyonları yuan cinsine çevrilemiyor.")),

    ("PortfolioFetchingQuotes", (
        "正在读取昨收与现价…", "正在讀取昨收與現價…", "Reading yesterday's close and the live price…",
        "前日終値と現在値を読み込み中…", "전일 종가와 현재가를 읽는 중…",
        "Vortagsschluss und aktueller Kurs werden gelesen…", "Lecture de la clôture de la veille et du cours actuel…",
        "Leyendo el cierre de ayer y el precio actual…", "Lettura della chiusura di ieri e del prezzo attuale…",
        "Odczyt wczorajszego zamknięcia i bieżącej ceny…", "Lendo o fechamento de ontem e o preço atual…",
        "Načítá se včerejší zavření a aktuální cena…", "Читаем вчерашнее закрытие и текущую цену…",
        "Dünkü kapanış ve güncel fiyat okunuyor…")),

    ("PortfolioFetchingRates", (
        "正在读取 {0} 的分钟价…", "正在讀取 {0} 的分鐘價…", "Reading {0}'s minute prices…",
        "{0} の分足を読み込み中…", "{0}의 분봉을 읽는 중…", "Minutenkurse von {0} werden gelesen…",
        "Lecture des cours minute de {0}…", "Leyendo los precios por minuto de {0}…",
        "Lettura dei prezzi minuto di {0}…", "Odczyt cen minutowych {0}…",
        "Lendo os preços por minuto de {0}…", "Načítají se minutové ceny {0}…",
        "Читаем минутные цены {0}…", "{0} için dakika fiyatları okunuyor…")),

    ("PortfolioFetchingMinutes", (
        "已读取 {0}/{1} 只", "已讀取 {0}/{1} 檔", "{0}/{1} instruments read", "{0}/{1} 銘柄を読み込みました",
        "{0}/{1}종목 읽음", "{0}/{1} Positionen gelesen", "{0}/{1} positions lues",
        "{0}/{1} posiciones leídas", "{0}/{1} posizioni lette", "Odczytano {0}/{1} pozycji",
        "{0}/{1} posições lidas", "Načteno {0}/{1} pozic", "Прочитано позиций: {0}/{1}",
        "{0}/{1} pozisyon okundu")),

    ("PortfolioDialogTitle", (
        "持仓", "持倉", "Holdings", "保有銘柄", "보유 종목", "Bestand", "Positions", "Posiciones",
        "Posizioni", "Pozycje", "Posições", "Pozice", "Позиции", "Pozisyonlar")),

    ("PortfolioDialogClose", (
        "关闭", "關閉", "Close", "閉じる", "닫기", "Schließen", "Fermer", "Cerrar", "Chiudi",
        "Zamknij", "Fechar", "Zavřít", "Закрыть", "Kapat")),

    ("PortfolioDialogHint", (
        "按代码添加；数量与成本照券商 App 填。成本是摊薄成本：买入会摊高，卖出盈利会摊低。",
        "按代碼新增；數量與成本照券商 App 填。成本是攤薄成本：買入會攤高，賣出獲利會攤低。",
        "Add by code; enter the size and cost your broker shows. Cost is diluted: a purchase raises it, a profitable sale lowers it.",
        "コードで追加します。数量と取得単価は証券アプリの表示どおりに入力してください。単価は希薄化後（買いで上がり、利益のある売りで下がる）です。",
        "코드로 추가하고, 수량과 단가는 증권 앱에 표시된 값으로 입력하세요. 단가는 희석 단가입니다(매수 시 상승, 이익 매도 시 하락).",
        "Per Kennung hinzufügen; Stück und Einstand so eintragen, wie die Broker-App sie zeigt. Der Einstand ist verwässert: ein Kauf hebt ihn, ein Verkauf mit Gewinn senkt ihn.",
        "Ajout par code ; saisissez la quantité et le prix de revient affichés par le courtier. Le prix est dilué : un achat le relève, une vente gagnante le baisse.",
        "Añada por código; introduzca la cantidad y el coste que muestra el bróker. El coste es diluido: una compra lo sube, una venta con beneficio lo baja.",
        "Aggiungi per codice; inserisci quantità e costo come li mostra il broker. Il costo è diluito: un acquisto lo alza, una vendita in utile lo abbassa.",
        "Dodaj po kodzie; podaj liczbę sztuk i koszt tak, jak pokazuje je aplikacja brokera. Koszt jest rozwodniony: zakup go podnosi, zyskowna sprzedaż obniża.",
        "Adicione por código; informe a quantidade e o custo como o broker mostra. O custo é diluído: uma compra o sobe, uma venda com lucro o abaixa.",
        "Přidejte podle kódu; zadejte počet kusů a cenu tak, jak je ukazuje aplikace brokera. Cena je zředěná: nákup ji zvyšuje, ziskový prodej snižuje.",
        "Добавьте по коду; количество и стоимость вводите как в приложении брокера. Стоимость разводнённая: покупка её повышает, прибыльная продажа понижает.",
        "Kodla ekleyin; adet ve maliyeti aracı kurumun gösterdiği gibi girin. Maliyet seyreltilmiştir: alım yükseltir, kârlı satış düşürür.")),

    ("PortfolioDialogAdd", (
        "添加一只", "新增一檔", "Add a holding", "銘柄を追加", "종목 추가", "Position hinzufügen",
        "Ajouter une position", "Añadir una posición", "Aggiungi una posizione", "Dodaj pozycję",
        "Adicionar uma posição", "Přidat pozici", "Добавить позицию", "Pozisyon ekle")),

    ("PortfolioDialogCode.PlaceholderText", (
        "代码，如 600519 / 01024", "代碼，如 600519 / 01024", "Code, e.g. 600519 / 01024",
        "コード（例：600519 / 01024）", "코드(예: 600519 / 01024)", "Kennung, z. B. 600519 / 01024",
        "Code, ex. 600519 / 01024", "Código, p. ej. 600519 / 01024", "Codice, es. 600519 / 01024",
        "Kod, np. 600519 / 01024", "Código, ex. 600519 / 01024", "Kód, např. 600519 / 01024",
        "Код, напр. 600519 / 01024", "Kod, ör. 600519 / 01024")),

    ("PortfolioDialogShares.PlaceholderText", (
        "数量", "數量", "Shares", "数量", "수량", "Stück", "Quantité", "Cantidad", "Quantità",
        "Liczba sztuk", "Quantidade", "Počet kusů", "Количество", "Adet")),

    ("PortfolioDialogCost.PlaceholderText", (
        "成本", "成本", "Cost", "取得単価", "단가", "Einstand", "Prix de revient", "Coste",
        "Costo", "Koszt", "Custo", "Cena", "Стоимость", "Maliyet")),

    ("PortfolioDialogAddButton.Content", (
        "添加", "新增", "Add", "追加", "추가", "Hinzufügen", "Ajouter", "Añadir", "Aggiungi",
        "Dodaj", "Adicionar", "Přidat", "Добавить", "Ekle")),

    ("PortfolioDialogRemove", (
        "移除 {0}", "移除 {0}", "Remove {0}", "{0} を削除", "{0} 삭제", "{0} entfernen",
        "Retirer {0}", "Quitar {0}", "Rimuovi {0}", "Usuń {0}", "Remover {0}", "Odebrat {0}",
        "Удалить {0}", "{0} kaldır")),

    ("PortfolioDialogBadCode", (
        "代码看不懂：6 位是沪深京，5 位是港股。",
        "代碼看不懂：6 位是滬深京，5 位是港股。",
        "That code is not readable: six digits is a mainland listing, five is Hong Kong.",
        "コードを読み取れません。6桁は中国本土、5桁は香港です。",
        "코드를 읽을 수 없습니다. 6자리는 중국 본토, 5자리는 홍콩입니다.",
        "Kennung nicht lesbar: sechs Ziffern sind Festland, fünf Hongkong.",
        "Code illisible : six chiffres = continent, cinq = Hong Kong.",
        "Código ilegible: seis dígitos es continental, cinco es Hong Kong.",
        "Codice illeggibile: sei cifre è Cina continentale, cinque è Hong Kong.",
        "Nieczytelny kod: sześć cyfr to kontynent, pięć to Hongkong.",
        "Código ilegível: seis dígitos é continente, cinco é Hong Kong.",
        "Kód nelze přečíst: šest číslic je pevnina, pět Hongkong.",
        "Код не читается: шесть цифр — материковый рынок, пять — Гонконг.",
        "Kod okunamadı: altı hane anakara, beş hane Hong Kong.")),

    ("PortfolioDialogBadNumbers", (
        "数量要大于 0，成本不能为负。", "數量要大於 0，成本不能為負。",
        "Shares must be above zero and cost cannot be negative.",
        "数量は 0 より大きく、単価は負にできません。",
        "수량은 0보다 커야 하고 단가는 음수일 수 없습니다.",
        "Stück muss über null liegen, der Einstand darf nicht negativ sein.",
        "La quantité doit être positive et le prix ne peut pas être négatif.",
        "La cantidad debe ser mayor que cero y el coste no puede ser negativo.",
        "La quantità deve essere maggiore di zero e il costo non può essere negativo.",
        "Liczba sztuk musi być większa od zera, koszt nie może być ujemny.",
        "A quantidade deve ser maior que zero e o custo não pode ser negativo.",
        "Počet kusů musí být větší než nula, cena nesmí být záporná.",
        "Количество должно быть больше нуля, стоимость не может быть отрицательной.",
        "Adet sıfırdan büyük olmalı, maliyet negatif olamaz.")),

    ("PortfolioDialogChecking", (
        "正在核对代码…", "正在核對代碼…", "Checking the code…", "コードを確認中…",
        "코드를 확인하는 중…", "Kennung wird geprüft…", "Vérification du code…",
        "Comprobando el código…", "Verifica del codice…", "Sprawdzanie kodu…",
        "Verificando o código…", "Kontrola kódu…", "Проверяем код…", "Kod denetleniyor…")),

    ("PortfolioDialogUnknown", (
        "行情源查不到 {0}。", "行情源查不到 {0}。", "The quote source does not know {0}.",
        "相場データに {0} が見つかりません。", "시세에서 {0}을(를) 찾을 수 없습니다.",
        "Die Kursquelle kennt {0} nicht.", "La source de cours ne connaît pas {0}.",
        "La fuente de cotizaciones no conoce {0}.", "La fonte delle quotazioni non conosce {0}.",
        "Źródło notowań nie zna {0}.", "A fonte de cotações não conhece {0}.",
        "Zdroj kurzů {0} nezná.", "Источник котировок не знает {0}.",
        "Fiyat kaynağı {0} kodunu bilmiyor.")),

    ("PortfolioImportTitle", (
        "导入成交记录", "匯入成交紀錄", "Import filled orders", "約定履歴を取り込む",
        "체결 내역 가져오기", "Ausführungen importieren", "Importer les exécutions",
        "Importar ejecuciones", "Importa esecuzioni", "Importuj transakcje",
        "Importar execuções", "Importovat obchody", "Импорт сделок", "İşlemleri içe aktar")),

    ("PortfolioImportApply", (
        "导入", "匯入", "Import", "取り込む", "가져오기", "Importieren", "Importer", "Importar",
        "Importa", "Importuj", "Importar", "Importovat", "Импортировать", "İçe aktar")),

    ("PortfolioImportHint", (
        "选一张当日成交的截图，或者直接把成交记录粘进来。识别结果可以先改，确认无误再导入。",
        "選一張當日成交的截圖，或者直接把成交紀錄貼進來。識別結果可以先改，確認無誤再匯入。",
        "Pick a screenshot of the day's filled orders, or paste the list. The result can be corrected before anything is applied.",
        "当日の約定のスクリーンショットを選ぶか、約定履歴を貼り付けてください。内容は取り込む前に修正できます。",
        "당일 체결 화면 캡처를 선택하거나 체결 내역을 붙여넣으세요. 가져오기 전에 수정할 수 있습니다.",
        "Ein Bildschirmfoto der heutigen Ausführungen wählen oder die Liste einfügen. Das Ergebnis lässt sich vor dem Import korrigieren.",
        "Choisissez une capture des exécutions du jour, ou collez la liste. Le résultat est modifiable avant l'import.",
        "Elija una captura de las ejecuciones del día o pegue la lista. El resultado se puede corregir antes de importar.",
        "Scegli uno screenshot delle esecuzioni del giorno o incolla l'elenco. Il risultato è correggibile prima dell'importazione.",
        "Wybierz zrzut ekranu dzisiejszych transakcji lub wklej listę. Wynik można poprawić przed importem.",
        "Escolha uma captura das execuções do dia ou cole a lista. O resultado pode ser corrigido antes de importar.",
        "Vyberte snímek dnešních obchodů nebo vložte seznam. Výsledek lze před importem opravit.",
        "Выберите снимок сегодняшних сделок или вставьте список. Результат можно исправить до импорта.",
        "Günün işlemlerinin ekran görüntüsünü seçin ya da listeyi yapıştırın. Sonuç, aktarmadan önce düzeltilebilir.")),

    ("PortfolioImportPick.Content", (
        "选择截图…", "選擇截圖…", "Choose screenshot…", "スクリーンショットを選ぶ…",
        "캡처 선택…", "Bildschirmfoto wählen…", "Choisir une capture…", "Elegir captura…",
        "Scegli screenshot…", "Wybierz zrzut…", "Escolher captura…", "Vybrat snímek…",
        "Выбрать снимок…", "Ekran görüntüsü seç…")),

    ("PortfolioImportDay.Header", (
        "交易日期", "交易日期", "Trading day", "取引日", "거래일", "Handelstag", "Jour de bourse",
        "Día de negociación", "Giorno di contrattazione", "Dzień transakcyjny", "Dia de negociação",
        "Obchodní den", "Торговый день", "İşlem günü")),

    ("PortfolioImportRaw.PlaceholderText", (
        "粘贴成交记录，一行一笔", "貼上成交紀錄，一行一筆", "Paste the filled orders, one per line",
        "約定履歴を貼り付け（1行1件）", "체결 내역 붙여넣기(한 줄에 한 건)",
        "Ausführungen einfügen, eine pro Zeile", "Collez les exécutions, une par ligne",
        "Pegue las ejecuciones, una por línea", "Incolla le esecuzioni, una per riga",
        "Wklej transakcje, jedna w wierszu", "Cole as execuções, uma por linha",
        "Vložte obchody, jeden na řádek", "Вставьте сделки, по одной в строке",
        "İşlemleri her satıra bir tane olacak şekilde yapıştırın")),

    ("PortfolioImportParse.Content", (
        "解析", "解析", "Parse", "解析", "분석", "Auswerten", "Analyser", "Analizar", "Analizza",
        "Analizuj", "Analisar", "Analyzovat", "Разобрать", "Çözümle")),

    ("PortfolioImportEmpty", (
        "还没有解析结果", "還沒有解析結果", "Nothing parsed yet", "まだ解析結果がありません",
        "아직 분석 결과가 없습니다", "Noch nichts ausgewertet", "Rien d'analysé pour l'instant",
        "Aún no hay resultados", "Nessun risultato", "Brak wyników", "Nada analisado ainda",
        "Zatím žádný výsledek", "Пока ничего не разобрано", "Henüz sonuç yok")),

    ("PortfolioImportReading", (
        "正在识别截图…", "正在識別截圖…", "Reading the screenshot…", "スクリーンショットを認識中…",
        "캡처를 인식하는 중…", "Bildschirmfoto wird gelesen…", "Lecture de la capture…",
        "Leyendo la captura…", "Lettura dello screenshot…", "Odczyt zrzutu ekranu…",
        "Lendo a captura…", "Čte se snímek…", "Распознаём снимок…", "Ekran görüntüsü okunuyor…")),

    ("PortfolioImportNoOcr", (
        "这台电脑没有安装 Windows 的 OCR 语言包，只能手工粘贴。",
        "這台電腦沒有安裝 Windows 的 OCR 語言包，只能手動貼上。",
        "Windows has no OCR language pack on this machine; paste the list instead.",
        "この PC には Windows の OCR 言語パックがありません。貼り付けで入力してください。",
        "이 PC에는 Windows OCR 언어 팩이 없습니다. 붙여넣기로 입력하세요.",
        "Windows hat auf diesem Rechner kein OCR-Sprachpaket; bitte die Liste einfügen.",
        "Windows n'a pas de pack OCR sur cette machine ; collez la liste.",
        "Windows no tiene paquete OCR en este equipo; pegue la lista.",
        "Windows non ha un pacchetto OCR su questo PC; incolla l'elenco.",
        "Windows nie ma tu pakietu OCR; wklej listę.",
        "O Windows não tem pacote OCR nesta máquina; cole a lista.",
        "Windows na tomto počítači nemá OCR balíček; vložte seznam.",
        "На этом компьютере нет языкового пакета OCR для Windows; вставьте список.",
        "Bu bilgisayarda Windows OCR dil paketi yok; listeyi yapıştırın.")),

    ("PortfolioImportNoChinese", (
        "系统里没有中文识别包，中文名可能认不出；数字与代码仍然可用。",
        "系統裡沒有中文識別包，中文名可能認不出；數字與代碼仍然可用。",
        "Windows has no Chinese recogniser, so names may be unreadable; the numbers and codes still are.",
        "中国語の認識パックがないため、中国語名は読めない場合があります。数字とコードは読み取れます。",
        "중국어 인식 팩이 없어 이름이 인식되지 않을 수 있습니다. 숫자와 코드는 읽을 수 있습니다.",
        "Es gibt keine chinesische Erkennung; Namen bleiben evtl. unlesbar, Zahlen und Kennungen nicht.",
        "Pas de reconnaissance chinoise : les noms peuvent être illisibles, les nombres et codes non.",
        "No hay reconocedor de chino: los nombres pueden ser ilegibles; los números y códigos no.",
        "Manca il riconoscitore cinese: i nomi possono essere illeggibili, i numeri e i codici no.",
        "Brak rozpoznawania chińskiego: nazwy mogą być nieczytelne, liczby i kody nie.",
        "Não há reconhecedor de chinês: os nomes podem ficar ilegíveis; os números e códigos não.",
        "Chybí čínské rozpoznávání: jména nemusí být čitelná, čísla a kódy ano.",
        "Нет распознавания китайского: имена могут остаться нечитаемыми, числа и коды — нет.",
        "Çince tanıma yok: adlar okunamayabilir; sayılar ve kodlar okunur.")),

    ("PortfolioImportNothing", (
        "没有读到成交记录", "沒有讀到成交紀錄", "No trades were read", "約定を読み取れませんでした",
        "체결 내역을 읽지 못했습니다", "Keine Ausführungen gelesen", "Aucune exécution lue",
        "No se leyó ninguna ejecución", "Nessuna esecuzione letta", "Nie odczytano transakcji",
        "Nenhuma execução lida", "Nebyly načteny žádné obchody", "Сделки не распознаны",
        "İşlem okunamadı")),

    ("PortfolioImportParsed", (
        "识别到 {0} 笔，跳过 {1} 行", "識別到 {0} 筆，跳過 {1} 行",
        "{0} trades read, {1} lines skipped", "{0} 件を認識、{1} 行をスキップ",
        "{0}건 인식, {1}행 건너뜀", "{0} Ausführungen erkannt, {1} Zeilen übersprungen",
        "{0} exécutions lues, {1} lignes ignorées", "{0} ejecuciones leídas, {1} líneas omitidas",
        "{0} esecuzioni lette, {1} righe saltate", "Odczytano {0} transakcji, pominięto {1} wierszy",
        "{0} execuções lidas, {1} linhas ignoradas", "Rozpoznáno {0} obchodů, přeskočeno {1} řádků",
        "Распознано сделок: {0}, пропущено строк: {1}", "{0} işlem okundu, {1} satır atlandı")),

    ("PortfolioImportSkipped", (
        "有 {0} 行读不出来，先改好再导入", "有 {0} 行讀不出來，先改好再匯入",
        "{0} lines could not be read — fix them before importing",
        "{0} 行を読み取れません。修正してから取り込んでください",
        "{0}행을 읽을 수 없습니다. 수정한 뒤 가져오세요",
        "{0} Zeilen waren nicht lesbar — vor dem Import korrigieren",
        "{0} lignes illisibles — corrigez-les avant d'importer",
        "{0} líneas ilegibles: corríjalas antes de importar",
        "{0} righe illeggibili: correggile prima di importare",
        "{0} wierszy nieczytelnych — popraw je przed importem",
        "{0} linhas ilegíveis — corrija antes de importar",
        "{0} řádků nelze přečíst — před importem je opravte",
        "Строк не удалось прочитать: {0} — исправьте перед импортом",
        "{0} satır okunamadı — aktarmadan önce düzeltin")),

    ("PortfolioImportBuy", (
        "买入", "買入", "Buy", "買い", "매수", "Kauf", "Achat", "Compra", "Acquisto", "Kupno",
        "Compra", "Nákup", "Покупка", "Alım")),

    ("PortfolioImportSell", (
        "卖出", "賣出", "Sell", "売り", "매도", "Verkauf", "Vente", "Venta", "Vendita", "Sprzedaż",
        "Venda", "Prodej", "Продажа", "Satım")),

    ("PortfolioImportRow", (
        "{0} {1} {2} · {3} × {4} · {5}", "{0} {1} {2} · {3} × {4} · {5}",
        "{0} {1} {2} · {3} × {4} · {5}", "{0} {1} {2} · {3} × {4} · {5}",
        "{0} {1} {2} · {3} × {4} · {5}", "{0} {1} {2} · {3} × {4} · {5}",
        "{0} {1} {2} · {3} × {4} · {5}", "{0} {1} {2} · {3} × {4} · {5}",
        "{0} {1} {2} · {3} × {4} · {5}", "{0} {1} {2} · {3} × {4} · {5}",
        "{0} {1} {2} · {3} × {4} · {5}", "{0} {1} {2} · {3} × {4} · {5}",
        "{0} {1} {2} · {3} × {4} · {5}", "{0} {1} {2} · {3} × {4} · {5}")),
]


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    for index, (key, values) in enumerate(ENTRIES):
        assert len(values) == len(LANGS), f"{key}: {len(values)} values for {len(LANGS)} languages"

    for lang in LANGS:
        path = os.path.join(ROOT, lang, "Resources.resw")
        raw = open(path, "rb").read()
        assert raw.startswith(codecs.BOM_UTF8), f"{lang}: resw must keep its BOM"
        text = raw.decode("utf-8-sig")

        # Drop anything this script wrote last time, so it can be re-run after an edit.
        for key, _ in ENTRIES:
            text = re.sub(r'\n *<data name="%s"[^>]*>.*?</data>\n' % re.escape(key), "\n", text, flags=re.S)

        block = []
        for at, (key, values) in enumerate(ENTRIES):
            block.append('  <data name="%s"><value>%s</value></data>' % (key, escape(values[LANGS.index(lang)])))

        text = text.replace("</root>", "\n".join(block) + "\n</root>")
        open(path, "wb").write(codecs.BOM_UTF8 + text.encode("utf-8"))
        print(f"  {lang:8s} +{len(block)} keys")

    # Key order must be identical in all fourteen files: the equality is what the
    # cross-language check rests on.
    hashes = {}
    for lang in LANGS:
        path = os.path.join(ROOT, lang, "Resources.resw")
        names = re.findall(r'<data name="([^"]+)"', open(path, encoding="utf-8-sig").read())
        hashes[lang] = (len(names), hashlib.md5("\n".join(names).encode()).hexdigest()[:12])

    distinct = {v for v in hashes.values()}
    print("key counts/hashes:", hashes)
    assert len(distinct) == 1, "the fourteen files disagree on key order"
    print("OK,", distinct.pop(), "in all fourteen")


if __name__ == "__main__":
    main()
