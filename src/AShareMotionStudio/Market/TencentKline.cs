using System.Globalization;
using System.Net.Http;
using System.Text.Json;

namespace AShareMotionStudio.Market;

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
