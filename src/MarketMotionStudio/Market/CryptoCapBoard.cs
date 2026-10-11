using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The crypto market's value board: who the largest coins are, and how that order moved.
///
/// **Two sources, asked one thing each.** The field comes from CoinGecko's ranking —
/// today's largest coins by market value, asked for rather than written down, so a coin
/// that grew into the top fifteen this year is on the board without anybody editing a
/// list. The history comes from CoinMetrics, one request for the whole board: on the
/// estimate metric, which is the only one every coin in that catalogue carries, and
/// which starts on the same day for all of them.
///
/// **Stablecoins stay on it.** Measured 2026-10-11: the top thirty carry six of them
/// (usdt, usdc, usds, usde, dai, usd1), and tether is the third largest thing on this
/// market. A board that hid them would be ranking something other than size. What they
/// do to the picture is honest and worth knowing: their line is flat, because a dollar
/// is worth a dollar, so the board shows at a glance which of the largest things on
/// this market actually move.
///
/// **Why the ranking is a request and the history is not.** A board needs both a field
/// and a series per member, and the two have very different prices. The ranking is one
/// small call. The history is one call for all fifteen because CoinMetrics takes a
/// comma-separated asset list — measured at fifteen assets in a single reply. So the
/// board costs two requests, not fifteen.
/// </summary>
public static class CryptoCapBoard
{
    /// <summary>
    /// How many coins the board shows. Fifteen, the same number the stock board draws,
    /// arrived at there for the same reason: fifteen rows is what a frame holds before
    /// the labels start overlapping.
    /// </summary>
    public const int Board = 15;

    /// <summary>
    /// The fewest coins a board can be made of. Below this it is not a ranking, and the
    /// likely cause is a source that answered for none of them rather than a market with
    /// four coins in it.
    /// </summary>
    private const int FewestCoins = 5;

    /// <summary>Every value is in 亿 USD, as the stock board's are in 亿元.</summary>
    private const double PerYi = 1e8;

    /// <summary>
    /// Today's board, priced day by day over the span.
    ///
    /// The span is clipped to <see cref="CryptoCaps.EstimateFloor"/> rather than refused,
    /// because the estimate is what every coin on the board has: asking for 2016 would
    /// get a board on which two coins have eight years of history and thirteen have
    /// none, which reads as coins that appeared out of nowhere.
    /// </summary>
    public static async Task<SectorRaceSeries> LoadAsync(
        CryptoCaps caps,
        DateOnly from,
        DateOnly to,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        var listing = await caps.RankingAsync(Board, progress, cancellation);

        if (listing.Count < FewestCoins)
        {
            throw new InvalidOperationException(Strings.Get("CryptoMarketCapTooFew"));
        }

        var assets = listing.Select(l => CryptoCaps.AssetOf(l.Gecko)).ToArray();

        var start = from > CryptoCaps.EstimateFloor ? from : CryptoCaps.EstimateFloor;

        if (start >= to)
        {
            throw new InvalidOperationException(Strings.Get("CryptoMarketCapTooShort"));
        }

        var days = await caps.BatchAsync(assets, start, to, progress, cancellation);

        // Kept in the ranking's own order, which is the order the board's colours are
        // assigned in — a coin's colour here is a fact about this board rather than
        // about the coin, exactly as it is on the stock board. A coin the value source
        // does not carry is dropped rather than drawn flat at zero: a flat line at the
        // bottom of a value race reads as a coin that went to nothing.
        var kept = new List<(CryptoListing Listing, List<CryptoCapDay> Days)>();

        foreach (var item in listing)
        {
            if (days.TryGetValue(CryptoCaps.AssetOf(item.Gecko), out var series) && series.Count > 0)
            {
                kept.Add((item, series));
            }
        }

        if (kept.Count < FewestCoins)
        {
            throw new InvalidOperationException(Strings.Get("CryptoMarketCapTooFew"));
        }

        var dates = kept
            .SelectMany(k => k.Days.Select(d => d.Date))
            .Distinct()
            .OrderBy(d => d)
            .ToArray();

        if (dates.Length < 5)
        {
            throw new InvalidOperationException(Strings.Get("CryptoMarketCapTooShort"));
        }

        var at = new Dictionary<DateOnly, int>(dates.Length);

        for (var i = 0; i < dates.Length; i++)
        {
            at[dates[i]] = i;
        }

        var rows = new List<double[]>(kept.Count);
        var entries = new List<RaceEntry>(kept.Count);
        var starts = new List<int>(kept.Count);

        foreach (var (item, series) in kept)
        {
            var row = new double[dates.Length];
            var first = dates.Length;

            foreach (var day in series)
            {
                var index = at[day.Date];

                if (index < first)
                {
                    first = index;
                }

                row[index] = day.CapUsd / PerYi;
            }

            // A day the coin has no figure for carries the last one forward, as on the
            // stock board: a hole in a daily series is a reporting gap, not a coin that
            // stopped being worth anything. Before its first figure it is zero, and
            // `Starts` tells the renderer not to draw that stretch.
            for (var i = 1; i < row.Length; i++)
            {
                if (row[i] <= 0)
                {
                    row[i] = row[i - 1];
                }
            }

            rows.Add(row);
            starts.Add(first);
            entries.Add(new RaceEntry(item.Code, InstrumentNames.Display(item.Code, item.Name)));
        }

        // The race model carries two measures and this page has one, as on the stock
        // board: the value lives in both slots so any path through the renderer reads
        // the same numbers.
        return new SectorRaceSeries(entries, dates, rows, rows, starts);
    }
}
