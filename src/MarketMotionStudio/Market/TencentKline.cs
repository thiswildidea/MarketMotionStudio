using System.Globalization;
using System.IO;
using System.Net.Http;
using System.Text.Json;

namespace MarketMotionStudio.Market;
/// <summary>
/// One trading day, in the two fields this app reads out of a bar.
/// </summary>
/// <param name="TurnoverYi">Turnover in 亿元 (hundreds of millions of yuan).</param>
/// <param name="Close">
/// The closing level. Kept unconverted because the only thing derived from it is the ratio
/// between one day's and the previous day's, where the unit cancels.
/// </param>
public sealed record DailyBar(double TurnoverYi, double Close);

/// <summary>
/// Daily bars from Tencent Finance's chart endpoint, as date → turnover in 亿元
/// (hundreds of millions of yuan).
///
/// The only place this app speaks HTTP to a quote source. Going through
/// <see cref="HttpClient"/> rather than the browser's JSONP trick removes two things
/// the tools this replaces had to live with: there is no same-origin policy to work
/// around, so no callback parameter and no injected script tag, and a failure is an
/// exception with a status code rather than a script that silently did not load.
/// </summary>
public sealed class TencentKline(HttpClient http)
{
    private const string Endpoint = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get";

    /// <summary>
    /// Hong Kong's own adjusted-history endpoint. The general one answers a Hong
    /// Kong code with unadjusted rows whatever adjustment is asked for — and a
    /// listing there splits: 腾讯控股 went one-for-five on 2014-05-15, which
    /// unadjusted is a close of 514.0 falling to 108.8 overnight, minus seventy-nine
    /// per cent on a day the holder lost nothing.
    /// </summary>
    private const string HongKongFqEndpoint = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/hkfqkline/get";

    /// <summary>
    /// The US one, which carries only the forward-adjusted series: there is no
    /// <c>hfqday</c> for a US code anywhere on this source. Apple's four-for-one
    /// split on 2020-08-31 is minus seventy-four per cent unadjusted.
    /// </summary>
    private const string UnitedStatesFqEndpoint = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get";

    /// <summary>
    /// The A-share session ends at 15:00. Five minutes of slack covers the closing
    /// auction being settled into the day's bar.
    /// </summary>
    private static readonly TimeOnly SettledAfter = new(15, 5);

    /// <summary>
    /// One request returns at most this many bars. Asking for more is not refused by
    /// the server — it simply returns this many, which would silently shorten the
    /// range, so the caller is told instead.
    /// </summary>
    public const int MostBarsPerRequest = 640;

    /// <summary>
    /// Fetches one instrument's daily bars over a range.
    /// </summary>
    /// <remarks>
    /// <paramref name="code"/> reaches a URL, so it is checked against the shape a
    /// market code actually has rather than trusted. Every caller in this app passes
    /// a literal, but a value on its way into a request is worth validating whatever
    /// its provenance looks like today.
    /// </remarks>
    public async Task<Dictionary<DateOnly, DailyBar>> DailyBarsAsync(
        string code, DateOnly start, DateOnly end, CancellationToken cancellation)
    {
        if (!IsMarketCode(code))
        {
            throw new ArgumentException($"Not a market code: {code}", nameof(code));
        }

        if (start >= end)
        {
            throw new ArgumentException("The start date must fall before the end date.", nameof(start));
        }

        // The endpoint ignores the start date in the parameter and returns the last
        // `count` bars ending at the end date, so `count` is what decides how far back
        // it reaches. Counting calendar days over-fetches, because weekends and
        // holidays are not bars — which is what we want: the range is then trimmed
        // exactly, below, rather than approximately by the server.
        var span = end.DayNumber - start.DayNumber;
        var count = Math.Clamp(span, 5, MostBarsPerRequest);

        var iso = CultureInfo.InvariantCulture;
        var parameter = $"{code},day,{start:yyyy-MM-dd},{end:yyyy-MM-dd},{count.ToString(iso)},qfq";
        var uri = $"{Endpoint}?param={Uri.EscapeDataString(parameter)}";

        using var response = await http.GetAsync(uri, cancellation);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        // The response is served as text/html despite being JSON, so the content type
        // is no use as a check. The envelope's own code is.
        var root = json.RootElement;

        if (!root.TryGetProperty("code", out var status) || status.GetInt32() != 0)
        {
            var message = root.TryGetProperty("msg", out var msg) ? msg.GetString() : null;
            throw new InvalidOperationException($"{code}: {message ?? "the quote source reported a failure"}");
        }

        if (!root.TryGetProperty("data", out var data) || !data.TryGetProperty(code, out var node))
        {
            throw new InvalidOperationException($"{code}: the response carried no data for this code.");
        }

        // Adjusted bars where they exist. An index has no adjustment and carries only
        // `day`; a stock carries both, and the adjusted series is the comparable one.
        var bars = node.TryGetProperty("qfqday", out var adjusted) && adjusted.GetArrayLength() > 0
            ? adjusted
            : node.TryGetProperty("day", out var plain) ? plain : default;

        if (bars.ValueKind != JsonValueKind.Array || bars.GetArrayLength() == 0)
        {
            throw new InvalidOperationException($"{code}: no daily bars in the response.");
        }

        var series = new Dictionary<DateOnly, DailyBar>();

        foreach (var bar in bars.EnumerateArray())
        {
            // Read by index and only the fields that matter. The bar is a heterogeneous
            // array — field 6 is an empty JSON object — so it cannot be deserialized as an
            // array of strings, and a parser that assumes it can fails on every response
            // rather than on an unusual one.
            if (bar.ValueKind != JsonValueKind.Array || bar.GetArrayLength() < 9)
            {
                continue;
            }

            if (!DateOnly.TryParseExact(bar[0].GetString(), "yyyy-MM-dd", out var day) ||
                !double.TryParse(bar[2].GetString(), NumberStyles.Float, iso, out var close) ||
                !double.TryParse(bar[8].GetString(), NumberStyles.Float, iso, out var wan))
            {
                continue;
            }

            if (day < start || day > end || !IsSettled(day))
            {
                continue;
            }

            // Turnover converted from 万元 to 亿元, the unit the market is quoted in and the
            // one the animation labels its axis with. The close is kept as it comes, because
            // what is derived from it is a ratio between two of them.
            series[day] = new DailyBar(wan / 10_000d, close);
        }

        return series;
    }

    /// <summary>
    /// Whether a day's bar is finished.
    ///
    /// Before the close, the current day's bar holds only its opening auction — a
    /// figure that can be under one per cent of the day's eventual turnover. Drawn, it
    /// is a bar lying flat against the axis at the end of the chart, which reads as a
    /// market that collapsed rather than as a day still in progress.
    /// </summary>
    private static bool IsSettled(DateOnly day) =>
        day < DateOnly.FromDateTime(DateTime.Now) ||
        TimeOnly.FromDateTime(DateTime.Now) >= SettledAfter;

    /// <summary>
    /// One daily bar of a single stock, in the units the endpoint hands them over.
    ///
    /// Raw rather than converted because the volume field's unit is not fixed: for most
    /// listings it is lots (手) and for STAR-market ones it is shares, and deciding which
    /// needs the close and the amount beside it. See <see cref="StockSeries"/> for where that
    /// decision is made — it is a property of a whole series, not of one bar.
    /// </summary>
    public sealed record StockBar(DateOnly Date, double Close, double RawVolume, double TurnoverRate, double AmountWan);

    /// <summary>
    /// One candle: the four prices a bar is drawn from, and how much traded.
    ///
    /// Its own record rather than a wider <see cref="StockBar"/>, because the two
    /// answer different questions. That one keeps whatever the row carried so a
    /// caller can decide what the volume means; this one is what a chart draws,
    /// and a field it cannot draw is a field it has to keep explaining.
    ///
    /// Kept unconverted: the prices are on whatever basis the adjustment asked for
    /// puts them, which is the whole point — a ratio between two of them is the
    /// return a holder earned, and converting first would only put a constant in
    /// the way of every division.
    /// </summary>
    public sealed record CandleBar(
        DateOnly Date, double Open, double High, double Low, double Close, double Volume);

    /// <summary>
    /// One instrument's candles over a range, on the venue's own adjusted series.
    ///
    /// The period is <c>day</c>, <c>week</c> or <c>month</c>, and each is served by
    /// its own block — <c>hfqweek</c>, <c>qfqmonth</c> and so on — so the same
    /// request that gets daily candles gets weekly ones by naming the period
    /// twice: once in the parameter and once in the block read back. All three are
    /// adjusted on every venue this app quotes, which is the reason this is not
    /// derived from daily bars instead: an unadjusted month is a month with a split
    /// in it, and a split is not a move.
    /// </summary>
    /// <param name="count">
    /// How many candles to ask for. One request carries at most
    /// <see cref="MostBarsPerRequest"/> of them, so a longer range is gathered by
    /// asking again for the window ending before the earliest one held — see
    /// <see cref="CandleLoader"/>.
    /// </param>
    public async Task<List<CandleBar>> CandleBarsAsync(
        string code, string period, DateOnly start, DateOnly end, int count, CancellationToken cancellation)
    {
        if (!IsStockCode(code))
        {
            throw new ArgumentException($"Not a stock code: {code}", nameof(code));
        }

        if (start > end)
        {
            throw new ArgumentException("The start date must fall on or before the end date.", nameof(start));
        }

        // A bare US ticker answers with one bar from 2011 rather than with an error,
        // so the venues are tried in turn — see UsSuffixCandidates.
        if (Markets.IsBareUsTicker(code))
        {
            Exception? last = null;

            // What each venue answered, carried into the message. An index written
            // without a suffix goes through here, the venues answer it with a single
            // row, and "no day bars in that range" says nothing about which of the
            // four was asked or what came back — a diagnosis that costs one fetch to
            // collect and is otherwise unobtainable from a log.
            var tried = new List<string>();
            var answered = false;

            foreach (var candidate in UsSuffixCandidates(code))
            {
                try
                {
                    var bars = await FetchCandlesAsync(candidate, period, start, end, count, cancellation);

                    if (bars.Count >= FewestBars)
                    {
                        RememberNameAs(code, candidate);
                        return bars;
                    }

                    answered = true;
                    tried.Add($"{candidate}: {bars.Count}");
                }
                catch (Exception ex)
                {
                    last = ex;
                    tried.Add($"{candidate}: {ex.Message}");
                }
            }

            // A window with no candles in it and a ticker that does not exist answer
            // the same way from here, and the second one is not the more likely of the
            // two. Caught by the walk, which asks its last window before it has
            // finished: the cursor lands back on the range's own start, the source
            // answers from outside that one-day window, every row is trimmed, and an
            // exception here threw away a walk already holding seven hundred candles
            // — on the US codes only, since a Hong Kong or A-share code is one request
            // with nobody guessing at its venue. An empty list lets the walk stop with
            // what it has; a ticker that really does not exist ends at the loader's
            // own "too few candles" guard instead.
            if (answered)
            {
                return [];
            }

            throw last ?? new InvalidOperationException(
                $"{code}: no {period} bars in that range ({string.Join("; ", tried)}).");
        }

        return await FetchCandlesAsync(code, period, start, end, count, cancellation);
    }

    /// <summary>
    /// Bars as they were actually bought and sold — no adjustment of any kind.
    ///
    /// The rest of this class hands back a *ratio* series: `qfq` or `hfq` is what makes a
    /// decade of returns comparable to itself. That is exactly what makes it useless for
    /// comparing **two listings against each other**, which is what the AH page does. The
    /// backward-adjusted series anchors the earliest price and lets every later one grow, so
    /// ICBC's A share comes back at 13.34 when the price on the screen was 8.28 — and a ratio
    /// built from two such series reported a 245% premium on a stock that trades at 26%.
    ///
    /// Empty adjustment at the general endpoint is what returns the plain block: the code in
    /// `CandlesFromAsync` asks for `adjustment + period`, so an empty adjustment asks for
    /// `month`, which is the price that was paid. `hkfqkline` cannot do this — an empty
    /// adjustment there answers with an empty list — so both legs of a cross-market comparison
    /// come through here, where one code path serves A shares, H shares and a currency alike.
    /// </summary>
    public async Task<List<CandleBar>> RawBarsAsync(
        string code, string period, DateOnly start, DateOnly end, int count, CancellationToken cancellation)
    {
        if (start > end)
        {
            throw new ArgumentException("The start date must fall on or before the end date.", nameof(start));
        }

        return await CandlesFromAsync(Endpoint, string.Empty, code, period, start, end, count, cancellation);
    }

    private async Task<List<CandleBar>> FetchCandlesAsync(
        string code, string period, DateOnly start, DateOnly end, int count, CancellationToken cancellation)
    {
        var (endpoint, adjustment) = TotalReturn(code);

        for (var attempt = 1; ; attempt++)
        {
            try
            {
                return await CandlesFromAsync(endpoint, adjustment, code, period, start, end, count, cancellation);
            }
            catch (Exception ex) when (attempt < AdjustedAttempts && IsTransient(ex))
            {
                await Task.Delay(TransientPause * attempt, cancellation);
            }
            catch (Exception ex)
            {
                // The same fallback the daily path makes, and for the same reason: the
                // general endpoint always has the plain rows, and a series refused
                // outright is worse than one drawn from them. A chart with a split day
                // in it is wrong in a way the reader can see; a chart that never
                // appears is wrong in a way nobody can.
                Diagnostics.CrashLog.Note(
                    $"[kline] {endpoint} failed for {code} {period} ({ex.Message}); falling back to {Endpoint}.");

                return await CandlesFromAsync(Endpoint, adjustment, code, period, start, end, count, cancellation);
            }
        }
    }

    private async Task<List<CandleBar>> CandlesFromAsync(
        string endpoint, string adjustment, string code, string period,
        DateOnly start, DateOnly end, int count, CancellationToken cancellation)
    {
        var iso = CultureInfo.InvariantCulture;
        var wanted = Math.Clamp(count, 5, MostBarsPerRequest);
        var parameter = $"{code},{period},{start:yyyy-MM-dd},{end:yyyy-MM-dd},{wanted.ToString(iso)},{adjustment}";
        var uri = $"{endpoint}?param={Uri.EscapeDataString(parameter)}";

        using var response = await http.GetAsync(uri, cancellation);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        var root = json.RootElement;

        if (!root.TryGetProperty("code", out var status) || status.GetInt32() != 0)
        {
            var message = root.TryGetProperty("msg", out var msg) ? msg.GetString() : null;
            throw new InvalidOperationException($"{code}: {message ?? "the quote source reported a failure"}");
        }

        if (!root.TryGetProperty("data", out var data) || !data.TryGetProperty(code, out var node))
        {
            throw new InvalidOperationException($"{code}: the response carried no data for this code.");
        }

        // The adjusted block for the period asked for, falling back to the plain
        // one — which is what an index carries, having no dividend or split to
        // adjust for.
        var bars = node.TryGetProperty(adjustment + period, out var adjusted) && adjusted.GetArrayLength() > 0
            ? adjusted
            : node.TryGetProperty(period, out var plain) ? plain : default;

        // Asked for a window that ends before this listing's history begins — which
        // is what the backward walk in CandleLoader asks on its last pass — the
        // source answers with no block at all, not with an empty one. That is the
        // answer "there is nothing earlier", not a failure: the walk already holds
        // every candle there is, and throwing here would drop the lot. It shows as
        // a chart of 1,969 weekly bars ending in a thrown-away exception otherwise,
        // and only on Hong Kong and US codes, whose weekly and monthly blocks are
        // served differently from the A-share ones.
        if (bars.ValueKind != JsonValueKind.Array || bars.GetArrayLength() == 0)
        {
            return [];
        }

        var name = code.ToUpperInvariant();

        if (node.TryGetProperty("qt", out var qt) && qt.TryGetProperty(code, out var meta) &&
            meta.GetArrayLength() > 1 && meta[1].GetString() is { Length: > 0 } known)
        {
            name = known;
        }

        var series = new List<CandleBar>();

        foreach (var bar in bars.EnumerateArray())
        {
            // Six fields is the least a candle can be read from — the US
            // forward-adjusted row stops after the volume — and every venue's
            // weekly and monthly rows carry the four prices in the same places.
            if (bar.ValueKind != JsonValueKind.Array || bar.GetArrayLength() < 6)
            {
                continue;
            }

            if (!DateOnly.TryParseExact(bar[0].GetString(), "yyyy-MM-dd", out var day) ||
                !double.TryParse(bar[1].GetString(), NumberStyles.Float, iso, out var open) ||
                !double.TryParse(bar[2].GetString(), NumberStyles.Float, iso, out var close) ||
                !double.TryParse(bar[3].GetString(), NumberStyles.Float, iso, out var high) ||
                !double.TryParse(bar[4].GetString(), NumberStyles.Float, iso, out var low))
            {
                continue;
            }

            if (day < start || day > end || !IsSettledFor(day, period))
            {
                continue;
            }

            if (open <= 0 || close <= 0 || high <= 0 || low <= 0)
            {
                continue;
            }

            // A row can arrive with a high below its own low, or a close outside
            // them, from a source that wrote a stale field. Left alone it draws as
            // a candle standing outside its own wick.
            var top = Math.Max(Math.Max(open, close), high);
            var foot = Math.Min(Math.Min(open, close), low);

            series.Add(new CandleBar(day, open, top, foot, close, Field(bar, 5, iso)));
        }

        if (series.Count == 0)
        {
            Diagnostics.CrashLog.Note(
                $"[kline] {code} {period}: {bars.GetArrayLength()} rows, none usable. {uri} first={bars[0].GetRawText()}");
        }

        BarMeta[code] = name;

        return series;
    }

    /// <summary>
    /// Whether a bar is finished, in the period it belongs to.
    ///
    /// A day's bar is settled once its session is over. A week's or a month's is
    /// the week or the month *so far* until its last day has passed, and drawing
    /// it is drawing a candle made of three days and calling it a week — it sits
    /// at the end of the chart as a stub, and reads as a collapse rather than as a
    /// period still running.
    /// </summary>
    private static bool IsSettledFor(DateOnly day, string period)
    {
        var today = DateOnly.FromDateTime(DateTime.Now);

        if (period is "week")
        {
            // Monday as the week's first day, so a week's bar is settled once the
            // following Monday has come.
            var back = ((int)today.DayOfWeek + 6) % 7;

            return day < today.AddDays(-back);
        }

        if (period is "month")
        {
            return day < new DateOnly(today.Year, today.Month, 1);
        }

        return IsSettled(day);
    }

    /// <summary>
    /// One stock's daily bars over a range, unconverted.
    ///
    /// Same endpoint and same envelope as <see cref="DailyBarsAsync"/> — the market page and the
    /// stock page ask it different questions of the same rows — so the parsing here follows the
    /// same rules: index-read fields, settled days only, exact range trim.
    ///
    /// The default adjustment is <c>hfq</c>, the total-return series, and it is the
    /// default rather than an option because there is no page that is better off
    /// without it. The forward-adjusted series rebases itself to today, which for a
    /// heavy payer lands the historical closes below zero — 贵州茅台's whole
    /// 2010-2015 stretch arrives negative on <c>qfq</c>, and a ratio between two
    /// negative numbers is not a return. Where <c>qfq</c> stays positive the two
    /// differ by one constant factor and every ratio drawn from them is identical,
    /// so nothing that was right before is made wrong.
    /// </summary>
    /// <param name="turnover">
    /// Whether the caller draws turnover as well as price. The US forward-adjusted
    /// series stops after the volume and carries no amount, so with this set the
    /// amount is read from the general endpoint and merged in — see
    /// <see cref="FillTurnoverAsync"/>.
    /// </param>
    public async Task<List<StockBar>> StockBarsAsync(
        string code, DateOnly start, DateOnly end, CancellationToken cancellation,
        string adjustment = "hfq", bool turnover = false)
    {
        if (!IsStockCode(code))
        {
            throw new ArgumentException($"Not a stock code: {code}", nameof(code));
        }

        // A single day is a range. Refusing `start == end` looks harmless and is not:
        // <see cref="HistoryWalk"/> walks backwards and its last window is the one
        // between the range's own start and the earliest bar it holds, which is
        // exactly one day wide when the range starts the day before the first bar —
        // which is what "the last thirteen years" is on a market whose first trading
        // day after the range's start falls one day later. Thrown there, it killed a
        // walk that had already gathered three thousand bars, and the page sat on
        // its progress line for ever.
        if (start > end)
        {
            throw new ArgumentException("The start date must fall on or before the end date.", nameof(start));
        }

        // A US ticker typed without its exchange suffix is not quotable as it stands
        // — see UsSuffixCandidates — so the venues are tried in turn and the first
        // that answers with a real history wins. Everything else is one request.
        if (Markets.IsBareUsTicker(code))
        {
            Exception? last = null;
            var answered = false;

            foreach (var candidate in UsSuffixCandidates(code))
            {
                try
                {
                    var bars = await FetchStockBarsAsync(candidate, start, end, cancellation, adjustment, turnover);

                    if (bars.Count >= FewestBars)
                    {
                        RememberNameAs(code, candidate);
                        return bars;
                    }

                    answered = true;
                }
                catch (Exception ex)
                {
                    last = ex;
                }
            }

            // Nothing in this window is not the same as nothing under this name — see
            // the note in CandleBarsAsync, where the same confusion took down a walk
            // that had already finished.
            if (answered)
            {
                return [];
            }

            throw last ?? new InvalidOperationException($"{code}: no daily bars in that range.");
        }

        return await FetchStockBarsAsync(code, start, end, cancellation, adjustment, turnover);
    }

    /// <summary>
    /// A bare US ticker followed by each exchange suffix it might carry, its bare
    /// form last.
    ///
    /// The endpoint answers <c>usAAPL</c> with one bar from 2011 rather than with an
    /// error, which is the worst possible reply: it looks like a listing that hardly
    /// ever trades. Trying the venues is the only way to tell which one the ticker
    /// is on, and the bare form is kept as a last resort so a failure says what was
    /// asked for.
    /// </summary>
    private static IEnumerable<string> UsSuffixCandidates(string code) =>
        Markets.UsSuffixes.Select(s => code + s).Append(code);

    /// <summary>
    /// Fewer bars than this means the response did not really have the instrument.
    /// Used only to tell a resolved US ticker from an unresolved one.
    /// </summary>
    private const int FewestBars = 2;

    /// <summary>
    /// Carries the name learned under one code over to another.
    ///
    /// A bare US ticker is quoted under whichever suffix answered, and that is the
    /// code the name is cached against — while every caller asks for the ticker it
    /// was given. Left alone <see cref="LastName"/> finds nothing and hands back the
    /// code itself, and the frame is titled <c>USAAPL</c> where Apple should be.
    /// </summary>
    private void RememberNameAs(string code, string answered)
    {
        if (!string.Equals(code, answered, StringComparison.Ordinal) &&
            BarMeta.TryGetValue(answered, out var name))
        {
            BarMeta[code] = name;
        }
    }

    /// <summary>
    /// The endpoint and adjustment that hold one code's total-return series.
    ///
    /// <c>hfq</c> is how the two pages that buy at a price ask for "a series whose
    /// ratios are what a holder earned, dividends and splits included" — and the
    /// general endpoint only answers that for an A-share. A Hong Kong code comes
    /// back unadjusted there and is served by its own endpoint; a US code has no
    /// backward-adjusted series on this source at all, only the forward-adjusted
    /// one. The two differ by a single constant factor over the whole series, and
    /// that factor cancels in everything these pages derive: a buy is
    /// <c>amount / price</c> and a marking is <c>shares × price</c>, so the same
    /// constant sits above and below.
    /// </summary>
    public static (string Endpoint, string Adjustment) TotalReturn(string code) =>
        code.StartsWith("hk") ? (HongKongFqEndpoint, "hfq") :
        code.StartsWith("us") ? (UnitedStatesFqEndpoint, "qfq") :
        (Endpoint, "hfq");

    /// <summary>
    /// How many times the venue's own endpoint is asked before this app gives up on
    /// it and takes the unadjusted rows instead.
    ///
    /// Giving up is expensive and permanent — see <see cref="Degraded"/> — so it has
    /// to be an answer, not a mood. A dropped connection or a gateway's busy page is
    /// neither: the endpoint serves the adjusted rows every other time, and losing
    /// them for the rest of the session over one bad round trip is the worse trade,
    /// because what comes back instead is a series whose split days are cliffs.
    /// </summary>
    private const int AdjustedAttempts = 3;

    /// <summary>How long the next attempt waits. Doubling, because a busy server
    /// wants a moment, not a second request in the same millisecond.</summary>
    private static readonly TimeSpan TransientPause = TimeSpan.FromMilliseconds(300);

    /// <summary>
    /// Whether a failure is worth answering with another attempt.
    ///
    /// The distinction is between a request that did not get through and an endpoint
    /// that did answer. The first is a <see cref="HttpRequestException"/> (which
    /// covers a non-success status, since that is what
    /// <c>EnsureSuccessStatusCode</c> throws), a timeout, a broken stream, or a body
    /// that is not JSON at all — a gateway's HTML error page, say. The second is an
    /// <see cref="InvalidOperationException"/>: the source answered with a code that
    /// is not zero, or with no block for the instrument, which is it telling us it
    /// does not serve this code here, and asking again would not change that.
    /// </summary>
    private static bool IsTransient(Exception ex) =>
        ex is HttpRequestException or TaskCanceledException or IOException or JsonException;

    private async Task<List<StockBar>> FetchStockBarsAsync(
        string code, DateOnly start, DateOnly end, CancellationToken cancellation,
        string adjustment, bool turnover)
    {
        var (endpoint, wanted) = adjustment == "hfq" && !Degraded.ContainsKey(code)
            ? TotalReturn(code)
            : (Endpoint, adjustment);

        if (endpoint == Endpoint)
        {
            return await FetchFromAsync(endpoint, wanted, code, start, end, cancellation);
        }

        for (var attempt = 1; ; attempt++)
        {
            try
            {
                var bars = await FetchFromAsync(endpoint, wanted, code, start, end, cancellation);

                return turnover ? await FillTurnoverAsync(bars, code, start, end, cancellation) : bars;
            }
            catch (Exception ex) when (attempt < AdjustedAttempts && IsTransient(ex))
            {
                await Task.Delay(TransientPause * attempt, cancellation);
            }
            catch (Exception ex)
            {
                // The fallback has to stick, or a walk would mix bases: the general
                // endpoint answers these venues with unadjusted rows, so a series whose
                // early pages came from the adjusted endpoint and whose later ones fell
                // back would draw a cliff where the basis changed. One code, one basis.
                Degraded[code] = 1;

                // Only the unadjusted rows are guaranteed to be on the general
                // endpoint, and a plan refused outright is worse than one drawn from
                // them: a code the source knows under a path it does not serve would
                // otherwise fail with a message about the range, which is nowhere near
                // what went wrong.
                Diagnostics.CrashLog.Note(
                    $"[kline] {endpoint} failed for {code} ({ex.Message}); falling back to {Endpoint}.");

                return await FetchFromAsync(Endpoint, adjustment, code, start, end, cancellation);
            }
        }
    }

    /// <summary>
    /// Puts turnover back into a series the adjusted endpoint returned without it.
    ///
    /// The US forward-adjusted series is six fields long and stops at the volume: it
    /// carries no amount and no change rate. Turnover is the one measure an
    /// adjustment does not move — a split divides the price and multiplies the share
    /// count, and the money that changed hands is the same money — so the general
    /// endpoint's figure is the right one, and this is the only way to hold both
    /// measures for a US code in one series. The closes stay where they came from.
    /// </summary>
    private async Task<List<StockBar>> FillTurnoverAsync(
        List<StockBar> bars, string code, DateOnly start, DateOnly end, CancellationToken cancellation)
    {
        if (bars.Count == 0 || bars.Exists(b => b.AmountWan > 0))
        {
            return bars;
        }

        try
        {
            var plain = await FetchFromAsync(Endpoint, "qfq", code, start, end, cancellation);
            var amounts = new Dictionary<DateOnly, double>();

            foreach (var bar in plain)
            {
                if (bar.AmountWan > 0)
                {
                    amounts[bar.Date] = bar.AmountWan;
                }
            }

            return [.. bars.Select(b =>
                amounts.TryGetValue(b.Date, out var amount) ? b with { AmountWan = amount } : b)];
        }
        catch (Exception ex)
        {
            // A price series without turnover still answers the question the page
            // was asked. Refusing to draw it because a second figure is missing is
            // not.
            Diagnostics.CrashLog.Note($"[kline] no turnover for {code} ({ex.Message}); amounts left at zero.");

            return bars;
        }
    }

    private async Task<List<StockBar>> FetchFromAsync(
        string endpoint,
        string adjustment,
        string code, DateOnly start, DateOnly end, CancellationToken cancellation)
    {
        var span = end.DayNumber - start.DayNumber;
        var count = Math.Clamp(span, 5, MostBarsPerRequest);

        var iso = CultureInfo.InvariantCulture;
        var parameter = $"{code},day,{start:yyyy-MM-dd},{end:yyyy-MM-dd},{count.ToString(iso)},{adjustment}";
        var uri = $"{endpoint}?param={Uri.EscapeDataString(parameter)}";

        using var response = await http.GetAsync(uri, cancellation);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        var root = json.RootElement;

        if (!root.TryGetProperty("code", out var status) || status.GetInt32() != 0)
        {
            var message = root.TryGetProperty("msg", out var msg) ? msg.GetString() : null;
            throw new InvalidOperationException($"{code}: {message ?? "the quote source reported a failure"}");
        }

        if (!root.TryGetProperty("data", out var data) || !data.TryGetProperty(code, out var node))
        {
            throw new InvalidOperationException($"{code}: the response carried no data for this code.");
        }

        // The adjusted series named after the adjustment asked for, falling back to
        // the plain one. The fallback is not about the venue any more — Hong Kong and
        // US rows are adjusted now — but about the instrument: an index has no
        // dividend and no split to adjust for, and neither has a trust that has never
        // paid one, so those rows legitimately carry `day` alone.
        var bars = node.TryGetProperty(adjustment + "day", out var wanted) && wanted.GetArrayLength() > 0
            ? wanted
            : node.TryGetProperty("day", out var plain) ? plain : default;

        if (bars.ValueKind != JsonValueKind.Array || bars.GetArrayLength() == 0)
        {
            // An empty reply is a reply, not a failure — the same rule the bare-US-ticker path
            // above already follows, for the same reason.
            //
            // A window can legitimately hold no trading days: one that starts before the listing
            // existed, or one that falls entirely inside a holiday week. The caller has to be able
            // to tell that from a failure, because a walk backwards asks for exactly such a window
            // as its last step and reads an empty answer as "the range is covered" — which is what
            // HistoryWalk's stop condition does. Throwing here is what turned a ten-year
            // market-cap board into a hard failure the moment the walk reached 中国移动, which
            // only listed on the mainland in 2022 and therefore has no rows at all for the window
            // the walk asked for next.
            return [];
        }

        // The stock's name rides along in the envelope's `qt` block, free of a second request.
        var name = code.ToUpperInvariant();

        if (node.TryGetProperty("qt", out var qt) && qt.TryGetProperty(code, out var meta) &&
            meta.GetArrayLength() > 1 && meta[1].GetString() is { Length: > 0 } known)
        {
            name = known;
        }

        var series = new List<StockBar>();

        foreach (var bar in bars.EnumerateArray())
        {
            // A row carries more fields on the general endpoint than on the
            // adjusted ones: the US forward-adjusted series stops after the
            // volume, with no turnover and no change rate behind it, so a bar
            // that demands nine fields reads nothing at all from it. The date and
            // the close are what every row has; the rest is read where it exists.
            if (bar.ValueKind != JsonValueKind.Array || bar.GetArrayLength() < 6)
            {
                continue;
            }

            if (!DateOnly.TryParseExact(bar[0].GetString(), "yyyy-MM-dd", out var day) ||
                !double.TryParse(bar[2].GetString(), NumberStyles.Float, iso, out var close))
            {
                continue;
            }

            var volume = Field(bar, 5, iso);
            var amount = Field(bar, 8, iso);
            var rate = Field(bar, 7, iso);

            if (day < start || day > end || !IsSettled(day))
            {
                continue;
            }

            series.Add(new StockBar(day, close, volume, rate, amount));
        }

        // An empty window is an answer, not a failure — the rows were there, the range
        // simply holds none of them, which is what a range starting inside a holiday
        // week looks like. <see cref="HistoryWalk"/> depends on reading it that way: it
        // walks backwards asking for the window between the range's start and the
        // earliest bar it holds, and stops when that comes back empty. Thrown instead,
        // it would abort a walk that has already gathered years of bars — a plan over
        // "the last five years" failing whenever the start date lands on a weekend or a
        // public holiday, which is roughly a third of the calendar. The genuinely
        // dataless reply — no bars block at all — still throws above, and
        // <see cref="DailyBarsAsync"/> has always answered an empty window this way.
        BarMeta[code] = name;

        return series;
    }

    /// <summary>
    /// The name seen on the last bars fetch for a code, for callers that never made a separate
    /// lookup. Keyed rather than returned because the bars and the name come from one response —
    /// threading both out of one method would mean a tuple whose second half every caller passes on.
    /// </summary>
    private readonly Dictionary<string, string> BarMeta = [];

    /// <summary>
    /// Codes whose own adjusted endpoint has already failed here. Once a code has
    /// fallen back to the general endpoint it stays there for the rest of the
    /// session — see <see cref="FetchStockBarsAsync"/> for why a fallback that
    /// lasted one page would be worse than none.
    ///
    /// Concurrent because the sector page asks for its entrants side by side.
    /// </summary>
    private readonly System.Collections.Concurrent.ConcurrentDictionary<string, byte> Degraded = [];

    public string LastName(string code) => BarMeta.TryGetValue(code, out var name) ? name : code.ToUpperInvariant();

    /// <summary>
    /// One numeric field of a bar, zero when the row is too short to carry it or
    /// when it holds something that is not a number.
    ///
    /// The adjusted endpoints hand back shorter rows than the general one, so
    /// asking for a field by index and trusting it to be there is what turns a
    /// whole series into nothing.
    /// </summary>
    private static double Field(JsonElement bar, int index, IFormatProvider iso) =>
        index < bar.GetArrayLength() &&
        bar[index].ValueKind == JsonValueKind.String &&
        double.TryParse(bar[index].GetString(), NumberStyles.Float, iso, out var value)
            ? value
            : 0d;

    /// <summary>
    /// A stock code is looser than a market code: five digits for Hong Kong, letters for a US
    /// ticker. The prefix still has to be one this app knows how to quote.
    /// </summary>
    private static bool IsStockCode(string code) =>
        code.Length >= 4 &&
        (code.StartsWith("sh") || code.StartsWith("sz") || code.StartsWith("bj") ||
         code.StartsWith("hk") || code.StartsWith("us")) &&
        code[2..].Length > 0;

    /// <summary>
    /// A two-letter venue prefix and six digits, which is every code this app sends.
    /// </summary>
    private static bool IsMarketCode(string code) =>
        code.Length == 8 &&
        char.IsAsciiLetterLower(code[0]) &&
        char.IsAsciiLetterLower(code[1]) &&
        code.AsSpan(2).ContainsOnlyDigits();
}

internal static class SpanDigits
{
    public static bool ContainsOnlyDigits(this ReadOnlySpan<char> span)
    {
        foreach (var c in span)
        {
            if (!char.IsAsciiDigit(c))
            {
                return false;
            }
        }

        return true;
    }
}
