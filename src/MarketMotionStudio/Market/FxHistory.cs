using System.Globalization;

namespace MarketMotionStudio.Market;

/// <summary>
/// A currency pair's own history, day by day.
///
/// <para>
/// **A rate has to belong to the day it is used on.** The rest of this app converts at today's
/// rate, which is fine for a page drawing today and quietly wrong for anything longer: measured
/// over the last twelve months 港币 went from 0.913 to 0.848 against the renminbi, and a portfolio
/// holding Hong Kong shares through that lost seven per cent of its value to the currency alone —
/// money no price chart mentions and no position's own return accounts for.
/// </para>
///
/// <para>
/// The rows come off the same kline endpoint the equities come off, with no adjustment asked for:
/// a currency pair has no dividend and no split to adjust for, and asking for one is how a venue
/// answers with nothing at all. The pair code is a `wh` one, which is why the request goes through
/// the plain path rather than the stock one the rest of the app uses.
/// </para>
/// </summary>
public static class FxHistory
{
    /// <summary>The pair's closes over the span, keyed by day, or as many as the source has.</summary>
    public static async Task<SortedList<DateOnly, double>> ReadAsync(
        TencentKline kline,
        string code,
        DateOnly start,
        DateOnly end,
        CancellationToken cancellation)
    {
        var rates = new SortedList<DateOnly, double>();

        var cursor = end;
        var earliest = end;

        // Six requests is three years of trading days, which is past where this app's own ranges
        // reach; the loop ends on its own whenever a request brings nothing earlier than what is
        // already held, and this is the backstop for a source that stops playing along.
        for (var request = 0; request < 6 && cursor >= start; request++)
        {
            var bars = await kline.RawBarsAsync(
                code, "day", start, cursor, TencentKline.MostBarsPerRequest, cancellation);

            if (bars.Count == 0)
            {
                break;
            }

            foreach (var bar in bars)
            {
                // Trimmed here rather than trusted: this endpoint answers to the *count* it was
                // given and not to the window, so asking for a year can come back with eighteen
                // months and the extra months would otherwise sit at the front of the series as
                // days the caller never asked about.
                if (bar.Close > 0 && bar.Date >= start && bar.Date <= end)
                {
                    rates.TryAdd(bar.Date, bar.Close);
                }
            }

            var first = bars[0].Date;

            if (first >= earliest || first <= start)
            {
                break;
            }

            earliest = first;
            cursor = first.AddDays(-1);
        }

        return rates;
    }

    /// <summary>
    /// The rate in force on a day: the day's own close, or the last one quoted before it.
    ///
    /// Carried forward rather than left missing, because a day nobody recorded a rate for is still
    /// a day somebody held dollars, and a zero there would value the position at nothing.
    /// </summary>
    public static double RateOn(SortedList<DateOnly, double> rates, DateOnly day, double fallback)
    {
        for (var i = rates.Count - 1; i >= 0; i--)
        {
            if (rates.Keys[i] <= day)
            {
                return rates.Values[i];
            }
        }

        return rates.Count > 0 ? rates.Values[0] : fallback;
    }
}
