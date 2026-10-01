using System.Globalization;
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
    /// One stock's daily bars over a range, unconverted.
    ///
    /// Same endpoint and same envelope as <see cref="DailyBarsAsync"/> — the market page and the
    /// stock page ask it different questions of the same rows — so the parsing here follows the
    /// same rules: index-read fields, settled days only, exact range trim. The adjustment is a
    /// parameter because the two pages that buy at a price want <c>hfq</c> (see
    /// <see cref="HistoryWalk"/> for why the forward-adjusted series will not do), while the
    /// pages that only read ratios stay on the default <c>qfq</c>.
    /// </summary>
    public async Task<List<StockBar>> StockBarsAsync(
        string code, DateOnly start, DateOnly end, CancellationToken cancellation,
        string adjustment = "qfq")
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

            foreach (var candidate in UsSuffixCandidates(code))
            {
                try
                {
                    var bars = await FetchStockBarsAsync(candidate, start, end, cancellation, adjustment);

                    if (bars.Count >= FewestBars)
                    {
                        return bars;
                    }
                }
                catch (Exception ex)
                {
                    last = ex;
                }
            }

            throw last ?? new InvalidOperationException($"{code}: no daily bars in that range.");
        }

        return await FetchStockBarsAsync(code, start, end, cancellation, adjustment);
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
    private static (string Endpoint, string Adjustment) TotalReturn(string code) =>
        code.StartsWith("hk") ? (HongKongFqEndpoint, "hfq") :
        code.StartsWith("us") ? (UnitedStatesFqEndpoint, "qfq") :
        (Endpoint, "hfq");

    private async Task<List<StockBar>> FetchStockBarsAsync(
        string code, DateOnly start, DateOnly end, CancellationToken cancellation,
        string adjustment = "qfq")
    {
        var (endpoint, wanted) = adjustment == "hfq" && !Degraded.ContainsKey(code)
            ? TotalReturn(code)
            : (Endpoint, adjustment);

        try
        {
            return await FetchFromAsync(endpoint, wanted, code, start, end, cancellation);
        }
        catch (Exception ex) when (endpoint != Endpoint)
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
            throw new InvalidOperationException($"{code}: no daily bars in the response.");
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
