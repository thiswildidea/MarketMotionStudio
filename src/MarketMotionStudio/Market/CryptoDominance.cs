using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// Market-cap dominance: each chosen coin's share of the chosen set's total cap, day by day.
///
/// CoinMetrics gives every coin's cap on the estimate metric from the same floor, so the shares are
/// honest across coins and over time. The share is of the coins on the frame, not of the whole
/// market — a figure the source serves per coin but not as one total — so the columns sum to one
/// hundred across the chosen coins, and the page says so. BTC, ETH and the rest are seen competing
/// for the same hundred points, which is what dominance means.
///
/// The board is the sector race on <see cref="RaceMetric.Amount"/>, the unit being the per-cent share
/// — so the bars are read as a slice of one hundred rather than as a currency.
/// </summary>
public static class CryptoDominance
{
    /// <summary>Fewer shared days than this and there is no story to tell.</summary>
    public const int FewestDays = 30;

    /// <summary>
    /// Builds the dominance board. Each day, every coin's cap is divided by the chosen set's total
    /// cap that day, giving each coin's share in per cent. The rows therefore sum to one hundred.
    /// </summary>
    public static async Task<SectorRaceSeries> LoadAsync(
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
            // Not one of the chosen coins had a cap in the span, which is the same two causes as the
            // price pages: the span is shorter than the source's history, or every coin chosen is one
            // the catalogue does not carry a cap for.
            throw new InvalidOperationException(Strings.Get("CryptoPriceNoData"));
        }

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

        // Each coin's cap on each shared day, the last known value carried forward through gaps.
        var capsByCoin = new List<double[]>(kept.Count);

        foreach (var (_, days) in kept)
        {
            var byDate = days.ToDictionary(d => d.Date, d => d.CapUsd);
            var row = new double[dates.Length];
            var last = 0.0;

            for (var i = 0; i < dates.Length; i++)
            {
                if (byDate.TryGetValue(dates[i], out var cap) && cap > 0)
                {
                    last = cap;
                }

                row[i] = last;
            }

            capsByCoin.Add(row);
        }

        var entries = kept.Select(k => new RaceEntry(k.Asset.Code, k.Asset.Display)).ToList();
        var amounts = new List<double[]>(kept.Count);

        for (var c = 0; c < capsByCoin.Count; c++)
        {
            var row = new double[dates.Length];

            for (var i = 0; i < dates.Length; i++)
            {
                var total = 0.0;

                foreach (var cap in capsByCoin)
                {
                    total += cap[i];
                }

                row[i] = total > 0 ? (capsByCoin[c][i] / total) * 100 : 0;
            }

            amounts.Add(row);
        }

        // The board draws Amount; the second slot mirrors so either metric reads the same numbers.
        return new SectorRaceSeries(entries, dates, amounts, amounts);
    }
}
