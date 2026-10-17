using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// Coins' market value, shaped into the board the value-history renderer draws.
///
/// **Why this is a loader and not a walk.** The stock page recovers a value from a
/// row — circulating shares are volume over turnover rate, multiplied by the price —
/// because no endpoint serves a capitalisation. Nothing of that applies here: the coin
/// market's source hands over the value itself, day by day, so the work is picking a
/// range and putting the days on one axis. That is also why this page can start where
/// the coin's own history starts rather than where a quotient stops being usable.
///
/// **Several coins change nothing about how a value is recovered.** There is no arithmetic
/// here to get wrong twice: each coin is one walk against the source, and the walks are
/// then laid on one axis by the same assembler the share pages use
/// (<see cref="CapLoader.Assemble"/>), because the two markets meet at exactly one point
/// — a set of series, each beginning where its own history does, that have to share a
/// date axis.
///
/// **A coin the source carries no value for is not drawn.** CoinMetrics knows bitcoin
/// and it does not know most of what the search box can find, and the catalogue is asked
/// under the CoinGecko id — see <see cref="CryptoCaps.AssetOf"/>, which translates the
/// handful of names the two catalogues spell differently and passes the rest through.
/// A coin that comes back with too little is named on the status line rather than drawn
/// flat along the bottom, which is the same answer the share page gives an index.
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

    /// <summary>
    /// What this board's figures are denominated in, as the stock page's board names its
    /// own. Nothing draws it directly on this page — the panel's unit word is built from
    /// the crypto page's own key — but the board carries a currency like every other, and
    /// a board that named none would be the one place the two pages' shapes disagreed.
    /// </summary>
    private const string UnitKey = "MarketCapUnitUsd";

    /// <summary>
    /// One coin's value day by day, or null when the span holds too few days to draw a
    /// history from.
    ///
    /// Null rather than an exception, and for the reason the share walk gives: "this coin
    /// has no history here" is an answer the caller has words for, and it is not the same
    /// answer as "this coin has none anywhere". A coin the catalogue does not carry comes
    /// back empty here and is named on the status line instead of being drawn — which on
    /// this page is not a rare case, because the search box can add coins from a ranking
    /// this source has never heard of.
    ///
    /// Internal because every caller wants a board: one coin's series still goes on an
    /// axis, even when there is only the one, and two ways to ask for a value history
    /// invite two answers that disagree about what the axis is.
    /// </summary>
    internal static async Task<CapSeries?> SeriesAsync(
        CryptoCaps caps,
        CryptoAsset asset,
        DateOnly from,
        DateOnly to,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        var days = await caps.HistoryAsync(
            CryptoCaps.AssetOf(asset.Gecko), from, to, progress, cancellation);

        if (days.Count < FewestDays)
        {
            return null;
        }

        var values = new CapDay[days.Count];

        for (var i = 0; i < days.Count; i++)
        {
            values[i] = new CapDay(days[i].Date, days[i].CapUsd / PerYi, days[i].PriceUsd);
        }

        return new CapSeries(asset.Code, asset.Display, UnitKey, false, values);
    }

    /// <summary>
    /// One or more coins' value over the same span, or null when not one of them had a
    /// history in it.
    ///
    /// Null rather than an exception, as the share page's board is: "no value in this
    /// range" is a thing both pages have words for. Every coin coming back empty is that
    /// answer; some coming back empty is not, and those are reported in
    /// <see cref="CapBoard.Skipped"/> instead.
    ///
    /// The walks are made one after another rather than together, for the reason the share
    /// page gives: six parallel streams against one endpoint is answered by a throttle,
    /// which takes the slow path anyway after making every other page on the machine slow
    /// with it. A decade of one coin is a single round trip here, so the turns are short.
    /// </summary>
    public static async Task<CapBoard?> LoadAsync(
        CryptoCaps caps,
        IReadOnlyList<CryptoAsset> assets,
        DateOnly from,
        DateOnly to,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        if (from >= to)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverRangeReversed"));
        }

        var walks = new List<CapSeries>(assets.Count);
        var skipped = new List<string>();

        foreach (var asset in assets)
        {
            var series = await SeriesAsync(caps, asset, from, to, progress, cancellation);

            if (series is null)
            {
                skipped.Add(asset.Display);
                continue;
            }

            walks.Add(series);
        }

        return CapLoader.Assemble(walks, skipped);
    }
}
