using System.Globalization;
using System.Net.Http;
using System.Text.Json;
using AShareMotionStudio.Localization;

namespace AShareMotionStudio.Market;

/// <summary>
/// One month's return of one instrument, `yyyy-MM` plus the per-cent change.
/// </summary>
public sealed record MonthlyPoint(string YearMonth, double Return);

/// <summary>
/// Monthly bars from the same chart endpoint the daily path uses, with `month` in place of
/// `day` in the parameter — one request then holds 130 bars, about eleven years, which is why
/// this is a page of its own rather than a fourth form of the daily page: the two cannot share
/// a range selector without one of them lying about what it controls.
/// </summary>
public static class MonthlySeries
{
    private const string Endpoint = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get";

    /// <summary>How many monthly bars one request returns — a decade and a bit.</summary>
    public const int MostBarsPerRequest = 130;

    /// <summary>
    /// The broad-index presets offered as one-tap buttons, all verified quotable.
    /// </summary>
    public static readonly RaceEntry[] BroadIndices =
    [
        new("sh000001", "上证指数"),
        new("sz399001", "深证成指"),
        new("sh000300", "沪深300"),
        new("sh000905", "中证500"),
        new("sz399006", "创业板指"),
        new("sh000688", "科创50"),
        new("sz399005", "中小100"),
        new("sh000016", "上证50"),
    ];

    /// <summary>
    /// Fetches one instrument's settled months.
    ///
    /// Two cleaning rules, both from the source tool. The last bar is the month in progress —
    /// kept, it would show half a month's move as the whole month — so every bar at or after
    /// the current `yyyy-MM` is dropped. And the first *kept* bar has no prior close inside the
    /// range to divide by, so it yields the first return rather than a point.
    /// </summary>
    public static async Task<(string Name, IReadOnlyList<MonthlyPoint> Series)> FetchAsync(
        HttpClient http, string code, CancellationToken cancellation)
    {
        var iso = CultureInfo.InvariantCulture;
        var parameter = $"{code},month,,,130,qfq";
        var uri = $"{Endpoint}?param={Uri.EscapeDataString(parameter)}";

        using var response = await http.GetAsync(uri, cancellation);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        var root = json.RootElement;

        if (!root.TryGetProperty("code", out var status) || status.GetInt32() != 0)
        {
            throw new InvalidOperationException(Strings.Get("MatrixMonthlyUnavailable"));
        }

        if (!root.TryGetProperty("data", out var data) || !data.TryGetProperty(code, out var node))
        {
            throw new InvalidOperationException(Strings.Get("MatrixMonthlyUnavailable"));
        }

        var bars = node.TryGetProperty("qfqmonth", out var adjusted) && adjusted.GetArrayLength() > 0
            ? adjusted
            : node.TryGetProperty("month", out var plain) ? plain : default;

        if (bars.ValueKind != JsonValueKind.Array || bars.GetArrayLength() < 13)
        {
            throw new InvalidOperationException(Strings.Get("MatrixTooFewMonths"));
        }

        var name = code.ToUpperInvariant();

        if (node.TryGetProperty("qt", out var qt) && qt.TryGetProperty(code, out var meta) &&
            meta.GetArrayLength() > 1 && meta[1].GetString() is { Length: > 0 } known)
        {
            name = known.Replace(" ", string.Empty);
        }

        var rows = new List<(string YearMonth, double Close)>();

        foreach (var bar in bars.EnumerateArray())
        {
            if (bar.ValueKind != JsonValueKind.Array || bar.GetArrayLength() < 3)
            {
                continue;
            }

            var day = bar[0].GetString();

            if (day is not { Length: >= 7 } ||
                !double.TryParse(bar[2].GetString(), NumberStyles.Float, iso, out var close) ||
                close <= 0)
            {
                continue;
            }

            rows.Add((day[..7], close));
        }

        // The current month is still walking; a bar for it is half a month, not a month.
        var thisMonth = DateTime.Now.ToString("yyyy-MM", iso);
        var settled = rows.Where(r => string.CompareOrdinal(r.YearMonth, thisMonth) < 0).ToList();

        if (settled.Count < 13)
        {
            throw new InvalidOperationException(Strings.Get("MatrixTooFewMonths"));
        }

        var series = new List<MonthlyPoint>(settled.Count - 1);

        for (var i = 1; i < settled.Count; i++)
        {
            series.Add(new MonthlyPoint(
                settled[i].YearMonth,
                (settled[i].Close / settled[i - 1].Close - 1) * 100));
        }

        return (name, series);
    }

    /// <summary>
    /// Compounds a run of monthly returns into a range return. Multiplying, not adding: a
    /// +20% month and a −20% month are −4% compounded, and adding them to zero overstates
    /// exactly the volatile ranges a matrix is read for.
    /// </summary>
    public static double Compound(IEnumerable<double> monthlyReturns) =>
        (monthlyReturns.Aggregate(1.0, (product, v) => product * (1 + (v / 100))) - 1) * 100;
}

/// <summary>
/// What the matrix renderer draws, once assembled: the labels, the cells in draw order, the
/// summary column, and the closing statistic cards. Both matrix kinds produce one of these,
/// which is what lets them share a renderer.
/// </summary>
public sealed record MatrixSpec(
    string Kind,
    IReadOnlyList<string> RowLabels,
    IReadOnlyList<string> ColumnLabels,
    IReadOnlyList<MatrixCell> Cells,
    string TailLabel,
    IReadOnlyList<double> Tail,
    string Span,
    string Title,
    string Subtitle,
    IReadOnlyList<(string Label, string Value)> Stats);

/// <summary>One lit cell: its grid coordinates, its value, and the label the header reads out.</summary>
public sealed record MatrixCell(int Row, int Column, double Value, string Label);

/// <summary>Assembles the two matrix kinds from fetched monthly series.</summary>
public static class MatrixSpecs
{
    /// <summary>
    /// The year × month kind: rows are years, columns are Jan–Dec, the tail is the whole year
    /// compounded. The seasonality read — which month tends to pay.
    /// </summary>
    public static MatrixSpec Year(
        string targetName, string targetCode, IReadOnlyList<MonthlyPoint> series, int years)
    {
        var culture = CultureInfo.InvariantCulture;

        IEnumerable<MonthlyPoint> kept = series;

        if (years > 0)
        {
            var minY = DateTime.Now.Year - years + 1;
            kept = series.Where(p => int.Parse(p.YearMonth[..4], culture) >= minY);
        }

        var points = kept.ToList();

        if (points.Count < 6)
        {
            throw new InvalidOperationException(Strings.Get("MatrixTooFewMonths"));
        }

        var yearList = points.Select(p => int.Parse(p.YearMonth[..4], culture)).Distinct().OrderBy(y => y).ToList();

        var cells = points.Select(p => new MatrixCell(
            yearList.IndexOf(int.Parse(p.YearMonth[..4], culture)),
            int.Parse(p.YearMonth[5..7], culture) - 1,
            p.Return,
            p.YearMonth)).ToList();

        var tail = yearList.Select(y => MonthlySeries.Compound(
            points.Where(p => int.Parse(p.YearMonth[..4], culture) == y).Select(p => p.Return))).ToList();

        // Every calendar month's average across the years — the answer to "which month pays".
        var byMonth = new List<double>[12];

        for (var i = 0; i < 12; i++)
        {
            byMonth[i] = [];
        }

        foreach (var p in points)
        {
            byMonth[int.Parse(p.YearMonth[5..7], culture) - 1].Add(p.Return);
        }

        var average = byMonth.Select(a => a.Count > 0 ? a.Average() : 0).ToArray();

        var best = 0;
        var worst = 0;

        for (var i = 1; i < 12; i++)
        {
            if (average[i] > average[best])
            {
                best = i;
            }

            if (average[i] < average[worst])
            {
                worst = i;
            }
        }

        string Sign(double v) => (v > 0 ? "+" : string.Empty) + v.ToString("0.0", culture) + "%";

        return new MatrixSpec(
            "year",
            [.. yearList.Select(y => y.ToString(culture))],
            [.. Enumerable.Range(1, 12).Select(m => m.ToString(culture))],
            cells,
            Strings.Get("MatrixTailYear"),
            tail,
            Strings.Format("MatrixYearSpan", yearList[0], points.Count),
            Strings.Format("MatrixYearTitle", targetName, yearList.Count),
            Strings.Format("MatrixYearSubtitle", targetName, targetCode.ToUpperInvariant()),
            [
                (Strings.Get("MatrixStatBestMonth"), Strings.Format("MatrixMonthValue", best + 1, Sign(average[best]))),
                (Strings.Get("MatrixStatWorstMonth"), Strings.Format("MatrixMonthValue", worst + 1, Sign(average[worst]))),
                (Strings.Get("MatrixStatUpRatio"), Math.Round(points.Count(p => p.Return > 0) * 100.0 / points.Count) + "%"),
                (Strings.Get("MatrixStatBestSingle"), "+" + points.Max(p => p.Return).ToString("0.0", culture) + "%"),
            ]);
    }

    /// <summary>
    /// The instruments × months kind: rows are instruments, columns the last N months they all
    /// share, the tail is the compounded range. The rotation read — who took the baton, when.
    /// </summary>
    public static MatrixSpec Compare(
        IReadOnlyList<(string Code, string Name, IReadOnlyList<MonthlyPoint> Series)> fetched,
        string listLabel, int months)
    {
        var culture = CultureInfo.InvariantCulture;

        // Only the months every instrument has, or one missing cell shifts its whole row.
        var shared = fetched[0].Series.Select(p => p.YearMonth).ToHashSet();

        foreach (var (_, _, series) in fetched.Skip(1))
        {
            shared.IntersectWith(series.Select(p => p.YearMonth));
        }

        var monthList = shared.OrderBy(m => m).TakeLast(months).ToList();

        if (monthList.Count < 3)
        {
            throw new InvalidOperationException(Strings.Get("MatrixTooFewShared"));
        }

        var cells = new List<MatrixCell>();

        for (var row = 0; row < fetched.Count; row++)
        {
            for (var col = 0; col < monthList.Count; col++)
            {
                var hit = fetched[row].Series.FirstOrDefault(p => p.YearMonth == monthList[col]);

                if (hit is not null)
                {
                    cells.Add(new MatrixCell(row, col, hit.Return, $"{fetched[row].Name} {hit.YearMonth}"));
                }
            }
        }

        // Column-major: the animation walks month by month, every instrument's cell of one
        // month lighting together before the next month begins.
        cells = [.. cells.OrderBy(c => c.Column).ThenBy(c => c.Row)];

        var tail = fetched.Select(f =>
            MonthlySeries.Compound(
                monthList.Select(m => f.Series.FirstOrDefault(p => p.YearMonth == m)?.Return ?? 0))).ToList();

        var ranked = Enumerable.Range(0, fetched.Count)
            .Select(i => (Index: i, Value: tail[i]))
            .OrderByDescending(r => r.Value)
            .ToList();

        string Sign0(double v) => (v > 0 ? "+" : string.Empty) + v.ToString("0", culture) + "%";

        return new MatrixSpec(
            "cmp",
            [.. fetched.Select(f => f.Name)],
            [.. monthList.Select(m => m.Length >= 7 ? m[2..].Replace("-", "/") : m)],
            cells,
            Strings.Get("MatrixTailTotal"),
            tail,
            Strings.Format("MatrixCmpSpan", monthList[0], monthList[^1], monthList.Count),
            Strings.Format("MatrixCmpTitle", listLabel),
            Strings.Format("MatrixCmpSubtitle", listLabel),
            [
                (Strings.Get("MatrixStatChampion"), $"{fetched[ranked[0].Index].Name} {Sign0(ranked[0].Value)}"),
                (Strings.Get("MatrixStatLast"), $"{fetched[ranked[^1].Index].Name} {Sign0(ranked[^1].Value)}"),
                (Strings.Get("MatrixStatTargets"), Strings.Format("MatrixCountTargets", fetched.Count)),
                (Strings.Get("MatrixStatSpan"), Strings.Format("MatrixCountMonths", monthList.Count)),
            ]);
    }
}
