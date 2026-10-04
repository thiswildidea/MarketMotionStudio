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
/// <param name="Day">Which session this is, `yyyy-MM-dd`. The endpoint keeps five and no date
/// picker is offered, so the frame has to say which of them it is showing.</param>
/// <param name="Labels">Clock labels, `09:30` … `15:00`.</param>
/// <param name="CumulativeYi">Running turnover in 亿元, same length as <paramref name="Labels"/>.</param>
public sealed record IntradayTurnover(
    string Code, string Name, string Day, IReadOnlyList<string> Labels, IReadOnlyList<double> CumulativeYi)
{
    /// <summary>The day's total, which is the last running total — not a sum of the minutes.</summary>
    public double TotalYi => CumulativeYi.Count > 0 ? CumulativeYi[^1] : 0;

    /// <summary>How many minutes the session is drawn across.</summary>
    public int Count => Labels.Count;

    /// <summary>The clock label where the afternoon resumes — the lunch break's right edge.</summary>
    public string NoonLabel => "13:00";

    /// <summary>The clock label where the morning ends — the lunch break's left edge.</summary>
    public string MorningLabel => "11:30";

    /// <summary>Where the last half hour starts, which is the part of the day traders mean by 尾盘.</summary>
    public string CloseLabel => "14:30";

    /// <summary>
    /// The running total as at a clock label, taking the last minute at or before it.
    ///
    /// "At or before" because these labels are minutes that were *reported*, and a session
    /// need not report the exact minute being asked about — asking for 11:30 on a day whose
    /// last morning minute is 11:29 must answer with 11:29's total, not with zero.
    /// </summary>
    public double AsAt(string clock)
    {
        var last = 0.0;

        for (var i = 0; i < Labels.Count; i++)
        {
            if (string.CompareOrdinal(Labels[i], clock) > 0)
            {
                break;
            }

            last = CumulativeYi[i];
        }

        return last;
    }

    /// <summary>Traded in the morning session — everything up to the lunch break.</summary>
    public double MorningYi => AsAt(MorningLabel);

    /// <summary>Traded after the lunch break. The day's total less the morning, so the two add up
    /// to the whole rather than each being rounded on its own.</summary>
    public double AfternoonYi => Math.Max(0, TotalYi - MorningYi);

    /// <summary>Traded in the last half hour, which is the part of a session traders mean by 尾盘.</summary>
    public double CloseRunYi => Math.Max(0, TotalYi - AsAt(CloseLabel));

    /// <summary>A part as a percentage of the day, or zero on a day that traded nothing.</summary>
    public double Share(double part) => TotalYi > 0 ? (part / TotalYi) * 100 : 0;

    /// <summary>The first index at or after a clock label, or -1 if the day ends before it.</summary>
    public int IndexAtOrAfter(string clock)
    {
        for (var i = 0; i < Labels.Count; i++)
        {
            if (string.CompareOrdinal(Labels[i], clock) >= 0)
            {
                return i;
            }
        }

        return -1;
    }
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
        CancellationToken cancellation,
        string? name = null)
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

        // The endpoint names the day as 20260930 and the frame prints 2026-09-30 in every
        // locale — see TurnoverRenderer.Iso for why a date here is never left to the culture.
        var stamp = chosen.Id.Length == 8
            ? $"{chosen.Id[..4]}-{chosen.Id[4..6]}-{chosen.Id[6..]}"
            : chosen.Id;

        return new IntradayTurnover(code, name ?? code.ToUpperInvariant(), stamp, labels, amounts);
    }

    /// <summary>
    /// Adds several instruments into one running total, minute by minute.
    ///
    /// **The axis is the longest series, not the intersection of them all.** A cumulative curve
    /// must never fall, and an instrument whose minute is missing has not traded *nothing* in that
    /// minute — it has simply not reported one since the minute before. Its last known running
    /// total is therefore carried forward, which keeps the sum monotonic. Intersecting would drop
    /// the minutes only one of them had, and on a board whose whole subject is the shape of a
    /// session, silently removing minutes is silently removing the shape.
    ///
    /// <para>
    /// Subtraction is carried rather than applied by the caller, because the main boards are
    /// derived — the Shanghai main board is the exchange less its STAR board — and doing that
    /// difference after the curves were drawn would be a second, differently-rounded answer to a
    /// question this one already answers exactly.
    /// </para>
    /// </summary>
    /// <param name="label">What the combined curve is, for its title and its file name.</param>
    /// <param name="adds">Instruments whose amounts are added.</param>
    /// <param name="subtracts">Instruments whose amounts are taken away.</param>
    public static IntradayTurnover Combine(
        string label,
        IReadOnlyList<IntradayTurnover> adds,
        IReadOnlyList<IntradayTurnover> subtracts)
    {
        var axis = adds.Concat(subtracts).MaxBy(s => s.Labels.Count)
            ?? throw new ArgumentException("an empty basket has no session to draw", nameof(adds));

        var summed = new List<double>(axis.Labels.Count);

        for (var i = 0; i < axis.Labels.Count; i++)
        {
            var total = 0.0;

            foreach (var part in adds)
            {
                total += At(part, axis.Labels[i]);
            }

            foreach (var part in subtracts)
            {
                total -= At(part, axis.Labels[i]);
            }

            summed.Add(Math.Max(0, total));
        }

        return new IntradayTurnover(axis.Code, label, axis.Day, axis.Labels, summed);
    }

    /// <summary>
    /// One series' running total at a minute, carrying the last known one forward.
    ///
    /// Not <c>TryGetValue</c>: a minute this series does not carry is a minute it has not
    /// reported, and the honest thing to plot is where it last stood, not zero.
    /// </summary>
    private static double At(IntradayTurnover series, string label)
    {
        var at = -1;

        for (var i = 0; i < series.Labels.Count; i++)
        {
            if (string.Equals(series.Labels[i], label, StringComparison.Ordinal))
            {
                at = i;
                break;
            }
        }

        if (at >= 0)
        {
            return series.CumulativeYi[at];
        }

        // Walked backwards rather than binary-searched: the axis is in clock order and the
        // minute wanted is nearly always the next one along, so the first comparison usually
        // answers it — and a bisection here would need the axis to be sorted, which is an
        // assumption about the source that nothing else in this file makes.
        for (var i = series.Labels.Count - 1; i >= 0; i--)
        {
            if (string.CompareOrdinal(series.Labels[i], label) < 0)
            {
                return series.CumulativeYi[i];
            }
        }

        return 0;
    }

    /// <summary>
    /// A whole board's or basket's session, fetched one instrument at a time and then added.
    ///
    /// **One instrument failing fails the batch.** A combined total that quietly left a member out
    /// is a plausible number that is wrong, and nothing in the frame would say so — the same trap
    /// as a daily board that comes back a row short, where "nine rows answered" and "the list only
    /// ever had six" look identical on screen. The exception names the code and the reason, so the
    /// reader is told which member to drop rather than being shown a smaller total.
    /// </summary>
    public static async Task<IntradayTurnover> LoadBasketAsync(
        HttpClient http,
        IReadOnlyList<string> adds,
        IReadOnlyList<string> subtracts,
        string label,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        if (adds.Count == 0)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverBasketEmpty"));
        }

        var positive = new List<IntradayTurnover>(adds.Count);
        var negative = new List<IntradayTurnover>(subtracts.Count);

        foreach (var code in adds)
        {
            positive.Add(await LoadAsync(http, code, null, progress, cancellation));
        }

        foreach (var code in subtracts)
        {
            negative.Add(await LoadAsync(http, code, null, progress, cancellation));
        }

        return Combine(label, positive, negative);
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
