using System.Globalization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One coin's monthly returns, folded out of the daily bars the chart path already fetches.
///
/// Crypto has no monthly endpoint to ask — see the note on <see cref="CryptoCandleLoader"/>,
/// which folds weeks and months out of days for the same reason — so the matrix's months are
/// made here, from the same daily series the chart pages draw. A month's figure is its last
/// daily close against the month before's, which on a coin is exact in a way it would not be
/// for a share: no holidays, no half-days, nothing to adjust for, so a month is its own days'
/// closes and nothing else.
///
/// The whole span the source holds is fetched and the year count is applied later, when the
/// spec is built — the stock matrix asks its endpoint for a decade of months in one request,
/// but a second walk of ten years of days is a minute of requests on a source that answers
/// slowly, and the years are a reading of the months rather than a different fetch.
/// </summary>
public static class CryptoMonthly
{
    /// <summary>
    /// One coin's settled months, oldest first.
    ///
    /// The first month in the walk has no month before it inside the span to be measured
    /// from, so its own return is not emitted — the same rule the stock matrix's endpoint
    /// obeys, and on a coin it costs almost nothing: the range is a decade and the frame
    /// wants at most ten of those years.
    ///
    /// The month in progress is dropped for the reason <see cref="MonthlySeries"/> gives:
    /// kept, it would show half a month's move as the whole month.
    ///
    /// A short history is an answer, not a throw: a coin listed three years ago has three
    /// years of rows, and whether that is enough is the spec builder's question, asked in
    /// words the reader can act on.
    /// </summary>
    public static async Task<(string Name, IReadOnlyList<MonthlyPoint> Series)> FetchAsync(
        CryptoQuotes quotes, CryptoAsset asset, IProgress<string>? progress, CancellationToken cancellation)
    {
        var today = DateOnly.FromDateTime(DateTime.Now);
        var from = today.AddDays(-(CryptoQuotes.YahooMostDays - 1));

        var bars = await quotes.BarsAsync(asset, from, today, progress, cancellation);

        // The last close of each calendar month, in the order the days gave them. A month
        // the range only enters part-way still holds its own month-end, so its close is
        // the real one — the partial month is only ever the first, and only its close is
        // read, as the base the second month is measured against.
        var closes = new List<(string YearMonth, double Close)>();

        foreach (var bar in bars)
        {
            var key = $"{bar.Date.Year}-{bar.Date.Month:00}";

            if (closes.Count > 0 && closes[^1].YearMonth == key)
            {
                closes[^1] = (key, bar.Close);
            }
            else
            {
                closes.Add((key, bar.Close));
            }
        }

        // The month being walked is half a month, not a month.
        var thisMonth = DateTime.Now.ToString("yyyy-MM", CultureInfo.InvariantCulture);

        while (closes.Count > 0 && string.CompareOrdinal(closes[^1].YearMonth, thisMonth) >= 0)
        {
            closes.RemoveAt(closes.Count - 1);
        }

        var series = new List<MonthlyPoint>(Math.Max(0, closes.Count - 1));

        for (var i = 1; i < closes.Count; i++)
        {
            series.Add(new MonthlyPoint(
                closes[i].YearMonth,
                (closes[i].Close / closes[i - 1].Close - 1) * 100));
        }

        return (asset.Display, series);
    }
}
