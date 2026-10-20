using System.Globalization;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>One minute of the day, as the portfolio lived it.</summary>
/// <param name="Minute">Minutes since midnight — 570 is 09:30.</param>
/// <param name="Pnl">Today's profit or loss at that minute, in yuan, after the fills' fees.</param>
/// <param name="Value">What the holdings were worth at that minute, in yuan.</param>
public sealed record PnlSample(int Minute, double Pnl, double Value);

/// <summary>
/// One minute of the book: what every position was holding at that minute, what it cost, and
/// what it had made by then.
///
/// <para>
/// The page's list reads this while the preview plays. Without it the list is a still life —
/// 超图软件 reading 5,900 shares from the open to the close while the curve behind it is drawn
/// on 3,000 — and a reader watching the sale go by at 09:35 sees nothing happen to the position
/// that made it. The whole point of putting the fills on a clock is that the position moves.
/// </para>
///
/// <para>
/// **Cost moves with the fills, not with the price.** It is the diluted figure the broker shows:
/// a purchase averages into it, a sale nets its proceeds off what the remaining shares cost. That
/// is why it is carried per minute rather than computed from the last trade — 顺丰控股's hundred
/// shares are gone at 09:40 and its cost goes with them.
/// </para>
/// </summary>
/// <param name="Minute">Minutes since midnight.</param>
/// <param name="Shares">Shares held of each code at that minute, after that minute's fills.</param>
/// <param name="Costs">Diluted cost per share of each code, in the venue's currency.</param>
/// <param name="Marks">The price each code was marked at, in the venue's currency.</param>
/// <param name="Contributions">What each code had contributed to the day by then, in yuan.</param>
public sealed record PnlMoment(
    int Minute,
    IReadOnlyDictionary<string, double> Shares,
    IReadOnlyDictionary<string, double> Costs,
    IReadOnlyDictionary<string, double> Marks,
    IReadOnlyDictionary<string, double> Contributions);

/// <summary>
/// One trade, placed on the curve.
/// </summary>
/// <param name="Code">The instrument.</param>
/// <param name="Name">Its name at import time.</param>
/// <param name="Side">Buy or sell.</param>
/// <param name="Price">The price it filled at, in the venue's currency.</param>
/// <param name="Shares">How many shares changed hands.</param>
/// <param name="Minute">
/// The minute of the curve the trade is applied at — not always the clock on the ticket: a trade
/// stamped inside the lunch break is applied when the afternoon opens, because that is the first
/// point of the curve that exists. Markers are drawn here, so a marker is always on a sample.
/// </param>
public sealed record PnlTrade(
    string Code, string Name, TradeSide Side, double Price, double Shares, int Minute);

/// <summary>One position, as the day treated it.</summary>
/// <param name="Code">The instrument.</param>
/// <param name="Name">Its name at the source.</param>
/// <param name="Shares">Shares held now — after today's trades, not before them.</param>
/// <param name="OpeningShares">Shares held when the day opened.</param>
/// <param name="Cost">Diluted cost per share, in the venue's currency.</param>
/// <param name="PrevClose">Yesterday's close, or today's last price when it did not trade.</param>
/// <param name="Last">Today's last price.</param>
/// <param name="DayPnl">This position's contribution to today's profit, in yuan.</param>
/// <param name="Value">What it is worth now, in yuan.</param>
/// <param name="HasSession">Whether the venue traded on the day being drawn.</param>
public sealed record PnlHolding(
    string Code,
    string Name,
    double Shares,
    double OpeningShares,
    double Cost,
    double PrevClose,
    double Last,
    double DayPnl,
    double Value,
    bool HasSession)
{
    /// <summary>Whether this is a Hong Kong listing, which is the only currency question here.</summary>
    public bool IsHongKong => Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase);
}

/// <summary>
/// A day's worth of a portfolio, minute by minute.
///
/// <para>
/// **The curve is mark-to-market against yesterday's close, with the trades at their own
/// minutes.** That is the only definition under which the number is continuous: a holding's
/// profit is <c>shares × (price − previous close)</c>, and when the shares change the profit must
/// not jump. Selling 5,900 shares at 10.05 when yesterday's close was 9.88 realises
/// <c>5,900 × 0.17</c>; a curve that dropped the position at the sale without crediting the sale
/// would show the whole morning's gain disappearing at 09:35. So the running figure is
/// <c>Σ shares(t) × price(t) + cash(t) − Σ shares(0) × previous close</c>, which is the same
/// number the broker app puts in 今日盈亏. The fills' fees come off the cash term, so the two are
/// the same figure and not two figures that happen to be close.
/// </para>
///
/// <para>
/// **The book is the day's opening position, and the fills walk it forward.** The reader copies
/// the broker's holdings screen at the open, so the shares in the book are the ones held at 09:30;
/// each fill moves them at its own minute. A sale bigger than what was held at that minute is
/// clamped to what was there — a row missing from the book must not turn into profit.
/// </para>
///
/// <para>
/// **One currency.** A Hong Kong holding is worth what it is worth in dollars, and the total on
/// the frame is in yuan, so the rate has to be applied somewhere. It is applied here, at today's
/// rate, to the position and to the day's profit — not to the cost, which is stored in the
/// venue's currency and is meant to last for years. A portfolio of one market never touches it.
/// </para>
/// </summary>
/// <param name="Day">The session being drawn, `2026-10-19`.</param>
/// <param name="OpenMinute">When it opened, 570 for 09:30.</param>
/// <param name="CloseMinute">When it closed: 900 for 15:00, 960 for Hong Kong's 16:00.</param>
/// <param name="Samples">One per trading minute from the open to the last print. **The lunch break
/// is not in it**: the axis is 09:30–11:30 then 13:00–15:00, four hours of trading laid end to
/// end, because a flat ninety-minute stretch in the middle of the frame is a quarter of the
/// picture spent saying nothing traded.</param>
/// <param name="Moments">The same minutes again, per position: what each one held, what it cost,
/// where it was marked and what it had made. The page's list is drawn from this, so the numbers
/// under the preview are the numbers the preview is drawing.</param>
/// <param name="Holdings">Every position, priced — plus any code that traded today and is no
/// longer held, at zero shares, so that a position closed out during the day still contributes the
/// profit its sale realised.</param>
/// <param name="Last">The day's profit at the last sample, in yuan.</param>
/// <param name="Peak">The highest the curve reached. Never below zero: the day starts there.</param>
/// <param name="Trough">The lowest it reached, and the axis's other end.</param>
/// <param name="Value">What the holdings are worth at the last sample, in yuan.</param>
/// <param name="PrevValue">What they were worth at yesterday's close, in yuan — the denominator
/// of the day's return.</param>
/// <param name="HkdCny">The rate used, or zero when no Hong Kong holding needed one.</param>
/// <param name="TradeCount">How many of today's trades are folded in.</param>
/// <param name="Trades">Those trades, placed on the curve, in clock order.</param>
/// <param name="Closed">Holdings whose venue did not trade today, excluded from the curve.</param>
/// <param name="FetchedAt">When this was read, for the page's "updated at" line.</param>
public sealed record PortfolioSession(
    string Day,
    int OpenMinute,
    int CloseMinute,
    IReadOnlyList<PnlSample> Samples,
    IReadOnlyList<PnlMoment> Moments,
    IReadOnlyList<PnlHolding> Holdings,
    double Last,
    double Peak,
    double Trough,
    int PeakMinute,
    int TroughMinute,
    double Value,
    double PrevValue,
    double HkdCny,
    int TradeCount,
    IReadOnlyList<PnlTrade> Trades,
    IReadOnlyList<string> Closed,
    DateTime FetchedAt)
{
    /// <summary>The day's return: profit over what the book was worth at yesterday's close.</summary>
    public double ReturnPct => PrevValue > 0 ? (Last / PrevValue) * 100 : 0;

    /// <summary>The clock label for a minute since midnight: `09:30`.</summary>
    public static string Clock(int minute) =>
        $"{minute / 60:00}:{minute % 60:00}";

    /// <summary>The minute the last sample landed on.</summary>
    public int LastMinute => Samples.Count > 0 ? Samples[^1].Minute : OpenMinute;

    /// <summary>How many positions the book actually holds, closed-out codes excluded.</summary>
    public int OpenPositions => Holdings.Count(h => h.Shares > 0);
}

/// <summary>
/// Reads a portfolio's day.
///
/// Two endpoints, both already used elsewhere in this app, and one property of each that this
/// page depends on:
///
/// <list type="bullet">
/// <item><c>qt.gtimg.cn/q=</c> takes every code in one request and carries yesterday's close in
/// field 4. That field is the whole basis of a day's profit and no other endpoint has it.</item>
/// <item><c>web.ifzq.gtimg.cn/appstock/app/day/query</c> carries five sessions of
/// <c>time, price, cumulative volume, cumulative amount</c>. The price at field 1 is what this
/// page draws; the amount is what the turnover page draws from the same rows.</item>
/// </list>
///
/// <para>
/// **The days are not the same on both venues.** Measured on 2026-10-19, a Hong Kong holiday:
/// the A-share codes listed that day and the Hong Kong ones listed 2026-10-16 as their latest.
/// So the day being drawn is chosen once — today if any holding traded, otherwise the latest day
/// any of them did — and a holding that did not trade on it contributes nothing and is named on
/// the page rather than being priced off a stale session, which would report Friday's move as
/// Monday's.
/// </para>
/// </summary>
public static class IntradayPnl
{
    private const string MinuteEndpoint = "https://web.ifzq.gtimg.cn/appstock/app/day/query";
    private const string FxEndpoint = "https://qt.gtimg.cn/q=whHKDCNY";

    /// <summary>The open, on every venue these pages cover.</summary>
    public const int OpenMinute = (9 * 60) + 30;

    /// <summary>When Shanghai and Shenzhen stop for lunch.</summary>
    public const int MainlandLunch = (11 * 60) + 30;

    /// <summary>When Hong Kong stops for lunch — half an hour later than the mainland.</summary>
    public const int KongLunch = 12 * 60;

    /// <summary>When every venue resumes.</summary>
    public const int AfternoonOpen = 13 * 60;

    /// <summary>When Shanghai and Shenzhen close.</summary>
    public const int MainlandClose = 15 * 60;

    /// <summary>When Hong Kong closes.</summary>
    public const int HongKongClose = 16 * 60;

    /// <summary>How many venues one load reads at once. Small: a book, not a board.</summary>
    private const int Parallel = 4;

    public static async Task<PortfolioSession> LoadAsync(
        HttpClient http,
        StockDirectory stocks,
        IReadOnlyList<Holding> holdings,
        IReadOnlyList<PortfolioTrade> journal,
        IProgress<string>? progress,
        CancellationToken cancellation,
        FeeSchedule? fees = null)
    {
        if (holdings.Count == 0)
        {
            throw new InvalidOperationException(Strings.Get("PortfolioEmpty"));
        }

        progress?.Report(Strings.Get("PortfolioFetchingQuotes"));

        var today = DateTime.Today.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

        // **Every code the journal mentions**, not just today's. The day being drawn is very often
        // not today — before the open it is the last session that traded — and a code that only
        // appears in that day's fills still needs a session to be priced off: a position bought and
        // sold the same day has no row in the book at all. (Filtering by today was how that code
        // went unfetched on every morning run.)
        var codes = holdings.Select(h => h.Code)
            .Concat(journal.Select(t => t.Code))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        var shots = await stocks.SnapshotsAsync(codes, cancellation);

        var sessions = await ReadSessionsAsync(http, codes, progress, cancellation);

        // The day: today if anyone traded, otherwise the latest session any of them has. See the
        // class note — choosing per holding would put two days on one axis.
        var day = sessions.Values.Select(s => s.Day).DefaultIfEmpty(string.Empty).Max(StringComparer.Ordinal) ?? string.Empty;

        if (sessions.Values.Any(s => s.Day == today))
        {
            day = today;
        }

        if (day.Length == 0)
        {
            throw new InvalidOperationException(Strings.Get("PortfolioNoSession"));
        }

        progress?.Report(Strings.Format("PortfolioFetchingRates", day));

        var hkd = holdings.Any(h => h.IsHongKong)
            ? await ReadHkdCnyAsync(http, cancellation)
            : 0;

        return Assemble(day, holdings, journal, shots, sessions, hkd, fees ?? FeeSchedule.Mainland);
    }

    /// <summary>
    /// Builds the curve from what was fetched. Pure, so the arithmetic can be read without a
    /// network in the way.
    /// </summary>
    public static PortfolioSession Assemble(
        string day,
        IReadOnlyList<Holding> holdings,
        IReadOnlyList<PortfolioTrade> journal,
        IReadOnlyDictionary<string, StockSnapshot> shots,
        IReadOnlyDictionary<string, DaySession> sessions,
        double hkdCny,
        FeeSchedule fees)
    {
        var trades = journal
            .Where(t => t.Day == day)
            .OrderBy(t => t.MinuteOfDay)
            .ThenBy(t => t.Time, StringComparer.Ordinal)
            .ToList();

        // **The book plus the day's closed-out codes.** `Portfolio.Apply` drops a position the
        // moment it reaches zero shares, which is what a book should do — and would take the day's
        // realised profit off the curve with it, because a code that is not in the book is not
        // priced. A position sold out at 14:00 must still have started the morning worth
        // something; it is carried here at zero shares so the arithmetic has somewhere to stand.
        var book = holdings.ToList();

        foreach (var code in trades.Select(x => x.Code).Distinct(StringComparer.OrdinalIgnoreCase))
        {
            if (book.Any(h => string.Equals(h.Code, code, StringComparison.OrdinalIgnoreCase)))
            {
                continue;
            }

            var named = trades.First(x => string.Equals(x.Code, code, StringComparison.OrdinalIgnoreCase)).Name;

            book.Add(new Holding(code, named, 0, 0));
        }

        // The book as the day opened. **It is the opening position already** — the reader copies
        // the broker's holdings screen at the open — so there is nothing to undo. It used to be
        // read as the *closing* position with the day's fills reversed out of it, which is only
        // right if the book is the evening's: fed a morning book, 超图软件's 5,900 shares plus a
        // 3,000 buy and a 5,900 sale came back as 8,800 shares at 09:30, and two thirds of the
        // day's move was reported on shares nobody held.
        var opening = book.ToDictionary(h => h.Code, h => h.Shares, StringComparer.OrdinalIgnoreCase);

        // Which venues actually traded today — the axis ends at the last of their closes, and the
        // lunch break it skips is the one they have. A book holding a Hong Kong name is not a
        // reason to draw to 16:00 on a day Hong Kong is shut: those holdings contribute nothing,
        // and the axis would end with an hour of empty frame under a label reading 16:00.
        var mainlandLive = book.Any(h =>
            !h.IsHongKong && sessions.TryGetValue(h.Code, out var s) && s.Day == day);

        var kongLive = book.Any(h =>
            h.IsHongKong && sessions.TryGetValue(h.Code, out var s) && s.Day == day);

        // The axis ends at the latest close among the venues that actually traded today — not at
        // 16:00 just because the book names a Hong Kong listing. Decided per holding below: a
        // holding that is open today and listed in Hong Kong pushes the close to 16:00; a book that
        // only holds Hong Kong names on a day Hong Kong is shut ends at 15:00 like any mainland day.
        var close = MainlandClose;

        var windows = new List<(int From, int To)>();

        if (mainlandLive)
        {
            windows.Add((OpenMinute, MainlandLunch));
            windows.Add((AfternoonOpen, MainlandClose));
        }

        if (kongLive)
        {
            windows.Add((OpenMinute, KongLunch));
            windows.Add((AfternoonOpen, HongKongClose));
        }

        // The last minute that carries a print. The curve stops there: a session still in progress
        // ends at its newest print, and drawing it out to the close would be an empty afternoon.
        var lastMinute = OpenMinute;
        var priced = new List<PnlHolding>();
        var closed = new List<string>();

        foreach (var holding in book)
        {
            shots.TryGetValue(holding.Code, out var shot);

            sessions.TryGetValue(holding.Code, out var session);

            var live = session is not null && session.Day == day;
            var rate = holding.IsHongKong ? hkdCny : 1;

            // A Hong Kong listing that is trading today extends the axis to 16:00; a shut one
            // does not — lastMinute is already capped by the venues that actually printed.
            if (holding.IsHongKong && live)
                {
                    close = HongKongClose;
                }

            // Prices came out of a JSON dictionary, so "the newest" and "the oldest" are both a
            // lookup and neither is a position: a sorted dictionary has no index to ask for.
            var prevClose = live
                ? shot?.PreviousClose is > 0 ? shot.PreviousClose : session!.FirstPrice
                : shot?.Price is > 0 ? shot.Price : session?.LastPrice ?? 0;

            var mark = live ? session!.LastPrice : prevClose;

            var openingShares = opening.TryGetValue(holding.Code, out var o) ? o : 0;

            // Where the day's fills leave this position, and the cash they actually moved.
            var (shares, cashMoved) = Replay(trades, holding.Code, openingShares, fees);

            // In the venue's own currency, then converted once: the price term and the cash term
            // are both dollars for a Hong Kong row, and converting only one of them would add a
            // number in one currency to a number in another.
            var contribution = live
                ? ((shares * mark) - (openingShares * prevClose) + cashMoved) * rate
                : 0;

            if (!live)
            {
                closed.Add(holding.Code);
                contribution = 0;
            }
            else
            {
                lastMinute = Math.Max(lastMinute, Math.Min(close, session!.LastMinute));
            }

            priced.Add(new PnlHolding(
                holding.Code,
                shot?.Name is { Length: > 0 } name ? name : holding.Name,
                shares,
                openingShares,
                holding.Cost,
                prevClose,
                live ? mark : prevClose,
                contribution,
                (live ? shares * mark : shares * prevClose) * rate,
                live));
        }

        // The axis: every minute the venues that traded were open, laid end to end. 09:30–11:30
        // then 13:00–15:00 is 242 points and four hours of trading — the lunch break is not in the
        // axis at all, because ninety minutes of flat line is a quarter of the frame spent drawing
        // a straight line, and the reader's eye reads the gap as missing data rather than as a
        // closed market.
        var slots = new List<int>();

        for (var minute = OpenMinute; minute <= Math.Min(close, Math.Max(OpenMinute, lastMinute)); minute++)
        {
            if (windows.Any(w => minute >= w.From && minute <= w.To))
            {
                slots.Add(minute);
            }
        }

        if (slots.Count == 0)
        {
            slots.Add(OpenMinute);
        }

        // Yesterday's value, in yuan: every position at yesterday's close. A holding that did not
        // trade today is valued at the price it is still marked at, which is the same number.
        var prevValue = 0.0;

        foreach (var holding in book)
        {
            var rate = holding.IsHongKong ? hkdCny : 1;
            var openingShares = opening.TryGetValue(holding.Code, out var o) ? o : 0;
            var at = priced.First(x => string.Equals(x.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            prevValue += openingShares * at.PrevClose * rate;
        }

        var positions = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var lastPrice = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var costs = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var cashOf = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var byCode = priced.ToDictionary(x => x.Code, StringComparer.OrdinalIgnoreCase);

        foreach (var holding in book)
        {
            var at = byCode[holding.Code];

            positions[holding.Code] = opening.TryGetValue(holding.Code, out var o) ? o : 0;
            lastPrice[holding.Code] = at.PrevClose;
            costs[holding.Code] = holding.Cost;
        }

        var samples = new List<PnlSample>();
        var moments = new List<PnlMoment>();
        var placed = new List<PnlTrade>();
        var cash = 0.0;
        var next = 0;

        foreach (var minute in slots)
        {
            // Every trade stamped at or before this minute, applied here. `<=` and a moving
            // cursor rather than a lookup by minute, because the axis has holes in it: the lunch
            // break, and any minute one venue is shut while another trades. A fill the broker
            // times inside a hole lands on the first point of the curve that exists instead of
            // nowhere at all.
            while (next < trades.Count && trades[next].MinuteOfDay <= minute)
            {
                var trade = trades[next++];
                var rate = trade.Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase) ? hkdCny : 1;

                positions.TryGetValue(trade.Code, out var held);

                // Only the shares that were actually there are booked. See `Replay`: money for
                // shares nobody held is not profit, it is a hole in the book. The marker is still
                // drawn for the fill as it happened — it is the money that is clamped.
                var moved = trade.Side == TradeSide.Buy ? trade.Shares : Math.Min(trade.Shares, held);

                // Fees are charged on the money that actually changed hands — the clamped shares,
                // not the ticket's — and in the venue's own currency, so both terms convert with
                // one rate below.
                var gross = moved * trade.Price;
                var fee = trade.Side == TradeSide.Buy ? fees.OnBuy(gross) : fees.OnSell(gross);

                cash += ((trade.Side == TradeSide.Buy ? -1 : 1) * gross - fee) * rate;
                cashOf[trade.Code] = Cash(cashOf, trade.Code)
                    + ((trade.Side == TradeSide.Buy ? -1 : 1) * gross - fee);

                // The diluted cost, moved by the same fill — a purchase averages into it, a sale
                // nets its proceeds off what is left. Kept in step with the fill so the page can
                // say what the remaining shares cost at the minute it is drawing, rather than
                // what they cost this morning.
                costs[trade.Code] = Diluted(Cash(costs, trade.Code), held, moved, trade, fee);

                positions[trade.Code] = trade.Side == TradeSide.Buy
                    ? held + moved
                    : Math.Max(0, held - moved);

                placed.Add(new PnlTrade(trade.Code, trade.Name, trade.Side, trade.Price, trade.Shares, minute));
            }

            foreach (var holding in book)
            {
                if (sessions.TryGetValue(holding.Code, out var session) && session.Day == day &&
                    session.TryPrice(minute, out var price))
                {
                    lastPrice[holding.Code] = price;
                }
            }

            var value = 0.0;
            var contributions = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);

            foreach (var holding in book)
            {
                var rate = holding.IsHongKong ? hkdCny : 1;

                positions.TryGetValue(holding.Code, out var shares);
                lastPrice.TryGetValue(holding.Code, out var price);

                value += shares * price * rate;

                // The same arithmetic the per-holding column ends up showing, only asked at this
                // minute: what the position is worth, what it was worth at yesterday's close, and
                // the cash the fills have moved so far.
                var at = byCode[holding.Code];

                contributions[holding.Code] =
                    ((shares * price) - (at.OpeningShares * at.PrevClose) + Cash(cashOf, holding.Code)) * rate;
            }

            samples.Add(new PnlSample(minute, value + cash - prevValue, value));
            moments.Add(new PnlMoment(
                minute,
                new Dictionary<string, double>(positions, StringComparer.OrdinalIgnoreCase),
                new Dictionary<string, double>(costs, StringComparer.OrdinalIgnoreCase),
                new Dictionary<string, double>(lastPrice, StringComparer.OrdinalIgnoreCase),
                contributions));
        }

        var peak = samples.Count > 0 ? samples.Max(s => s.Pnl) : 0;
        var trough = samples.Count > 0 ? samples.Min(s => s.Pnl) : 0;
        var atPeak = samples.FirstOrDefault(s => Math.Abs(s.Pnl - peak) < 1e-9)?.Minute ?? OpenMinute;
        var atTrough = samples.FirstOrDefault(s => Math.Abs(s.Pnl - trough) < 1e-9)?.Minute ?? OpenMinute;

        // Recomputed from the assembled samples rather than summed from the positions, so the
        // headline number and the curve's last point cannot disagree.
        var last = samples.Count > 0 ? samples[^1].Pnl : 0;

        var valueNow = 0.0;

        foreach (var holding in book)
        {
            var rate = holding.IsHongKong ? hkdCny : 1;

            positions.TryGetValue(holding.Code, out var shares);
            lastPrice.TryGetValue(holding.Code, out var price);

            valueNow += shares * price * rate;
        }

        return new PortfolioSession(
            day,
            OpenMinute,
            close,
            samples,
            moments,
            priced,
            last,
            Math.Max(0, peak),
            Math.Min(0, trough),
            atPeak,
            atTrough,
            valueNow,
            prevValue,
            hkdCny,
            trades.Count,
            placed,
            closed,
            DateTime.Now);
    }

    /// <summary>A code's running total in a dictionary that may not have it yet.</summary>
    private static double Cash(IReadOnlyDictionary<string, double> from, string code) =>
        from.TryGetValue(code, out var value) ? value : 0;

    /// <summary>
    /// The diluted cost per share after one fill — the figure the broker shows beside a position.
    ///
    /// A purchase averages into it, fee and all; a sale nets **what the sale actually brought in**
    /// off what is left, which is why a sale's fees push the remaining shares' cost *up* rather
    /// than down: 超图软件's 3,000 remaining shares read 6.544 in the broker app and 6.529 without
    /// the 45 yuan of commission and stamp duty, and the difference is not rounding.
    ///
    /// Zero once nothing is left: 顺丰控股's hundred shares are gone at 09:40, and a cost for
    /// shares that are not there is a number with nothing to describe.
    /// </summary>
    private static double Diluted(
        double cost, double held, double moved, PortfolioTrade trade, double fee)
    {
        if (trade.Side == TradeSide.Buy)
        {
            var after = held + moved;

            return after > 0 ? ((held * cost) + (moved * trade.Price) + fee) / after : trade.Price;
        }

        var left = held - moved;

        return left > 0 ? ((held * cost) - ((moved * trade.Price) - fee)) / left : 0;
    }

    /// <summary>
    /// One code's day, replayed from the shares the book opened with: where the position ends up,
    /// and the cash the fills actually moved — negative when it bought more than it sold.
    ///
    /// A sale of more shares than were held **at that moment** is clamped to what was there, and
    /// the clamped quantity is what gets booked. Without the clamp a row missing from the book
    /// becomes profit: 顺丰控股's 100 shares sold at 31.80 are ¥3,180 of "gain" if the sale is
    /// credited in full while no opening position is charged for it. Money for shares nobody held
    /// is not profit, it is a hole in the book — and the page says so on import instead.
    ///
    /// Used for the per-holding contribution so that each row adds up to the total: a holding that
    /// was sold out of still shows the profit the sale realised.
    /// </summary>
    /// <param name="fees">What the fills cost. Charged here too, or the per-holding column and
    /// the curve behind it would be two answers to the same question — one that knows about
    /// commission and one that does not.</param>
    private static (double Shares, double Cash) Replay(
        IEnumerable<PortfolioTrade> trades, string code, double opening, FeeSchedule fees)
    {
        var shares = opening;
        var cash = 0.0;

        foreach (var trade in trades)
        {
            if (!string.Equals(trade.Code, code, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (trade.Side == TradeSide.Buy)
            {
                var gross = trade.Shares * trade.Price;

                shares += trade.Shares;
                cash -= gross + fees.OnBuy(gross);
            }
            else
            {
                var sold = Math.Min(trade.Shares, shares);
                var gross = sold * trade.Price;

                shares -= sold;
                cash += gross - fees.OnSell(gross);
            }
        }

        return (shares, cash);
    }

    /// <summary>One instrument's session: the day it is, and the price at each minute.</summary>
    /// <param name="Day">`yyyy-MM-dd`.</param>
    /// <param name="Prices">Price by minute since midnight, ascending.</param>
    public sealed record DaySession(string Day, SortedDictionary<int, double> Prices)
    {
        public int LastMinute => Prices.Count > 0 ? Prices.Keys.Max() : 0;

        /// <summary>The first print of the day. Used as yesterday's close when the snapshot's own
        /// field is empty, which happens for a listing that did not trade yesterday.</summary>
        public double FirstPrice => Prices.Count > 0 ? Prices.Values.First() : 0;

        /// <summary>The newest print there is.</summary>
        public double LastPrice => Prices.Count > 0 ? Prices.Values.Last() : 0;

        /// <summary>The price at a minute, carrying the last print forward. Not zero: a minute
        /// with no print is a minute nothing traded, not a minute the stock was free.</summary>
        public bool TryPrice(int minute, out double price)
        {
            price = 0;
            var found = false;

            foreach (var (at, value) in Prices)
            {
                if (at > minute)
                {
                    break;
                }

                price = value;
                found = true;
            }

            return found;
        }
    }

    /// <summary>Reads every instrument's five sessions, a few at a time.</summary>
    private static async Task<Dictionary<string, DaySession>> ReadSessionsAsync(
        HttpClient http, IReadOnlyList<string> codes, IProgress<string>? progress, CancellationToken cancellation)
    {
        var found = new Dictionary<string, DaySession>(StringComparer.OrdinalIgnoreCase);
        var gate = new SemaphoreSlim(Parallel);
        var done = 0;

        var tasks = codes.Select(async code =>
        {
            await gate.WaitAsync(cancellation);

            try
            {
                var session = await ReadSessionAsync(http, code, cancellation);

                if (session is not null)
                {
                    lock (found)
                    {
                        found[code] = session;
                    }
                }
            }
            catch (Exception) when (!cancellation.IsCancellationRequested)
            {
                // One instrument the minute endpoint will not serve (a suspended listing, a
                // delisted one) must not take the book down. It is left out of the curve and
                // reported by the page, which is the difference between a number that is
                // slightly small and a page that cannot open.
            }
            finally
            {
                gate.Release();

                var at = Interlocked.Increment(ref done);
                progress?.Report(Strings.Format("PortfolioFetchingMinutes", at, codes.Count));
            }
        });

        await Task.WhenAll(tasks);

        return found;
    }

    /// <summary>
    /// One instrument's sessions, newest first from the source.
    ///
    /// Only the latest one is kept: this page draws a day, and the endpoint's five are there so
    /// the turnover page can offer a choice. Keeping all five would be four days of memory per
    /// holding to draw one.
    /// </summary>
    private static async Task<DaySession?> ReadSessionAsync(
        HttpClient http, string code, CancellationToken cancellation)
    {
        var uri = $"{MinuteEndpoint}?code={Uri.EscapeDataString(code.ToLowerInvariant())}";

        using var response = await http.GetAsync(uri, cancellation);

        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        var root = json.RootElement;

        if (!root.TryGetProperty("data", out var data) ||
            !data.TryGetProperty(code.ToLowerInvariant(), out var node) ||
            !node.TryGetProperty("data", out var days) ||
            days.ValueKind != JsonValueKind.Array)
        {
            return null;
        }

        DaySession? latest = null;

        foreach (var day in days.EnumerateArray())
        {
            if (!day.TryGetProperty("date", out var date) ||
                date.GetString() is not { Length: 8 } stamp ||
                !day.TryGetProperty("data", out var rows) ||
                rows.ValueKind != JsonValueKind.Array)
            {
                continue;
            }

            var prices = new SortedDictionary<int, double>();

            foreach (var row in rows.EnumerateArray())
            {
                var text = row.GetString();

                if (text is null)
                {
                    continue;
                }

                var fields = text.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);

                // Time, price, cumulative volume, cumulative amount. A three-field row is the
                // Beijing board's, which carries no amount — irrelevant here, since only the
                // price is read.
                if (fields.Length < 2 || fields[0].Length < 4)
                {
                    continue;
                }

                if (!int.TryParse(fields[0][..2], NumberStyles.Integer, CultureInfo.InvariantCulture, out var hour) ||
                    !int.TryParse(fields[0][2..4], NumberStyles.Integer, CultureInfo.InvariantCulture, out var minute) ||
                    !double.TryParse(fields[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var price) ||
                    price <= 0)
                {
                    continue;
                }

                prices[(hour * 60) + minute] = price;
            }

            if (prices.Count == 0)
            {
                continue;
            }

            var iso = $"{stamp[..4]}-{stamp[4..6]}-{stamp[6..]}";

            if (latest is null || string.CompareOrdinal(iso, latest.Day) > 0)
            {
                latest = new DaySession(iso, prices);
            }
        }

        return latest;
    }

    /// <summary>
    /// The Hong Kong dollar in yuan, as the quote endpoint has it now.
    ///
    /// **Asked for rather than assumed.** A constant here would be a rate frozen on the day the
    /// code was written, applied silently to every Hong Kong holding for as long as the app
    /// lives. `whHKDCNY` answers with 22 fields rather than the 46 a share carries, so it is
    /// read on its own rather than through <see cref="StockDirectory"/>.
    /// </summary>
    private static async Task<double> ReadHkdCnyAsync(HttpClient http, CancellationToken cancellation)
    {
        using var response = await http.GetAsync(FxEndpoint, cancellation);

        response.EnsureSuccessStatusCode();

        var bytes = await response.Content.ReadAsByteArrayAsync(cancellation);

        var text = Gbk.GetString(bytes);

        var fields = text.Split('~');

        if (fields.Length < 4 ||
            !double.TryParse(fields[3], NumberStyles.Float, CultureInfo.InvariantCulture, out var rate) ||
            rate <= 0)
        {
            throw new InvalidOperationException(Strings.Get("PortfolioFxFailed"));
        }

        return rate;
    }

    private static readonly Encoding Gbk = CreateGbk();

    private static Encoding CreateGbk()
    {
        Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);

        return Encoding.GetEncoding(936);
    }
}
