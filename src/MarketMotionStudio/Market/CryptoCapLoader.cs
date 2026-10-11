using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One coin's market value, shaped into the board the value-history renderer draws.
///
/// **Why this is a loader and not a walk.** The stock page recovers a value from a
/// row — circulating shares are volume over turnover rate, multiplied by the price —
/// because no endpoint serves a capitalisation. Nothing of that applies here: the coin
/// market's source hands over the value itself, day by day, so the work is picking a
/// range and putting the days on one axis. That is also why this page can start where
/// the coin's own history starts rather than where a quotient stops being usable.
///
/// **Circulating, and worth saying.** CoinMetrics' `CapMrktCurUSD` is the value of the
/// coins in circulation, not of every coin that will ever exist. On bitcoin the two
/// are four percent apart because the last block has not been mined; on a coin with a
/// locked treasury the difference is most of it. The page carries the word.
/// </summary>
public static class CryptoCapLoader
{
    /// <summary>
    /// Fewer days than this and there is no history to draw. Sixty, because this page's
    /// subject is a line over years: a fortnight of rows draws a plausible little curve
    /// and answers a question nobody asked.
    /// </summary>
    private const int FewestDays = 60;

    /// <summary>The value unit: every figure is in 亿 USD, as the stock page's are in 亿元.</summary>
    private const double PerYi = 1e8;

    public static async Task<CapBoard> LoadAsync(
        CryptoCaps caps,
        CryptoAsset asset,
        DateOnly from,
        DateOnly to,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        if (from >= to)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverRangeReversed"));
        }

        var days = await caps.HistoryAsync(
            CryptoCaps.AssetOf(asset.Gecko), from, to, progress, cancellation);

        if (days.Count < FewestDays)
        {
            throw new InvalidOperationException(Strings.Get("CryptoCapTooFewDays"));
        }

        var dates = new DateOnly[days.Count];
        var values = new double[days.Count];
        var prices = new double[days.Count];

        for (var i = 0; i < days.Count; i++)
        {
            dates[i] = days[i].Date;
            values[i] = days[i].CapUsd / PerYi;
            prices[i] = days[i].PriceUsd;
        }

        var track = new CapTrack(asset.Code, asset.Display, values, prices, 0, days.Count - 1);

        // One track, so the frame draws the two panels rather than a set of lines — see
        // the note on `CapHistoryRenderer`, which answers "did the count grow or did the
        // price" by stacking the two.
        return new CapBoard(dates, [track], "MarketCapUnitUsd", false, []);
    }
}
