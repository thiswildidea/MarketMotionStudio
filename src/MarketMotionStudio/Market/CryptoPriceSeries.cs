using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// Daily USD prices for a set of coins over a span, aligned to the days every chosen coin shares.
///
/// Built from CoinMetrics' estimate metric, which every coin in the catalogue carries from the same
/// floor (2019-06-22) — so all coins start on the same day, which a comparison page needs. The
/// price rides along with the value in the same request, so it is the same clock as the cap the
/// other crypto pages draw, and on a market that never closes that is the only honest one to use.
/// </summary>
public static class CryptoPriceSeries
{
    /// <summary>Fewer shared days than this and there is nothing to compare.</summary>
    public const int FewestDays = 30;

    /// <summary>One coin's aligned prices.</summary>
    /// <param name="Asset">The coin.</param>
    /// <param name="Dates">The days every chosen coin has, ascending.</param>
    /// <param name="Prices">This coin's USD price on each of those days, gaps filled.</param>
    public sealed record Series(CryptoAsset Asset, DateOnly[] Dates, double[] Prices);

    /// <summary>
    /// Fetches daily prices for each chosen coin and aligns them to the days they all share.
    ///
    /// A day any coin lacks is dropped from everyone — one missing bar would otherwise shift every
    /// coin's base, and a comparison is only honest against the same axis. Gaps inside the span are
    /// filled by carrying the last known price forward and the first known price back, so a hole in
    /// the source does not divide by zero or tear a line.
    /// </summary>
    public static async Task<IReadOnlyList<Series>> LoadAsync(
        CryptoCaps caps, IReadOnlyList<CryptoAsset> coins, DateOnly from, DateOnly to,
        IProgress<string>? progress, CancellationToken cancellation)
    {
        var assets = coins.Select(c => CryptoCaps.AssetOf(c.Gecko)).ToArray();
        var board = await caps.BatchAsync(assets, from, to, progress, cancellation);

        var kept = new List<(CryptoAsset Asset, List<CryptoCapDay> Days)>();

        foreach (var coin in coins)
        {
            var asset = CryptoCaps.AssetOf(coin.Gecko);

            if (board.TryGetValue(asset, out var days) && days.Count > 0)
            {
                kept.Add((coin, days));
            }
        }

        if (kept.Count == 0)
        {
            // Not one of the chosen coins had a price in the span. On this page that is one cause
            // with one answer: the span is shorter than the source's history, or every coin chosen
            // is one the catalogue does not carry a price for.
            throw new InvalidOperationException(Strings.Get("CryptoPriceNoData"));
        }

        // The days every kept coin has. One missing day is one jump in the comparison.
        var shared = new HashSet<DateOnly>(kept[0].Days.Select(d => d.Date));

        foreach (var (_, days) in kept.Skip(1))
        {
            shared.IntersectWith(days.Select(d => d.Date));
        }

        var dates = shared.OrderBy(d => d).ToArray();

        if (dates.Length < FewestDays)
        {
            throw new InvalidOperationException(Strings.Get("CryptoPriceTooFewDays"));
        }

        var series = new List<Series>(kept.Count);

        foreach (var (coin, days) in kept)
        {
            var byDate = days.ToDictionary(d => d.Date, d => d.PriceUsd);
            var prices = new double[dates.Length];

            // Carry the last known price forward through gaps.
            var last = 0.0;

            for (var i = 0; i < dates.Length; i++)
            {
                if (byDate.TryGetValue(dates[i], out var price) && price > 0)
                {
                    last = price;
                }

                prices[i] = last;
            }

            // No price before the first known day: fill the leading run from the first value, so
            // every coin's base is a real number and not an unfilled zero.
            var first = Array.FindIndex(prices, p => p > 0);

            if (first > 0)
            {
                for (var i = 0; i < first; i++)
                {
                    prices[i] = prices[first];
                }
            }

            series.Add(new Series(coin, dates, prices));
        }

        return series;
    }
}
