using System.Globalization;
using System.Net.Http;
using System.Text.Json;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One instrument's turnover, built up minute by minute from the open to the close.
///
/// The daily series says *how much* traded on a day and stops there. This one says *when* it
/// traded: the running total from 09:30 to 15:00, which is the shape of a trading day — the
/// heavy opening auction, the thin lunch hour, the rush into the close.
///
/// <para>
/// The amount is field [3] of each minute row, in 元, already cumulative. It is the same number
/// the daily series puts in field [8] in 万元: measured 2026-10-04, 贵州茅台's 2026-09-30 amount
/// is ¥4,797,249,139 at the 15:00 minute against 479,724.66 万元 on the daily row — a ratio of
/// 1.000, and the same for 上证综指, 沪深300 and 五粮液. Two endpoints, one figure, which is
/// what makes it safe to put them on the same axis.
/// </para>
/// </summary>
/// <param name="Code">The instrument, `sh600519` style.</param>
/// <param name="Name">Its name, for a legend and a file name.</param>
/// <param name="Labels">Clock labels, `09:30` … `15:00`.</param>
/// <param name="CumulativeYi">Running turnover in 亿元, same length as <paramref name="Labels"/>.</param>
public sealed record IntradayTurnover(
    string Code, string Name, IReadOnlyList<string> Labels, IReadOnlyList<double> CumulativeYi)
{
    /// <summary>The day's total, which is the last running total — not a sum of the minutes.</summary>
    public double TotalYi => CumulativeYi.Count > 0 ? CumulativeYi[^1] : 0;
}

/// <summary>Why an instrument could not be drawn on the intraday board.</summary>
public enum IntradayDenial
{
    /// <summary>The endpoint has no minute series for it at all.</summary>
    Unavailable,

    /// <summary>
    /// It has minutes but no amount column. Measured 2026-10-04: `bj899050`, the BSE 50, returns
    /// three-field rows — time, price, cumulative volume — where every other board returns four.
    /// Adding its volume to a basket of amounts would be adding a count to a sum of money, so it
    /// is refused rather than approximated.
    /// </summary>
    NoAmount,

    /// <summary>Too few minutes to be a day. A day in progress holds a dozen.</summary>
    TooFew,
}

public static class TurnoverIntraday
{
    private const string MinuteEndpoint = "https://web.ifzq.gtimg.cn/appstock/app/day/query";

    /// <summary>
    /// The last minute that counts. The endpoint pads a settled day out to 15:30, and that half
    /// hour is **not** part of the session — it carries the after-hours fixed-price trades, which
    /// the daily figure also leaves out. Measured on 贵州茅台 2026-09-30: ¥47.97 亿 at 15:00
    /// against ¥48.02 亿 at 15:30, while the daily row says ¥47.97 亿. Taking the last row
    /// therefore overstates the day by about a tenth of a per cent — small, and wrong in the one
    /// place a reader can check the page against a quote.
    /// </summary>
    private const string CloseAt = "1500";

    /// <summary>
    /// How many minutes a settled day holds. A day still in progress holds a fraction of that,
    /// and drawing one as if it were a whole day is a curve that stops halfway up the frame with
    /// nothing saying why.
    /// </summary>
    private const int SettledMinutes = 200;

    /// <summary>
    /// How many past sessions the endpoint keeps. It is five, and it is a property of the source
    /// rather than a choice — so the board offers those five and no date picker, because a picker
    /// that promises a date the source has already dropped is a picker that cannot be satisfied.
    /// </summary>
    public const int KeptDays = 5;

    public static async Task<IntradayTurnover> LoadAsync(
        HttpClient http,
        string code,
        string? wantedDay,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        progress?.Report(Strings.Format("TurnoverIntradayFetching", code.ToUpperInvariant()));

        var uri = $"{MinuteEndpoint}?code={Uri.EscapeDataString(code)}";

        using var response = await http.GetAsync(uri, cancellation);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        var root = json.RootElement;

        if (!root.TryGetProperty("code", out var status) || status.GetInt32() != 0 ||
            !root.TryGetProperty("data", out var data) || !data.TryGetProperty(code, out var node) ||
            !node.TryGetProperty("data", out var days) || days.GetArrayLength() == 0)
        {
            throw new IntradayUnavailableException(IntradayDenial.Unavailable, code);
        }

        var available = new List<(string Id, JsonElement Node, int Points)>();

        foreach (var day in days.EnumerateArray())
        {
            if (!day.TryGetProperty("date", out var date) || date.GetString() is not { Length: 8 } id)
            {
                continue;
            }

            var points = day.TryGetProperty("data", out var rows) ? rows.GetArrayLength() : 0;
            available.Add((id, day, points));
        }

        if (available.Count == 0)
        {
            throw new IntradayUnavailableException(IntradayDenial.Unavailable, code);
        }

        // The default is the latest *settled* day, unless one was asked for by name.
        var chosen = available.FirstOrDefault(d => d.Id == wantedDay);

        if (chosen.Node.ValueKind == JsonValueKind.Undefined)
        {
            chosen = available.FirstOrDefault(d => d.Points > SettledMinutes);
        }

        if (chosen.Node.ValueKind == JsonValueKind.Undefined)
        {
            chosen = available[^1];
        }

        var rows2 = chosen.Node.GetProperty("data").EnumerateArray()
            .Select(r => r.GetString())
            .Where(s => s is not null)
            .Select(s => s!.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries))
            .Where(f => f.Length >= 4)
            .Where(f => string.CompareOrdinal(f[0].Length >= 4 ? f[0][..4] : f[0], CloseAt) <= 0)
            .ToArray();

        if (rows2.Length == 0)
        {
            // Distinguishing this from `Unavailable` matters: an instrument the endpoint knows but
            // refuses to price is a different problem from one it has never heard of, and only one
            // of them will ever start working.
            var any = chosen.Node.GetProperty("data").EnumerateArray()
                .Select(r => r.GetString())
                .Where(s => s is not null)
                .Select(s => s!.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries))
                .FirstOrDefault();

            throw new IntradayUnavailableException(
                any is { Length: < 4 } ? IntradayDenial.NoAmount : IntradayDenial.TooFew, code);
        }

        var iso = CultureInfo.InvariantCulture;
        var labels = new List<string>(rows2.Length);
        var amounts = new List<double>(rows2.Length);

        foreach (var row in rows2)
        {
            if (!double.TryParse(row[3], NumberStyles.Float, iso, out var yuan))
            {
                continue;
            }

            labels.Add(row[0].Length >= 4 ? row[0][..2] + ":" + row[0][2..4] : row[0]);
            amounts.Add(yuan / 1e8);
        }

        if (amounts.Count < 10)
        {
            throw new IntradayUnavailableException(IntradayDenial.TooFew, code);
        }

        return new IntradayTurnover(code, code.ToUpperInvariant(), labels, amounts);
    }
}

/// <summary>
/// An instrument that cannot appear on the intraday board, and why — carried as a value rather
/// than a message because the caller decides whether one absent row is fatal.
/// </summary>
public sealed class IntradayUnavailableException : Exception
{
    public IntradayUnavailableException(IntradayDenial denial, string code)
        : base($"{code}: {denial}")
    {
        Denial = denial;
        Code = code;
    }

    public IntradayDenial Denial { get; }

    public string Code { get; }
}
