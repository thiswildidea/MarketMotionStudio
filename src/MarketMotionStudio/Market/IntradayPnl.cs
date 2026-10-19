using System.Globalization;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>One minute of the day, as the portfolio lived it.</summary>
/// <param name="Minute">Minutes since midnight — 570 is 09:30.</param>
/// <param name="Pnl">Today's profit or loss at that minute, in yuan, fees excluded.</param>
/// <param name="Value">What the holdings were worth at that minute, in yuan.</param>
public sealed record PnlSample(int Minute, double Pnl, double Value);

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
/// number the broker app puts in 今日盈亏 (its difference is fees, which this page does not
/// pretend to know).
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
/// <param name="Samples">One per trading minute from the open to the last print — flat across
/// the lunch break, which is what a price does when nobody is trading it.</param>
/// <param name="Holdings">Every position, priced.</param>
/// <param name="Last">The day's profit at the last sample, in yuan.</param>
/// <param name="Peak">The highest the curve reached. Never below zero: the day starts there.</param>
/// <param name="Trough">The lowest it reached, and the axis's other end.</param>
/// <param name="Value">What the holdings are worth at the last sample, in yuan.</param>
/// <param name="PrevValue">What they were worth at yesterday's close, in yuan — the denominator
/// of the day's return.</param>
/// <param name="HkdCny">The rate used, or zero when no Hong Kong holding needed one.</param>
/// <param name="TradeCount">How many of today's trades are folded in.</param>
/// <param name="Closed">Holdings whose venue did not trade today, excluded from the curve.</param>
/// <param name="FetchedAt">When this was read, for the page's "updated at" line.</param>
public sealed record PortfolioSession(
    string Day,
    int OpenMinute,
    int CloseMinute,
    IReadOnlyList<PnlSample> Samples,
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
        CancellationToken cancellation)
    {
        if (holdings.Count == 0)
        {
            throw new InvalidOperationException(Strings.Get("PortfolioEmpty"));
        }

        progress?.Report(Strings.Get("PortfolioFetchingQuotes"));

        var codes = holdings.Select(h => h.Code).Distinct(StringComparer.OrdinalIgnoreCase).ToList();

        var shots = await stocks.SnapshotsAsync(codes, cancellation);

        var sessions = await ReadSessionsAsync(http, codes, progress, cancellation);

        // The day: today if anyone traded, otherwise the latest session any of them has. See the
        // class note — choosing per holding would put two days on one axis.
        var today = DateTime.Today.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

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

        return Assemble(day, holdings, journal, shots, sessions, hkd);
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
        double hkdCny)
    {
        var trades = journal.Where(t => t.Day == day).OrderBy(t => t.MinuteOfDay).ToList();

        // The book as the day opened: today's holdings with today's trades undone. A curve that
        // started from the closing position would hold this afternoon's shares all morning.
        var opening = holdings.ToDictionary(h => h.Code, h => h.Shares, StringComparer.OrdinalIgnoreCase);

        foreach (var trade in trades)
        {
            opening.TryGetValue(trade.Code, out var held);

            var before = trade.Side == TradeSide.Buy ? held - trade.Shares : held + trade.Shares;

            if (before <= 0)
            {
                opening.Remove(trade.Code);
            }
            else
            {
                opening[trade.Code] = before;
            }
        }

        // The axis ends when the last venue that actually traded today closes. A book holding a
        // Hong Kong name is not a reason to draw to 16:00: on a day the Hong Kong market is shut,
        // those holdings contribute nothing (see `live` below), and an axis running on to 16:00
        // would leave the whole last hour of the frame empty — the curve stopping four fifths of
        // the way across a chart whose right-hand label says 16:00.
        var close = MainlandClose;

        // Minutes that carry a print, and the last of them. The curve stops at the latest print
        // any holding made: a session still in progress ends there, and drawing it out to the
        // close would be an empty afternoon.
        var lastMinute = OpenMinute;
        var priced = new List<PnlHolding>();
        var closed = new List<string>();

        foreach (var holding in holdings)
        {
            shots.TryGetValue(holding.Code, out var shot);

            sessions.TryGetValue(holding.Code, out var session);

            var live = session is not null && session.Day == day;
            var rate = holding.IsHongKong ? hkdCny : 1;

            // Prices came out of a JSON dictionary, so "the newest" and "the oldest" are both a
            // lookup and neither is a position: a sorted dictionary has no index to ask for.
            var prevClose = live
                ? shot?.PreviousClose is > 0 ? shot.PreviousClose : session!.FirstPrice
                : shot?.Price is > 0 ? shot.Price : session?.LastPrice ?? 0;

            var mark = live ? session!.LastPrice : prevClose;

            var shares = holding.Shares;
            var openingShares = opening.TryGetValue(holding.Code, out var o) ? o : 0;

            // In the venue's own currency, then converted once: the price term and the cash term
            // are both dollars for a Hong Kong row, and converting only one of them would add a
            // number in one currency to a number in another.
            var contribution = live
                ? ((shares * mark) - (openingShares * prevClose) + TradeCash(trades, holding.Code)) * rate
                : 0;

            if (!live)
            {
                closed.Add(holding.Code);
                contribution = 0;
            }
            else
            {
                // A live Hong Kong holding is what stretches the axis to 16:00 — decided here,
                // from the venue that traded, rather than from the book's contents.
                if (holding.IsHongKong)
                {
                    close = HongKongClose;
                }

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

        var samples = new List<PnlSample>();
        var byMinute = trades
            .GroupBy(t => Math.Max(OpenMinute, t.MinuteOfDay))
            .ToDictionary(g => g.Key, g => g.ToList());

        // Yesterday's value, in yuan: every position at yesterday's close. A holding that did not
        // trade today is valued at the price it is still marked at, which is the same number.
        var prevValue = 0.0;

        foreach (var holding in holdings)
        {
            var rate = holding.IsHongKong ? hkdCny : 1;
            var openingShares = opening.TryGetValue(holding.Code, out var o) ? o : 0;
            var p = priced.First(x => string.Equals(x.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            prevValue += openingShares * p.PrevClose * rate;
        }

        var positions = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var lastPrice = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var cash = 0.0;

        foreach (var holding in holdings)
        {
            var p = priced.First(x => string.Equals(x.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            positions[holding.Code] = opening.TryGetValue(holding.Code, out var o) ? o : 0;
            lastPrice[holding.Code] = p.PrevClose;
        }

        for (var minute = OpenMinute; minute <= lastMinute; minute++)
        {
            if (byMinute.TryGetValue(minute, out var due))
            {
                foreach (var trade in due)
                {
                    var rate = trade.Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase) ? hkdCny : 1;
                    var sign = trade.Side == TradeSide.Buy ? -1 : 1;

                    cash += sign * trade.Shares * trade.Price * rate;

                    positions.TryGetValue(trade.Code, out var held);
                    positions[trade.Code] = trade.Side == TradeSide.Buy ? held + trade.Shares : Math.Max(0, held - trade.Shares);
                }
            }

            foreach (var holding in holdings)
            {
                if (sessions.TryGetValue(holding.Code, out var session) && session.Day == day &&
                    session.TryPrice(minute, out var price))
                {
                    lastPrice[holding.Code] = price;
                }
            }

            var value = 0.0;

            foreach (var holding in holdings)
            {
                var rate = holding.IsHongKong ? hkdCny : 1;

                positions.TryGetValue(holding.Code, out var shares);
                lastPrice.TryGetValue(holding.Code, out var price);

                value += shares * price * rate;
            }

            samples.Add(new PnlSample(minute, value + cash - prevValue, value));
        }

        var peak = samples.Count > 0 ? samples.Max(s => s.Pnl) : 0;
        var trough = samples.Count > 0 ? samples.Min(s => s.Pnl) : 0;
        var atPeak = samples.FirstOrDefault(s => Math.Abs(s.Pnl - peak) < 1e-9)?.Minute ?? OpenMinute;
        var atTrough = samples.FirstOrDefault(s => Math.Abs(s.Pnl - trough) < 1e-9)?.Minute ?? OpenMinute;

        // Recomputed from the assembled samples rather than summed from the positions, so the
        // headline number and the curve's last point cannot disagree.
        var last = samples.Count > 0 ? samples[^1].Pnl : 0;

        var valueNow = 0.0;

        foreach (var holding in holdings)
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
            closed,
            DateTime.Now);
    }

    /// <summary>
    /// The cash a code's day of trading has produced or consumed, in the venue's currency —
    /// negative when it bought more than it sold.
    ///
    /// Used for the per-holding contribution so that each row adds up to the total: a holding
    /// that was sold out of still shows the profit the sale realised.
    /// </summary>
    private static double TradeCash(IEnumerable<PortfolioTrade> trades, string code)
    {
        var cash = 0.0;

        foreach (var trade in trades)
        {
            if (!string.Equals(trade.Code, code, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            cash += (trade.Side == TradeSide.Buy ? -1 : 1) * trade.Shares * trade.Price;
        }

        return cash;
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
