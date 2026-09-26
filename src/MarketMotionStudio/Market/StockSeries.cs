using System.Globalization;
using System.Net.Http;
using System.Text.Json;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The shape both of this page's modes are drawn from: one measure of volume and one of turnover
/// rate, sharing a label axis, in a display unit already chosen.
///
/// Normalising the two modes into one record is what lets one renderer draw both. The differences
/// that matter — bars against an area curve, per-day rate against a cumulative one — are flags
/// rather than types, because they change how the same numbers are *drawn*, not what they are.
/// </summary>
/// <param name="Code">The full code, `sh600000` style.</param>
/// <param name="Name">The instrument's name, for the title and the file name.</param>
/// <param name="Labels">Axis labels: `MM-DD` per day, or `HH:mm` per minute.</param>
/// <param name="Volumes">Volume in <paramref name="VolumeUnit"/> per label.</param>
/// <param name="Rates">Turnover rate in per cent — per day, or cumulative within the day.</param>
/// <param name="VolumeUnit">`手` or `万手`, chosen by the peak's size.</param>
/// <param name="VolumeDecimals">How a volume figure reads in that unit.</param>
/// <param name="RateIsCumulative">Whether the rate is a running total — drawn as an area curve.</param>
/// <param name="HasRate">Whether a rate exists at all; some listings carry none.</param>
/// <param name="Day">The chosen trading day, `yyyyMMdd`, in the intraday mode.</param>
/// <param name="AvailableDays">The days the intraday endpoint still holds.</param>
/// <param name="FileNameSpan">The range as a file-name fragment, `2026-06-26_2026-09-24` or `20260925`.</param>
public sealed record StockPanelSeries(
    string Code,
    string Name,
    IReadOnlyList<string> Labels,
    IReadOnlyList<double> Volumes,
    IReadOnlyList<double> Rates,
    string VolumeUnit,
    int VolumeDecimals,
    bool RateIsCumulative,
    bool HasRate,
    string? Day = null,
    IReadOnlyList<string>? AvailableDays = null,
    string FileNameSpan = "")
{
    public int Count => Labels.Count;

    public double VolumePeak { get; } = Volumes.Count > 0 ? Volumes.Max() : 0;

    public double VolumeLow { get; } = Volumes.Count > 0 ? Volumes.Min() : 0;

    public double VolumeAverage { get; } = Volumes.Count > 0 ? Volumes.Average() : 0;

    public int VolumePeakIndex { get; } = IndexOf(Volumes, Volumes.Count > 0 ? Volumes.Max() : 0);

    public int VolumeLowIndex { get; } = IndexOf(Volumes, Volumes.Count > 0 ? Volumes.Min() : 0);

    public double RatePeak { get; } = Rates.Count > 0 ? Rates.Max() : 0;

    public double RateLow { get; } = Rates.Count > 0 ? Rates.Min() : 0;

    public double RateAverage { get; } = Rates.Count > 0 ? Rates.Average() : 0;

    public double FinalRate { get; } = Rates.Count > 0 ? Rates[^1] : 0;

    private static int IndexOf(IReadOnlyList<double> values, double value)
    {
        for (var i = 0; i < values.Count; i++)
        {
            if (values[i] == value)
            {
                return i;
            }
        }

        return -1;
    }

    /// <summary>Grouped thousands with the unit's own decimals — the axis' and the read-out's format.</summary>
    public static string Round(double value, int decimals) =>
        value.ToString("N" + decimals.ToString(CultureInfo.InvariantCulture), CultureInfo.InvariantCulture);
}

/// <summary>
/// Loads the two modes' series from the Tencent endpoints, with every unit trap the browser tool
/// documented handled on the way in.
/// </summary>
public static class StockSeries
{
    private const string MinuteEndpoint = "https://web.ifzq.gtimg.cn/appstock/app/day/query";

    /// <summary>
    /// The daily mode: one bar per trading day, volume in the display unit, turnover rate as the
    /// endpoint reports it.
    /// </summary>
    public static async Task<StockPanelSeries> LoadDailyAsync(
        TencentKline kline, StockDirectory directory, MarketProfile market, string code,
        DateOnly start, DateOnly end, IProgress<string> progress, CancellationToken cancellation)
    {
        progress.Report(Strings.Format("StockFetching", code.ToUpperInvariant()));

        var bars = await kline.StockBarsAsync(code, start, end, cancellation);

        if (bars.Count < 3)
        {
            throw new InvalidOperationException(Strings.Get("TurnoverTooFewDays"));
        }

        var volumes = NormaliseVolume(bars, market, out var perShare);

        // A listing may report no turnover rate at all — an index masquerading as a stock in the
        // search list is the usual case. The chart still draws; the lower panel states its absence.
        var rates = bars.Select(b => b.TurnoverRate).ToArray();
        var hasRate = rates.Any(r => r > 0);

        var (tenThousand, decimals) = VolumeUnit(volumes);

        return new StockPanelSeries(
            code,
            kline.LastName(code),
            [.. bars.Select(b => b.Date.ToString("MM-dd", CultureInfo.InvariantCulture))],
            [.. volumes.Select(v => v / (tenThousand ? 10_000 : 1))],
            rates,
            tenThousand ? Strings.Get("StockUnitTenThousand") : Strings.Get("StockUnitHands"),
            decimals,
            RateIsCumulative: false,
            HasRate: hasRate,
            FileNameSpan: $"{bars[0].Date:yyyy-MM-dd}_{bars[^1].Date:yyyy-MM-dd}");
    }

    /// <summary>
    /// The intraday mode: per-minute volume as the difference of the cumulative series, and a
    /// cumulative turnover rate derived from the snapshot's free-float value.
    /// </summary>
    /// <remarks>
    /// Three endpoint quirks are handled here and nowhere else. The series runs past the close to
    /// 15:30, so it is cut at the market's own closing time and then at the last minute the
    /// cumulative total actually moved — a video that ends on a minute of nothing is a video with a
    /// dead frame. And the turnover rate is not in the response at all: the share count comes from
    /// the snapshot (free-float value ÷ price) and the rate is computed from it, degrading to an
    /// absent panel when the snapshot cannot be had.
    /// </remarks>
    public static async Task<StockPanelSeries> LoadIntradayAsync(
        HttpClient http, StockDirectory directory, MarketProfile market, string code, string? wantedDay,
        IProgress<string> progress, CancellationToken cancellation)
    {
        progress.Report(Strings.Format("StockFetchingIntraday", code.ToUpperInvariant()));

        var uri = $"{MinuteEndpoint}?code={Uri.EscapeDataString(code)}";

        using var response = await http.GetAsync(uri, cancellation);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        var root = json.RootElement;

        if (!root.TryGetProperty("code", out var status) || status.GetInt32() != 0)
        {
            throw new InvalidOperationException(Strings.Get("StockIntradayUnavailable"));
        }

        if (!root.TryGetProperty("data", out var data) || !data.TryGetProperty(code, out var node) ||
            !node.TryGetProperty("data", out var days) || days.GetArrayLength() == 0)
        {
            throw new InvalidOperationException(Strings.Get("StockIntradayUnavailable"));
        }

        var available = new List<(string Id, JsonElement Node, int Points)>();

        foreach (var day in days.EnumerateArray())
        {
            if (!day.TryGetProperty("date", out var date) || date.GetString() is not { Length: 8 } id)
            {
                continue;
            }

            var points = day.TryGetProperty("data", out var rows) ? rows.GetArrayLength() : 0;
            available.Add((id, day, points));
        }

        if (available.Count == 0)
        {
            throw new InvalidOperationException(Strings.Get("StockIntradayUnavailable"));
        }

        // The default is the latest *complete* day — one in progress holds only the minutes traded
        // so far, dozens where a settled day holds 260 — unless a specific day was asked for.
        var chosen = available.FirstOrDefault(d => d.Id == wantedDay);

        if (chosen.Node.ValueKind == JsonValueKind.Undefined)
        {
            chosen = available.FirstOrDefault(d => d.Points > 200);
        }

        if (chosen.Node.ValueKind == JsonValueKind.Undefined)
        {
            chosen = available[^1];
        }

        var dayId = chosen.Id;
        var minuteRows = chosen.Node.GetProperty("data").EnumerateArray()
            .Select(r => r.GetString())
            .Where(s => s is not null)
            .Select(s => s!.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries))
            .Where(f => f.Length >= 4)
            .ToArray();

        // Cut at the venue's own close — the endpoint pads settled days to 15:30.
        var closeAt = code.StartsWith("hk") ? "1600" : "1500";
        var cut = code.StartsWith("us")
            ? minuteRows
            : minuteRows.Where(r => r[0].Length >= 4 && string.CompareOrdinal(r[0][..4], closeAt) <= 0).ToArray();

        if (cut.Length < 10)
        {
            throw new InvalidOperationException(Strings.Get("StockIntradayTooFew"));
        }

        // Then cut at the last minute the cumulative volume moved.
        var last = cut.Length - 1;
        while (last > 0 && Parse(cut[last][2]) == Parse(cut[last - 1][2]))
        {
            last--;
        }

        var valid = cut[..(last + 1)];

        double Parse(string s) =>
            double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? v : 0;

        // Per-share detection, same as the daily mode: the minute endpoint's volume field follows
        // the listing's convention, not the endpoint's.
        var ratios = valid
            .Select(r => (vol: Parse(r[2]), price: Parse(r[1]), amount: Parse(r[3])))
            .Where(t => t.vol > 0 && t.price > 0 && t.amount > 0)
            .Select(t => (t.vol * 100 * t.price) / t.amount)
            .OrderBy(r => r)
            .ToArray();

        var perShare = market.Volume is VolumeBasis.Shares
            || (ratios.Length > 0 && ratios[ratios.Length / 2] > 10);

        var cumulative = valid.Select(r => Parse(r[2]) / (perShare ? 100 : 1)).ToArray();
        var perMinute = new double[cumulative.Length];

        for (var i = 0; i < cumulative.Length; i++)
        {
            perMinute[i] = i == 0 ? cumulative[i] : Math.Max(0, cumulative[i] - cumulative[i - 1]);
        }

        // The turnover rate needs the share count, which only the snapshot has. A failure here is
        // degraded-from, not fatal: the volume panel is the one that was asked for.
        var name = code.ToUpperInvariant();
        var floatShares = 0.0;

        try
        {
            var snapshot = await directory.SnapshotAsync(code, cancellation);
            name = snapshot.Name.Length > 0 ? snapshot.Name : name;

            if (snapshot.FloatCapYi > 0 && snapshot.Price > 0)
            {
                floatShares = snapshot.FloatCapYi * 1e8 / snapshot.Price;
            }
        }
        catch (Exception)
        {
            // The intraday panel is still a complete video without the rate.
        }

        var rates = floatShares > 0
            ? cumulative.Select(v => v * 100 / floatShares * 100).ToArray()
            : new double[cumulative.Length];

        var (tenThousand, decimals) = VolumeUnit(perMinute);

        return new StockPanelSeries(
            code,
            name,
            [.. valid.Select(r => r[0].Length >= 4 ? r[0][..2] + ":" + r[0][2..4] : r[0])],
            [.. perMinute.Select(v => v / (tenThousand ? 10_000 : 1))],
            rates,
            tenThousand ? Strings.Get("StockUnitTenThousand") : Strings.Get("StockUnitHands"),
            decimals,
            RateIsCumulative: true,
            HasRate: floatShares > 0,
            Day: dayId,
            AvailableDays: [.. available.Select(d => d.Id)],
            FileNameSpan: dayId);
    }

    /// <summary>
    /// Puts a volume series into lots. The endpoint's unit follows the listing — shares on the
    /// STAR market, lots elsewhere — and is told apart by "volume × price ≈ amount" rather than by
    /// a board prefix, which stays right when a prefix guess would not.
    /// </summary>
    private static double[] NormaliseVolume(List<TencentKline.StockBar> bars, MarketProfile market, out bool perShare)
    {
        var ratios = bars
            .Where(b => b.RawVolume > 0 && b.Close > 0 && b.AmountWan > 0)
            .Select(b => (b.RawVolume * 100 * b.Close / 10_000) / b.AmountWan)
            .OrderBy(r => r)
            .ToArray();

        // The ratio above asks "does volume × price come to the amount?" and it can only
        // be asked where the amount is quoted in 万元, as it is in Shanghai, Shenzhen and
        // Hong Kong. In New York it is plain dollars, the ratio collapses to a hundredth
        // of what it should be, and the answer has to come from the market instead.
        // Copied out of the parameter before the lambda below: an out parameter cannot be
        // captured, and this is the one place in the app that wants both the answer and the
        // series it came from in one expression.
        var byShare = perShare = market.Volume is VolumeBasis.Shares
            || (ratios.Length > 0 && ratios[ratios.Length / 2] > 10);

        return bars.Select(b => byShare ? b.RawVolume / 100 : b.RawVolume).ToArray();
    }

    /// <summary>
    /// The display unit: once the peak passes 100,000 lots the axis switches to 万手, because six
    /// grouped digits beside a gridline is where reading stops being instant.
    /// </summary>
    private static (bool IsTenThousand, int Decimals) VolumeUnit(double[] lots)
    {
        var peak = lots.Length > 0 ? lots.Max() : 0;
        var tenThousand = peak >= 100_000;

        return (tenThousand, tenThousand ? 1 : 0);
    }
}
