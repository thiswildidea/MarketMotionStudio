using System.Globalization;
using System.Net.Http;
using System.Text.Json;

namespace MarketMotionStudio.Market;

/// <summary>One minute of an index's day: the minute since midnight, and the level it printed.</summary>
/// <param name="Minute">Minutes since midnight — 570 is 09:30.</param>
/// <param name="Price">The index level at that minute.</param>
public sealed record IndexMinute(int Minute, double Price);

/// <summary>
/// One index's session, minute by minute, normalised against yesterday's close.
///
/// <para>
/// **Levels are not comparable and percentages are.** 恒生指数 printed 23,094 the day this was
/// written and 上证指数 3,681, so a frame that plotted the two levels on one axis would draw
/// the Hang Seng as a flat line at the top and 上证 as a flat line at the bottom, neither of
/// them saying anything. Every number this record hands out to the renderer is a percentage
/// against <see cref="PrevClose"/>, which is the one quantity the two markets do share.
/// </para>
///
/// <para>
/// The minute rows come from the source's own intraday endpoint, which answers with one price
/// per minute — no open, high or low. That is why the board's lower half is a line and not a run
/// of candles: candles would have to be invented from those prices, and an invented high is a
/// number the reader has no way to check.
/// </para>
/// </summary>
/// <param name="Code">The source's own spelling — <c>sh000001</c>, <c>hkHSI</c>.</param>
/// <param name="Name">The name the source quotes it under.</param>
/// <param name="IsHongKong">Which of the two calendars the session keeps.</param>
/// <param name="PrevClose">Yesterday's close, the denominator of every percentage here.</param>
/// <param name="Minutes">The session's prints, in time order, bounded by the venue's close.</param>
public sealed record IndexIntradaySeries(
    string Code,
    string Name,
    bool IsHongKong,
    double PrevClose,
    IReadOnlyList<IndexMinute> Minutes)
{
    public int OpenMinute => IntradayPnl.OpenMinute;

    /// <summary>When this venue stops: 15:00 on the mainland, 16:00 in Hong Kong.</summary>
    public int CloseMinute => IsHongKong ? IntradayPnl.HongKongClose : IntradayPnl.MainlandClose;

    public IndexMinute Last => Minutes.Count > 0 ? Minutes[^1] : new(OpenMinute, PrevClose);

    /// <summary>How far the index is from yesterday's close, in per cent, at one print.</summary>
    public double ChangeAt(IndexMinute sample) =>
        PrevClose > 0 ? (sample.Price - PrevClose) / PrevClose * 100 : 0;

    public double LastChange => ChangeAt(Last);

    public double LastPrice => Last.Price;
}

/// <summary>
/// Reads the intraday minute endpoint for a handful of indexes.
///
/// One request per index, in parallel, because the source takes one code at a time and a board
/// asking for six would otherwise take six round trips end to end. The endpoint is the same one
/// the app already trusts for a day's shape — it answers for both mainland and Hong Kong codes,
/// which is the property this page is built on.
/// </summary>
public static class IndexIntraday
{
    private const string Endpoint = "https://web.ifzq.gtimg.cn/appstock/app/minute/query?code=";

    /// <summary>
    /// Every selected index's day. Codes the source does not answer for are dropped rather than
    /// thrown: a board of two indexes with one of them missing still draws the other, and the
    /// page reports how many came back.
    /// </summary>
    public static async Task<List<IndexIntradaySeries>> LoadAsync(
        HttpClient http, IReadOnlyList<RaceEntry> entries, CancellationToken cancellation)
    {
        var loads = entries.Select(entry => LoadOneAsync(http, entry, cancellation));
        var loaded = await Task.WhenAll(loads);

        return [.. loaded.Where(s => s is not null).Select(s => s!)];
    }

    public static bool IsHongKong(string code) =>
        code.StartsWith("hk", StringComparison.OrdinalIgnoreCase);

    private static async Task<IndexIntradaySeries?> LoadOneAsync(
        HttpClient http, RaceEntry entry, CancellationToken cancellation)
    {
        var text = await http.GetStringAsync(
            Endpoint + Uri.EscapeDataString(entry.Code), cancellation);

        return Parse(text, entry);
    }

    /// <summary>
    /// The payload, turned into a session. Separated from the request so the shape can be read
    /// back from a saved body, and so a payload the source changes cannot take the page down:
    /// anything unexpected answers null and the board draws the indexes that did parse.
    /// </summary>
    public static IndexIntradaySeries? Parse(string json, RaceEntry entry)
    {
        JsonDocument document;

        try
        {
            document = JsonDocument.Parse(json);
        }
        catch (JsonException)
        {
            return null;
        }

        using (document)
        {
            if (!document.RootElement.TryGetProperty("data", out var data)
                || data.ValueKind != JsonValueKind.Object)
            {
                return null;
            }

            if (!TryGet(data, entry.Code, out var node))
            {
                return null;
            }

            if (!node.TryGetProperty("data", out var inner)
                || !inner.TryGetProperty("data", out var rows)
                || rows.ValueKind != JsonValueKind.Array)
            {
                return null;
            }

            var (sourceName, prevClose) = Quote(node, entry.Code);

            if (prevClose <= 0)
            {
                return null;
            }

            var isHongKong = IsHongKong(entry.Code);
            var close = isHongKong ? IntradayPnl.HongKongClose : IntradayPnl.MainlandClose;

            // Keyed by the minute so a duplicated print (the closing auction repeats 15:00) is
            // the last one rather than two points stacked on one x.
            var byMinute = new SortedDictionary<int, double>();

            foreach (var row in rows.EnumerateArray())
            {
                if (row.ValueKind != JsonValueKind.String)
                {
                    continue;
                }

                var parts = (row.GetString() ?? string.Empty)
                    .Split(' ', StringSplitOptions.RemoveEmptyEntries);

                if (parts.Length < 2 || parts[0].Length != 4)
                {
                    continue;
                }

                if (!int.TryParse(parts[0][..2], NumberStyles.None, CultureInfo.InvariantCulture, out var hour)
                    || !int.TryParse(parts[0][2..], NumberStyles.None, CultureInfo.InvariantCulture, out var minute))
                {
                    continue;
                }

                if (!double.TryParse(parts[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var price)
                    || price <= 0)
                {
                    continue;
                }

                var clock = (hour * 60) + minute;

                // The bounds are the venue's own: Hong Kong keeps printing into its closing
                // auction past 16:00, and those prints belong to a session this page says ends
                // at four o'clock.
                if (clock < IntradayPnl.OpenMinute || clock > close)
                {
                    continue;
                }

                byMinute[clock] = price;
            }

            if (byMinute.Count < 2)
            {
                return null;
            }

            var minutes = byMinute.Select(pair => new IndexMinute(pair.Key, pair.Value)).ToArray();

            return new IndexIntradaySeries(
                entry.Code,
                sourceName.Length > 0 ? sourceName : entry.Name,
                isHongKong,
                prevClose,
                minutes);
        }
    }

    /// <summary>The name and yesterday's close, out of the quote block that rides the payload.</summary>
    private static (string Name, double PrevClose) Quote(JsonElement node, string code)
    {
        if (!node.TryGetProperty("qt", out var quotes)
            || quotes.ValueKind != JsonValueKind.Object
            || !TryGet(node.GetProperty("qt"), code, out var fields)
            || fields.ValueKind != JsonValueKind.Array)
        {
            return (string.Empty, 0);
        }

        var name = fields.GetArrayLength() > 1 ? fields[1].GetString() ?? string.Empty : string.Empty;

        // The source's own field order: 3 is the last price, 4 yesterday's close, 5 today's open.
        var prevClose = fields.GetArrayLength() > 4
            && double.TryParse(fields[4].GetString(), NumberStyles.Float, CultureInfo.InvariantCulture, out var value)
            ? value
            : 0;

        return (name, prevClose);
    }

    private static bool TryGet(JsonElement parent, string name, out JsonElement value)
    {
        if (parent.TryGetProperty(name, out value))
        {
            return true;
        }

        foreach (var property in parent.EnumerateObject())
        {
            if (string.Equals(property.Name, name, StringComparison.OrdinalIgnoreCase))
            {
                value = property.Value;

                return true;
            }
        }

        value = default;

        return false;
    }
}
