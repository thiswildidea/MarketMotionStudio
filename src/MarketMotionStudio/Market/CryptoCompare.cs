using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The normalized price race: several coins' prices, each rebased to 100 on the first shared day,
/// raced as cumulative returns.
///
/// The renderer is the sector race on <see cref="RaceMetric.Return"/> — exactly the metric a
/// rebased-to-100 line is. Each coin starts at 0% (i.e. its own 100), and the race is "whose
/// price grew faster from the same starting line", which is the question a normalized comparison
/// exists to answer: bitcoin at $67,000 and dogecoin at $0.12 are placed on one axis honestly
/// because both begin at 100.
/// </summary>
public static class CryptoCompare
{
    /// <summary>
    /// Builds the race from daily prices. The base is the first *shared* day's price, so every coin
    /// starts at exactly 0% — the same starting line the chart calls day one.
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
            var basePrice = s.Prices[0];
            var row = new double[dates.Length];

            for (var i = 0; i < dates.Length; i++)
            {
                row[i] = basePrice > 0 ? (s.Prices[i] / basePrice - 1) * 100 : 0;
            }

            returns.Add(row);
        }

        // The race draws Return; the second slot mirrors so either metric reads the same numbers.
        return new SectorRaceSeries(entries, dates, returns, returns);
    }
}
