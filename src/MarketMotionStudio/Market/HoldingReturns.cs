using System.Globalization;
using System.Net.Http;
using System.Text.Json;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// How finely a range is drawn.
///
/// Two grains, and the choice between them is the reader's own span rather than a preference:
/// an hour is made of minutes and a year is made of closes, and drawing the other one either way
/// either asks the source for four hundred days of minute rows it does not have, or lays ten
/// years out as two hundred and forty points nobody can read a week inside.
/// </summary>
public enum ReturnGrain
{
    /// <summary>One point per minute, along the recent sessions the source still carries.</summary>
    Session = 0,

    /// <summary>One point per trading day, at its close.</summary>
    Daily = 1,
}

/// <summary>
/// One point of the curve: the book's worth and what it had made by then.
///
/// <paramref name="Minute"/> is negative for a daily point, which is the close of
/// <paramref name="Day"/>; anything else is minutes since midnight on that day — 570 is 09:30.
/// One constant would have been tidier and wrong: a daily curve stamped 15:00 would claim an
/// afternoon it never drew.
/// </summary>
/// <param name="Day">The trading day.</param>
/// <param name="Minute">Minutes since midnight, or negative for the day's close.</param>
/// <param name="Value">What the holdings were worth, in yuan.</param>
/// <param name="Pnl">What the book had made since the range began, in yuan, after every fee.</param>
public sealed record ReturnSample(DateOnly Day, int Minute, double Value, double Pnl)
{
    /// <summary>Whether this point stands for a whole day rather than a minute inside one.</summary>
    public bool IsClose => Minute < 0;

    /// <summary>`09:30` for a minute, the day itself for a close.</summary>
    public string Clock => Minute < 0
        ? Day.ToString("M/d", CultureInfo.InvariantCulture)
        : $"{Minute / 60:00}:{Minute % 60:00}";
}

/// <summary>
/// The book at one point: what each position held, what it cost, and where it was marked.
///
/// The pages' lists read this while the animation runs, so the rows under the curve are the rows
/// the curve at that minute was drawn from. Reading the *last* moment instead would put today's
/// five thousand shares beside a curve holding eight thousand.
/// </summary>
public sealed record ReturnMoment(
    DateOnly Day,
    int Minute,
    IReadOnlyDictionary<string, double> Shares,
    IReadOnlyDictionary<string, double> Costs,
    IReadOnlyDictionary<string, double> Marks);

/// <summary>A fill placed on the axis: which trade, and which sample it was applied at.</summary>
public sealed record ReturnFill(PortfolioTrade Trade, int Slot);

/// <summary>One position, as the range treated it.</summary>
/// <param name="Code">The instrument.</param>
/// <param name="Name">Its name at the source.</param>
/// <param name="Shares">Shares held at the end of the range.</param>
/// <param name="Opening">Shares held when the range began.</param>
/// <param name="Cost">Diluted cost per share at the end, in the venue's currency.</param>
/// <param name="Opened">Where it was marked when the range began, in the venue's currency.</param>
/// <param name="Last">Where it was marked at the end.</param>
/// <param name="Pnl">What it contributed to the range's profit, in yuan.</param>
/// <param name="Value">What it is worth at the end, in yuan.</param>
/// <param name="Priced">Whether the range ever had a price for it.</param>
public sealed record ReturnRow(
    string Code,
    string Name,
    double Shares,
    double Opening,
    double Cost,
    double Opened,
    double Last,
    double Pnl,
    double Value,
    bool Priced)
{
    /// <summary>Whether this is a Hong Kong listing, and therefore priced in dollars.</summary>
    public bool IsHongKong => Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase);

    /// <summary>Whether the range sold it out — still a row, because its sale made money.</summary>
    public bool Closed => Shares <= 0;
}

/// <summary>
/// A portfolio's history over one span, rebuilt from its snapshot and its fills.
///
/// <para>
/// **The arithmetic is one sentence.** Starting from the snapshot, every fill moves the shares,
/// moves the diluted cost and moves the cash; at each point the book is worth its shares at that
/// point's marks plus the cash the fills have actually moved. The profit is that figure less the
/// same figure at the range's first point — which is what "what I made over this span" means, and
/// the only reading under which the curve starts at zero every time.
/// </para>
///
/// <para>
/// **Measured against the first point and not against the cost.** The broker answers "how much of
/// this is profit" against what the shares cost, which is right for a position and useless for a
/// span: any range not containing the purchase would open on a number that is really last year's.
/// Starting from zero is also what makes two spans comparable — the next question after "how did
/// June go".
/// </para>
///
/// <para>
/// **The prices are the ones that were actually paid.** No adjustment: a position is a number of
/// shares, and an adjusted price series is not something anyone can hold — 中国平安's forward-
/// adjusted closes go negative years back. A dividend therefore shows here as the price falling,
/// which is what happened to anybody who marked their shares on the day, and the alternative
/// would be a claim about income this app cannot see the records of.
/// </para>
/// </summary>
/// <param name="From">The first day drawn, never earlier than the snapshot's own.</param>
/// <param name="To">The last day drawn.</param>
/// <param name="Grain">Minutes or closes — see <see cref="ReturnGrain"/>.</param>
/// <param name="Samples">The curve, in time order.</param>
/// <param name="Moments">The book, point by point, alongside it.</param>
/// <param name="Rows">Every position, priced, including ones closed out during the range.</param>
/// <param name="StartEquity">What the whole thing was worth at the first point, in yuan.</param>
/// <param name="Last">The profit at the last point, in yuan.</param>
/// <param name="Peak">The best it reached.</param>
/// <param name="Trough">The worst.</param>
/// <param name="HkdCny">The rate used, or zero with no Hong Kong position.</param>
/// <param name="Fills">Every fill the range carried, each with the sample it lands on — the count,
/// the frame's "成交 N 笔", and the markers on the curve all come from this one list.</param>
/// <param name="Unpriced">Instruments the range found no price for.</param>
/// <param name="FetchedAt">When this was read.</param>
/// <param name="Opening">Shares held at the **previous trading day's close** — the book the range
/// begins on, before any fill of its own first day.</param>
/// <param name="OpeningCosts">The diluted cost per share at that same moment.</param>
public sealed record ReturnHistory(
    DateOnly From,
    DateOnly To,
    ReturnGrain Grain,
    IReadOnlyList<ReturnSample> Samples,
    IReadOnlyList<ReturnMoment> Moments,
    IReadOnlyList<ReturnRow> Rows,
    double StartEquity,
    double Last,
    double Peak,
    double Trough,
    double HkdCny,
    IReadOnlyList<ReturnFill> Fills,
    IReadOnlyList<string> Unpriced,
    DateTime FetchedAt,
    IReadOnlyDictionary<string, double>? Opening = null,
    IReadOnlyDictionary<string, double>? OpeningCosts = null)
{
    /// <summary>The range's return: profit over what the book was worth when it began.</summary>
    public double ReturnPct => StartEquity > 0 ? (Last / StartEquity) * 100 : 0;

    /// <summary>What the holdings are worth at the last point, in yuan.</summary>
    public double EndValue => Samples.Count > 0 ? Samples[^1].Value : 0;

    /// <summary>How many positions still hold anything.</summary>
    public int OpenPositions => Rows.Count(r => r.Shares > 0);

    /// <summary>Whether there is a curve to draw.</summary>
    public bool Ready => Samples.Count > 1;
}

/// <summary>
/// Rebuilds a portfolio's history over any span, for every page that draws one.
///
/// <para>
/// **One engine, two pages.** The double-screen frame and the returns page ask the same question
/// of the same figures, and an answer that agreed to within a rounding error depending on which
/// door you came in by would be worse than either being wrong: nothing would look broken. Both
/// read this class and nothing else does the arithmetic.
/// </para>
///
/// <para>
/// **Nothing here skips a trade.** Every fill between the snapshot and the range's end is applied
/// at its own minute, in order, whether or not the instrument still has prices — a position sold
/// mid-range must stop being counted from that minute, and a position bought mid-range must be
/// there before it is worth anything.
/// </para>
///
/// <para>
/// **A start earlier than the snapshot is pulled forward to it.** Before the snapshot there is no
/// book to speak of — the app has never known what those shares were — and drawing a curve there
/// would invent both the position and the profit. The range simply begins where the record does,
/// and both pages say the same thing because both are handed the same <see cref="ReturnHistory.From"/>.
/// </para>
/// </summary>
public static class HoldingReturns
{
    /// <summary>
    /// How wide a span the minute source can still answer.
    ///
    /// Five sessions, measured across every venue this app draws: Shanghai, Shenzhen, Hong Kong
    /// and their indices. Past a week the answer is daily closes, not because minutes would be
    /// nicer to have but because the source has none.
    /// </summary>
    public const int MinuteWindowDays = 7;

    /// <summary>
    /// How far before a range its opening marks are looked up.
    ///
    /// Ten calendar days covers the longest closure either venue takes that is not a trading halt:
    /// a mainland 国庆 week, a Hong Kong 春节 week, and the weekend that follows either. Without it
    /// a range opening the morning one venue was shut marks that venue's shares at nothing — see
    /// the note at the read in <see cref="LoadAsync"/>.
    /// </summary>
    private const int LookBackDays = 10;

    private const string SessionEndpoint = "https://web.ifzq.gtimg.cn/appstock/app/day/query";
    private const string FxSpotEndpoint = "https://qt.gtimg.cn/q=whHKDCNY";

    /// <summary>How many instruments one load reads at once. Small: a book, not a board.</summary>
    private const int Parallel = 4;

    /// <summary>
    /// Which grain a span is drawn at: minutes inside the source's window, closes outside it.
    ///
    /// Decided here rather than by the page so that the two of them cannot disagree about what
    /// "近一周" means — one page offering minutes where the other offered closes is a picture that
    /// answers two questions with one label.
    /// </summary>
    public static ReturnGrain GrainFor(DateOnly from, DateOnly to)
    {
        var today = DateOnly.FromDateTime(DateTime.Now);

        return (to.DayNumber - from.DayNumber) <= MinuteWindowDays &&
               to >= today.AddDays(-MinuteWindowDays)
            ? ReturnGrain.Session
            : ReturnGrain.Daily;
    }

    /// <summary>
    /// Reads one portfolio's span.
    /// </summary>
    /// <param name="http">The shared client.</param>
    /// <param name="kline">The quote source every closing price comes off.</param>
    /// <param name="from">What the reader asked for. Pulled forward to the snapshot's day.</param>
    /// <param name="to">The last day wanted.</param>
    /// <param name="fees">What the fills cost; defaults to the schedule already in force.</param>
    /// <param name="scope">
    /// Which of the two books is being read. <see cref="PortfolioScope.AShare"/> reads the
    /// mainland baseline and leaves every Hong Kong row and every Hong Kong fill out of the
    /// replay, which is what makes the curve an A-share curve rather than a mixed one.
    /// </param>
    public static async Task<ReturnHistory> LoadAsync(
        HttpClient http,
        TencentKline kline,
        DateOnly from,
        DateOnly to,
        IProgress<string>? progress,
        CancellationToken cancellation,
        FeeTable? fees = null,
        PortfolioScope scope = PortfolioScope.WithKong)
    {
        Ledger.EnsureLoaded();

        if (Ledger.BaselineOf(scope) is not { Empty: false } snapshot)
        {
            throw new InvalidOperationException(Strings.Get("PortfolioEmpty"));
        }

        if (to < from)
        {
            (from, to) = (to, from);
        }

        // **The boundary rule, in one line.** A range that opens before the snapshot opens instead
        // at the snapshot's own morning, because before it there is no position to draw. Both pages
        // get the trimmed range back in `From`, so both can say what happened to the request rather
        // than silently answering about a shorter span.
        var start = from < snapshot.Day ? snapshot.Day : from;
        var grain = GrainFor(start, to);

        var schedule = fees ?? FeeTable.Default;

        // **Fills inside the range only.** These are what the samples walk, and a fill that happened
        // before the range's first day is already in the book the range opens on — carrying it here
        // as well applies it twice, which is invisible in the code and very visible in the answer:
        // 超图 read 21,000 shares where the book held 14,450, because the six sessions between the
        // snapshot and the range were added once to the opening and once again on the first sample.
        // **The Hong Kong rows go out with the Hong Kong fills.** A snapshot edited by hand can
        // carry a `hk` row the mainland book has no business holding — importing a whole holdings
        // screen into the mainland baseline is the ordinary way one gets there — and a single one
        // would put a second currency on a curve that is labelled in yuan.
        if (scope is PortfolioScope.AShare)
        {
            snapshot = new HoldingSnapshot(
                snapshot.Day,
                [.. snapshot.Kept.Where(h => !h.IsHongKong)]);
        }

        // **The Hong Kong fills go out with the Hong Kong rows.** The archive keeps every fill the
        // reader ever imported — that is the whole point of it — but a mainland book is not
        // entitled to them: a fill in a currency the curve is not drawn in, at a fee schedule the
        // curve does not charge, on shares the baseline does not hold. Dropped here rather than at
        // import, so that switching back still has them.
        var eligible = scope is PortfolioScope.AShare
            ? Ledger.Archive.Where(t => !t.Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase))
                .ToList()
            : [.. Ledger.Archive];

        var trades = eligible
            .Where(t => ParseDay(t.Day) != DateOnly.MinValue &&
                        ParseDay(t.Day) >= start &&
                        ParseDay(t.Day) <= to)
            .ToList();

        // Everything between the snapshot and the range, applied once, to build the opening book.
        var carries = eligible
            .Where(t => ParseDay(t.Day) != DateOnly.MinValue &&
                        ParseDay(t.Day) >= snapshot.Day &&
                        ParseDay(t.Day) < start)
            .ToList();

        var codes = snapshot.Kept.Select(h => h.Code)
            .Concat(trades.Select(t => t.Code))
            .Concat(carries.Select(t => t.Code))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        progress?.Report(Strings.Get("PortfolioFetchingQuotes"));

        // **Closes are asked for from before the range, not from its first day.** A range that
        // opens on a morning one venue was shut — a Hong Kong holiday that Shanghai traded through
        // is the ordinary case — has no price for that venue's shares on its own first day, and
        // marking them at nothing opens the picture on a book worth less than it was: the whole
        // curve then carries that hole as profit (实测：首点少算港股约 ¥5 万，10-19→10-30 期显示
        // +¥40,152，实际是 −¥13,226). Carrying the last close from before the range is also what
        // "where it was marked when the range began" has always meant.
        var daily = await ReadClosesAsync(kline, codes, start.AddDays(-LookBackDays), to, progress, cancellation);

        var sessions = grain == ReturnGrain.Session
            ? await ReadSessionsAsync(http, codes, start, to, progress, cancellation)
            : new Dictionary<string, SortedDictionary<DateOnly, SortedDictionary<int, double>>>(
                StringComparer.OrdinalIgnoreCase);

        // **The rate is announced only when it is read.** The message used to go out
        // unconditionally, so a pure-mainland span spent its whole read promising an exchange
        // rate it never asked for (实测：A 股区间进度条写「正在读取 HKD/CNY 的分钟价」).
        var rates = codes.Any(c => c.StartsWith("hk", StringComparison.OrdinalIgnoreCase))
            ? await ReadWithNoticeAsync(http, kline, progress, start, to, cancellation)
            : new SortedList<DateOnly, double>();

        return Assemble(snapshot, carries, trades, codes, daily, sessions, rates, grain, start, to, schedule);
    }

    /// <summary>
    /// The arithmetic, with nothing in it that needs the network.
    ///
    /// Pure so it can be read — and checked — without fetching anything, which for a one-line
    /// definition of profit is the only way anybody will ever believe the number.
    /// </summary>
    public static ReturnHistory Assemble(
        HoldingSnapshot snapshot,
        IReadOnlyList<PortfolioTrade> carries,
        IReadOnlyList<PortfolioTrade> trades,
        IReadOnlyList<string> codes,
        IReadOnlyDictionary<string, SortedList<DateOnly, double>> daily,
        IReadOnlyDictionary<string, SortedDictionary<DateOnly, SortedDictionary<int, double>>> sessions,
        SortedList<DateOnly, double> rates,
        ReturnGrain grain,
        DateOnly start,
        DateOnly to,
        FeeTable fees)
    {
        var ordered = trades
            .OrderBy(t => t.Day, StringComparer.Ordinal)
            .ThenBy(t => t.MinuteOfDay)
            .ThenBy(t => t.Time, StringComparer.Ordinal)
            .ToList();

        // The book as the range opens: the snapshot's own rows, then every fill between a snapshot
        // older than the request and the range's first day. Those fills happened, were counted into
        // none of the points drawn, and leaving them out would open the range on a position the
        // reader has not held since the day they happened.
        var shares = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var costs = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        // **Two purses, because the book holds two currencies.** A fill moves cash in the venue's
        // own money, and a Hong Kong sale leaves Hong Kong dollars behind — adding those to a
        // yuan total at par overstates the book by the exchange rate on every such fill (实测：
        // 一笔 HK$22,512 的卖出，按 1:1 记账会让权益虚高约 ¥3,400). Kept apart here, converted
        // at each sample's own rate below.
        var cashCny = 0.0;
        var cashHkd = 0.0;
        var cashByCode = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);

        foreach (var row in snapshot.Kept)
        {
            shares[row.Code] = row.Shares;
            costs[row.Code] = row.Cost;
        }

        foreach (var trade in carries
                     .OrderBy(t => t.Day, StringComparer.Ordinal)
                     .ThenBy(t => t.MinuteOfDay)
                     .ThenBy(t => t.Time, StringComparer.Ordinal))
        {
            Apply(trade, shares, costs, cashByCode, fees, ref cashCny, ref cashHkd);
        }

        // **This is the book the range begins on**, and it is a moment the reader can name: the
        // close of the last session before the range's first day. Every fill before that close has
        // been applied and every fill after it has not, which is what makes it usable as the list's
        // opening figures rather than as "whatever the first sample happened to catch".
        var openingShares = new Dictionary<string, double>(shares, StringComparer.OrdinalIgnoreCase);
        var openingCosts = new Dictionary<string, double>(costs, StringComparer.OrdinalIgnoreCase);

        // The axis: what the span actually has to stand on.
        var slots = new List<(DateOnly Day, int Minute)>();

        if (grain == ReturnGrain.Session && sessions.Count > 0)
        {
            var days = sessions.Values
                .SelectMany(s => s.Keys)
                .Where(d => d >= start && d <= to)
                .Distinct()
                .OrderBy(d => d)
                .ToList();

            foreach (var day in days)
            {
                // The union of the venues' minutes. A book holding both markets trades through Hong
                // Kong's longer afternoon, and an axis that stopped at Shanghai's close would drop
                // the last hour of half the book off the picture for no reason anyone stated.
                var minutes = new SortedSet<int>();

                foreach (var one in sessions.Values)
                {
                    if (one.TryGetValue(day, out var at))
                    {
                        foreach (var minute in at.Keys)
                        {
                            minutes.Add(minute);
                        }
                    }
                }

                foreach (var minute in minutes)
                {
                    slots.Add((day, minute));
                }
            }
        }

        if (slots.Count == 0)
        {
            var fall = daily.Values
                .SelectMany(d => d.Keys)
                .Where(d => d >= start && d <= to)
                .Distinct()
                .OrderBy(d => d)
                .ToList();

            foreach (var day in fall)
            {
                slots.Add((day, -1));
            }
        }

        if (slots.Count == 0)
        {
            throw new InvalidOperationException(Strings.Get("PortfolioNoSession"));
        }

        // Where every code stood before the first point, for the per-row column and for the very
        // first sample's own arithmetic.
        var marks = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var openedAt = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        var priced = new Dictionary<string, bool>(StringComparer.OrdinalIgnoreCase);

        foreach (var code in codes)
        {
            var first = slots[0];
            var at = MarkOf(code, first, sessions, daily);

            marks[code] = at;
            openedAt[code] = at;
            priced[code] = at > 0;
        }

        var samples = new List<ReturnSample>();
        var moments = new List<ReturnMoment>();
        var placed = new List<ReturnFill>();
        var startEquity = 0.0;
        var next = 0;

        foreach (var slot in slots)
        {
            // Every fill stamped at or before this point, applied here and once. Ordered by the
            // clock, because a round trip only adds up if the buy is seen before the sell.
            while (next < ordered.Count && AtOrBefore(ordered[next], slot))
            {
                Apply(ordered[next], shares, costs, cashByCode, fees, ref cashCny, ref cashHkd);

                // The sample this fill belongs to is the one about to be added — a marker drawn
                // anywhere else would sit beside a position that does not include the fill yet.
                placed.Add(new ReturnFill(ordered[next], moments.Count));
                next++;
            }

            foreach (var code in codes)
            {
                if (GrainPriceOf(code, slot, sessions, daily, marks[code]) is { } price)
                {
                    marks[code] = price;
                    priced[code] = true;
                }
            }

            // Converted at the day's own rate, and every code and every cash term on that day is
            // converted with the same one — picking two rates for two terms of one sum is how a
            // number in one currency ends up added to a number in another.
            var rate = RateOf(rates, slot.Day);

            var value = 0.0;

            foreach (var code in codes)
            {
                value += Holding(shares, code) * marks[code] *
                    (code.StartsWith("hk", StringComparison.OrdinalIgnoreCase) ? rate : 1);
            }

            var equity = value + cashCny + (cashHkd * rate);

            if (samples.Count == 0)
            {
                startEquity = equity;
            }

            samples.Add(new ReturnSample(slot.Day, slot.Minute, value, equity - startEquity));
            moments.Add(new ReturnMoment(
                slot.Day,
                slot.Minute,
                new Dictionary<string, double>(shares, StringComparer.OrdinalIgnoreCase),
                new Dictionary<string, double>(costs, StringComparer.OrdinalIgnoreCase),
                new Dictionary<string, double>(marks, StringComparer.OrdinalIgnoreCase)));
        }

        var rows = new List<ReturnRow>();

        foreach (var code in codes)
        {
            var named = snapshot.Kept.FirstOrDefault(h => Same(h.Code, code))?.Name
                ?? Ledger.Archive.FirstOrDefault(t => Same(t.Code, code))?.Name
                ?? code;

            // A row is priced at the last point's rate, which is the one the columns beside it were
            // computed with: the list under the curve has to agree with its last frame.
            var kong = code.StartsWith("hk", StringComparison.OrdinalIgnoreCase);
            var rate = kong ? RateOf(rates, slots[^1].Day) : 1;
            var opening = Holding(openingShares, code);
            var held = Holding(shares, code);

            rows.Add(new ReturnRow(
                code,
                named,
                held,
                opening,
                Holding(costs, code),
                openedAt[code],
                marks[code],
                ((held * marks[code]) - (opening * openedAt[code]) + Holding(cashByCode, code)) * rate,
                held * marks[code] * rate,
                priced[code]));
        }

        var pnl = samples.Select(s => s.Pnl).ToList();
        var last = pnl.Count > 0 ? pnl[^1] : 0;

        return new ReturnHistory(
            slots[0].Day,
            slots[^1].Day,
            slots[0].Minute < 0 ? ReturnGrain.Daily : grain,
            samples,
            moments,
            rows,
            startEquity,
            last,
            pnl.Count > 0 ? Math.Max(0, pnl.Max()) : 0,
            pnl.Count > 0 ? Math.Min(0, pnl.Min()) : 0,
            RateOf(rates, slots[^1].Day),
            placed,
            [.. rows.Where(r => !r.Priced).Select(r => r.Code)],
            DateTime.Now,
            openingShares,
            openingCosts);
    }

    /// <summary>Whether a fill belongs to a point yet.</summary>
    private static bool AtOrBefore(PortfolioTrade trade, (DateOnly Day, int Minute) slot)
    {
        var day = ParseDay(trade.Day);

        if (day != slot.Day)
        {
            return day < slot.Day;
        }

        // A daily point is the day's close, so every fill stamped that day has happened by it. A
        // minute point has not yet seen the fills of its own minute past its own second, but an
        // order ticket carries no seconds that matter to a chart: intraday, `<=` is what puts the
        // 09:35 sale onto the 09:35 sample rather than the one after, which is the one the reader
        // watched it happen on.
        return slot.Minute < 0 || trade.MinuteOfDay <= slot.Minute;
    }

    /// <summary>
    /// One fill, applied where it belongs: to the shares, to the diluted cost and to the cash.
    ///
    /// **Only the shares actually there are sold.** A sale of more than the book holds clamps to
    /// what is there and books that, because money for shares nobody held is not profit — it is a
    /// gap in the record, and quietly paying it out is how a curve invents a gain the reader never
    /// made.
    /// </summary>
    private static void Apply(
        PortfolioTrade trade,
        Dictionary<string, double> shares,
        Dictionary<string, double> costs,
        Dictionary<string, double> cashByCode,
        FeeTable fees,
        ref double cashCny,
        ref double cashHkd)
    {
        var held = Holding(shares, trade.Code);
        var moved = trade.Side == TradeSide.Buy ? trade.Shares : Math.Min(trade.Shares, held);

        // **A fill that moves nothing is not a fill.** It is a record for shares this book never
        // held — something sold before the snapshot was taken, or a code the reader has since
        // closed — and charging it the five-yuan commission minimum takes money off the curve for
        // a trade that did not happen here (实测：两笔无对应股数的卖出各扣 ¥5，区间收益偏了 ¥10).
        // Returning before the cash moves also keeps the position's own contribution honest, since
        // a sale of nothing changes no cost either.
        if (moved <= 0)
        {
            return;
        }

        var gross = moved * trade.Price;
        var fee = trade.Side == TradeSide.Buy
            ? fees.OnBuy(trade.Code, gross)
            : fees.OnSell(trade.Code, gross);

        var flow = trade.Side == TradeSide.Buy ? -(gross + fee) : gross - fee;

        if (FeeTable.IsKong(trade.Code))
        {
            cashHkd += flow;
        }
        else
        {
            cashCny += flow;
        }

        cashByCode[trade.Code] = Holding(cashByCode, trade.Code) + flow;

        costs[trade.Code] = IntradayPnl.Diluted(
            Holding(costs, trade.Code), held, moved, trade, fee);

        shares[trade.Code] = trade.Side == TradeSide.Buy
            ? held + moved
            : Math.Max(0, held - moved);
    }

    /// <summary>
    /// The rate in force on a day, or 1 when there is nothing to convert — which is also the right
    /// answer for a book with no Hong Kong row: multiplying by a rate nobody asked for would be a
    /// change to every mainland figure, however small the rate made it look.
    /// </summary>
    private static double RateOf(SortedList<DateOnly, double> rates, DateOnly day) =>
        rates.Count == 0 ? 1 : FxHistory.RateOn(rates, day, 1);

    /// <summary>A code's number in a dictionary that may not mention it yet.</summary>
    private static double Holding(IReadOnlyDictionary<string, double> from, string code) =>
        from.TryGetValue(code, out var value) ? value : 0;

    /// <summary>The price a code is marked at a point, whichever grain the range is drawn on.</summary>
    private static double? GrainPriceOf(
        string code,
        (DateOnly Day, int Minute) slot,
        IReadOnlyDictionary<string, SortedDictionary<DateOnly, SortedDictionary<int, double>>> sessions,
        IReadOnlyDictionary<string, SortedList<DateOnly, double>> daily,
        double fallback)
    {
        if (slot.Minute >= 0 &&
            sessions.TryGetValue(code, out var days) &&
            days.TryGetValue(slot.Day, out var minutes) &&
            LastAtOrBefore(minutes, slot.Minute) is { } print)
        {
            return print;
        }

        if (daily.TryGetValue(code, out var closes) &&
            LastAtOrBefore(closes, slot.Day) is { } close)
        {
            return close;
        }

        // No price at this point is absence, not a fall to nothing: the shares are still worth what
        // they were worth an hour ago, and a marked-to-zero line is a collapse nobody suffered.
        return fallback > 0 ? fallback : null;
    }

    /// <summary>The same question asked before the first point, for the opening mark.</summary>
    private static double MarkOf(
        string code,
        (DateOnly Day, int Minute) slot,
        IReadOnlyDictionary<string, SortedDictionary<DateOnly, SortedDictionary<int, double>>> sessions,
        IReadOnlyDictionary<string, SortedList<DateOnly, double>> daily) =>
        GrainPriceOf(code, slot, sessions, daily, 0) ?? 0;

    private static double? LastAtOrBefore(SortedDictionary<int, double> prices, int minute)
    {
        double? found = null;

        foreach (var (at, price) in prices)
        {
            if (at > minute)
            {
                break;
            }

            found = price;
        }

        return found;
    }

    private static double? LastAtOrBefore(SortedList<DateOnly, double> closes, DateOnly day)
    {
        double? found = null;

        foreach (var (at, close) in closes)
        {
            if (at > day)
            {
                break;
            }

            found = close;
        }

        return found;
    }

    private static bool Same(string a, string b) => string.Equals(a, b, StringComparison.OrdinalIgnoreCase);

    /// <summary>Reads `yyyy-MM-dd` as a date; the earliest date there is when it is not one.</summary>
    private static DateOnly ParseDay(string text) =>
        DateOnly.TryParseExact(text.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture,
            DateTimeStyles.None, out var day)
            ? day
            : DateOnly.MinValue;

    // ---- fetching ----------------------------------------------------------------------

    /// <summary>
    /// Every instrument's daily closes over the span, unadjusted.
    ///
    /// Read even when the curve is drawn on minutes, because they are also the fallback: a code
    /// whose session went missing — a suspension, a lifting mid-range — is priced off the last
    /// close it has rather than dropping off the book.
    /// </summary>
    private static async Task<Dictionary<string, SortedList<DateOnly, double>>> ReadClosesAsync(
        TencentKline kline,
        IReadOnlyList<string> codes,
        DateOnly start,
        DateOnly end,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        var found = new Dictionary<string, SortedList<DateOnly, double>>(StringComparer.OrdinalIgnoreCase);
        var gate = new SemaphoreSlim(Parallel);
        var done = 0;

        var tasks = codes.Select(async code =>
        {
            await gate.WaitAsync(cancellation);

            try
            {
                var closes = await HistoryWalk.ClosesAsync(
                    kline, code, code, start, end, new Progress<string>(_ => { }), cancellation,
                    adjustment: string.Empty);

                if (closes.Count > 0)
                {
                    lock (found)
                    {
                        found[code] = closes;
                    }
                }
            }
            catch (Exception) when (!cancellation.IsCancellationRequested)
            {
                // One instrument the source will not serve must not take the whole range down. It
                // is priced off whatever it does have, or named as unpriced on the page — better a
                // number slightly short than a page that will not open.
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
    /// Every instrument's recent sessions, minute by minute, for the spans drawn that finely.
    ///
    /// The endpoint answers with the **five latest sessions it still carries**, in either direction
    /// including Hong Kong — which is why a week is drawn on minutes at all, and why nothing longer
    /// can be: there is no further back to ask for.
    /// </summary>
    private static async Task<Dictionary<string, SortedDictionary<DateOnly, SortedDictionary<int, double>>>>
        ReadSessionsAsync(
            HttpClient http,
            IReadOnlyList<string> codes,
            DateOnly start,
            DateOnly end,
            IProgress<string>? progress,
            CancellationToken cancellation)
    {
        var found = new Dictionary<string, SortedDictionary<DateOnly, SortedDictionary<int, double>>>(
            StringComparer.OrdinalIgnoreCase);

        var gate = new SemaphoreSlim(Parallel);
        var done = 0;

        var tasks = codes.Select(async code =>
        {
            await gate.WaitAsync(cancellation);

            try
            {
                var sessions = await ReadSessionsOneAsync(http, code, cancellation);

                if (sessions.Count > 0)
                {
                    lock (found)
                    {
                        found[code] = sessions;
                    }
                }
            }
            catch (Exception) when (!cancellation.IsCancellationRequested)
            {
                // Falling back to closes is the caller's business, and it has them already.
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

    public static async Task<SortedDictionary<DateOnly, SortedDictionary<int, double>>>
        ReadSessionsOneAsync(HttpClient http, string code, CancellationToken cancellation)
    {
        var sessions = new SortedDictionary<DateOnly, SortedDictionary<int, double>>();

        // **The code goes out exactly as it is carried, case and all.** Lower-casing it was
        // harmless for every holding — `hk01024`, `sh601006` are lower-case already — and wrong
        // for every index: `hkHSI` asked as `hkhsi` comes back as an entry called `hkhsi` holding
        // **no sessions at all**, with no error to notice (实测：hkHSI 5 个交易日，hkhsi 0 个).
        // The response keys off the spelling it was asked with, so the only safe request is the
        // one the catalog already spells.
        var uri = $"{SessionEndpoint}?code={Uri.EscapeDataString(code)}";

        using var response = await http.GetAsync(uri, cancellation);

        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        // Keyed by the spelling asked for; a source that re-cases it still answers under one
        // property, and a single-instrument reply has exactly one to take.
        if (!json.RootElement.TryGetProperty("data", out var data) ||
            data.ValueKind != JsonValueKind.Object)
        {
            return sessions;
        }

        var quoted = data.EnumerateObject();

        if (!quoted.MoveNext())
        {
            return sessions;
        }

        var node = data.TryGetProperty(code, out var exact) ? exact : quoted.Current.Value;

        if (!node.TryGetProperty("data", out var days) || days.ValueKind != JsonValueKind.Array)
        {
            return sessions;
        }

        foreach (var day in days.EnumerateArray())
        {
            if (!day.TryGetProperty("date", out var stamp) ||
                stamp.GetString() is not { Length: 8 } date ||
                !DateOnly.TryParseExact(date, "yyyyMMdd", CultureInfo.InvariantCulture,
                    DateTimeStyles.None, out var at) ||
                !day.TryGetProperty("data", out var rows) ||
                rows.ValueKind != JsonValueKind.Array)
            {
                continue;
            }

            var prices = new SortedDictionary<int, double>();

            foreach (var row in rows.EnumerateArray())
            {
                if (row.GetString() is not { } text)
                {
                    continue;
                }

                // Time, price, cumulative volume, cumulative amount. Only the first two are read
                // here: a book is priced, not turned over.
                var fields = text.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);

                if (fields.Length < 2 || fields[0].Length < 4 ||
                    !int.TryParse(fields[0][..2], NumberStyles.Integer, CultureInfo.InvariantCulture, out var hour) ||
                    !int.TryParse(fields[0][2..4], NumberStyles.Integer, CultureInfo.InvariantCulture, out var minute) ||
                    !double.TryParse(fields[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var price) ||
                    price <= 0)
                {
                    continue;
                }

                prices[(hour * 60) + minute] = price;
            }

            if (prices.Count > 0)
            {
                sessions[at] = prices;
            }
        }

        return sessions;
    }

    /// <summary>
    /// The Hong Kong dollar in yuan, **day by day** rather than as one figure.
    ///
    /// A rate from today applied to a year of dollars is a currency that never moved: measured
    /// over the last twelve months 港币 went from 0.913 to 0.848, and every Hong Kong position in
    /// the book had seven per cent taken off it by that alone. So each day is converted at that
    /// day's close, and a day the source has no quote for is carried forward — a rate nobody
    /// recorded is still the rate that was paid.
    /// </summary>
    private static async Task<SortedList<DateOnly, double>> ReadWithNoticeAsync(
        HttpClient http, TencentKline kline, IProgress<string>? progress,
        DateOnly start, DateOnly to, CancellationToken cancellation)
    {
        progress?.Report(Strings.Format("PortfolioFetchingRates", "HKD/CNY"));

        return await ReadHkdCnyAsync(http, kline, start.AddDays(-LookBackDays), to, cancellation);
    }

    private static async Task<SortedList<DateOnly, double>> ReadHkdCnyAsync(
        HttpClient http, TencentKline kline, DateOnly start, DateOnly end, CancellationToken cancellation)
    {
        try
        {
            return await FxHistory.ReadAsync(kline, "whHKDCNY", start, end, cancellation);
        }
        catch (Exception) when (!cancellation.IsCancellationRequested)
        {
            // One spot rate is worse than a history and better than nothing: it is at least today's
            // number rather than a number nobody ever lived through.
            var rates = new SortedList<DateOnly, double>();

            using var response = await http.GetAsync(FxSpotEndpoint, cancellation);

            response.EnsureSuccessStatusCode();

            var fields = Gbk.GetString(await response.Content.ReadAsByteArrayAsync(cancellation))
                .Split('~');

            if (fields.Length > 3 &&
                double.TryParse(fields[3], NumberStyles.Float, CultureInfo.InvariantCulture, out var rate) &&
                rate > 0)
            {
                rates[end] = rate;
            }

            return rates;
        }
    }

    private static readonly System.Text.Encoding Gbk = CreateGbk();

    private static System.Text.Encoding CreateGbk()
    {
        System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);

        return System.Text.Encoding.GetEncoding(936);
    }
}
