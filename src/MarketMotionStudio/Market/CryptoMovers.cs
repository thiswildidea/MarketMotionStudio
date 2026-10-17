using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The 24-hour movers board: each coin's change versus the previous day, raced day by day.
///
/// CoinGecko's live 24h ranking is the natural source, but it is behind the same wall as the rest
/// of that endpoint on machines that cannot reach it — so the move is computed from CoinMetrics'
/// daily <c>PriceUSD</c> as the close-over-previous-close change. A daily close is a fair proxy for
/// a 24-hour move on a market that never sleeps; it is not an intraday tick, and the page says so.
///
/// The board is the sector race on <see cref="RaceMetric.Return"/> with the bars coloured by sign
/// (red up, green down) and ranked by magnitude, because a movers board is about the biggest moves
/// either way, not about a signed ladder.
/// </summary>
public static class CryptoMovers
{
    /// <summary>
    /// Builds the board from daily prices. Day zero has no prior close, so it reads zero and the
    /// page hides it rather than drawing a row of nothing.
    /// </summary>
    public static async Task<SectorRaceSeries> LoadAsync(
        CryptoCaps caps, IReadOnlyList<CryptoAsset> coins, DateOnly from, DateOnly to,
        IProgress<string>? progress, CancellationToken cancellation)
    {
        var series = await CryptoPriceSeries.LoadAsync(caps, coins, from, to, progress, cancellation);

        var dates = series[0].Dates;
        var entries = series.Select(s => new RaceEntry(s.Asset.Code, s.Asset.Display)).ToList();
        var returns = new List<double[]>(series.Count);

        foreach (var s in series)
        {
            var row = new double[dates.Length];

            for (var i = 0; i < dates.Length; i++)
            {
                row[i] = i > 0 && s.Prices[i - 1] > 0
                    ? (s.Prices[i] / s.Prices[i - 1] - 1) * 100
                    : 0;
            }

            returns.Add(row);
        }

        return new SectorRaceSeries(entries, dates, returns, returns);
    }
}
