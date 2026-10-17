using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The annual-returns matrix: coins as rows, calendar years as columns, each cell a coin's return
/// over that year, red up and green down.
///
/// The return of a year is the price at its close against the price at the prior year's close —
/// year-end to year-end, the figure a "best year" line is built from. The source's daily closes are
/// folded into it the same way the monthly matrix folds months: the last daily close of a year is its
/// figure. The current, still-walking year is left off, because a half year read as a whole year is
/// a lie about the size of the move.
///
/// One matrix renderer draws it — the same <see cref="MatrixSpec"/> the share page's compare grid
/// builds — so this page is a loader and a set of choices, nothing about the grid new.
/// </summary>
public static class CryptoAnnual
{
    /// <summary>Fewer than this many full years and the grid is not worth drawing.</summary>
    public const int FewestYears = 2;

    /// <summary>
    /// Builds the matrix from daily prices. The fetch spans the chosen range; every full calendar
    /// year inside it (both its close and the prior year's close in hand) becomes a column.
    /// </summary>
    public static async Task<MatrixSpec> LoadAsync(
        CryptoCaps caps, IReadOnlyList<CryptoAsset> coins, DateOnly from, DateOnly to,
        IProgress<string>? progress, CancellationToken cancellation)
    {
        var series = await CryptoPriceSeries.LoadAsync(caps, coins, from, to, progress, cancellation);

        var fromYear = from.Year;
        var toYear = to.Year;

        // Columns are the full years between, each needing both its own close and the prior year's.
        var years = new List<int>();

        for (var y = fromYear + 1; y < toYear; y++)
        {
            years.Add(y);
        }

        if (years.Count < FewestYears)
        {
            throw new InvalidOperationException(Strings.Get("CryptoAnnualTooFewYears"));
        }

        // Last close of each year, per coin. Dates are ascending, so the last write wins.
        var lastPrice = new Dictionary<int, double>[series.Count];

        for (var c = 0; c < series.Count; c++)
        {
            var dict = new Dictionary<int, double>();

            for (var i = 0; i < series[c].Dates.Length; i++)
            {
                dict[series[c].Dates[i].Year] = series[c].Prices[i];
            }

            lastPrice[c] = dict;
        }

        var cells = new List<MatrixCell>();

        for (var c = 0; c < series.Count; c++)
        {
            for (var yi = 0; yi < years.Count; yi++)
            {
                var y = years[yi];

                if (lastPrice[c].TryGetValue(y, out var end)
                    && lastPrice[c].TryGetValue(y - 1, out var prior) && prior > 0)
                {
                    cells.Add(new MatrixCell(
                        c, yi, (end / prior - 1) * 100, $"{series[c].Asset.Display} {y}"));
                }
            }
        }

        // Column-major: the animation walks year by year, every coin's cell of one year lighting
        // together before the next year begins — the same order the share page's compare grid uses.
        cells = [.. cells.OrderBy(c => c.Column).ThenBy(c => c.Row)];

        // The summary column: each coin's return compounded over the shown years.
        var tail = new List<double>(series.Count);

        for (var c = 0; c < series.Count; c++)
        {
            var factor = 1.0;

            foreach (var y in years)
            {
                if (lastPrice[c].TryGetValue(y, out var end)
                    && lastPrice[c].TryGetValue(y - 1, out var prior) && prior > 0)
                {
                    factor *= end / prior;
                }
            }

            tail.Add((factor - 1) * 100);
        }

        var ranked = Enumerable.Range(0, series.Count)
            .Select(i => (Index: i, Value: tail[i]))
            .OrderByDescending(r => r.Value)
            .ToList();

        var culture = CultureInfo.InvariantCulture;

        string Sign(double v) => (v > 0 ? "+" : string.Empty)
            + v.ToString("0.0", culture) + "%";

        return new MatrixSpec(
            "cmp",
            [.. series.Select(s => s.Asset.Display)],
            [.. years.Select(y => y.ToString(culture))],
            cells,
            Strings.Get("CryptoAnnualTail"),
            tail,
            Strings.Format("CryptoAnnualSpan", years[0], years[^1], years.Count),
            Strings.Format("CryptoAnnualTitle", years[0], years[^1]),
            Strings.Format("CryptoAnnualSubtitle", years.Count),
            [
                (Strings.Get("CryptoAnnualStatBest"), $"{series[ranked[0].Index].Asset.Display} {Sign(ranked[0].Value)}"),
                (Strings.Get("CryptoAnnualStatWorst"), $"{series[ranked[^1].Index].Asset.Display} {Sign(ranked[^1].Value)}"),
                (Strings.Get("CryptoAnnualStatTargets"), Strings.Format("MatrixCountTargets", series.Count)),
                (Strings.Get("CryptoAnnualStatYears"), Strings.Format("MatrixCountYears", years.Count)),
            ]);
    }
}
