using System.Globalization;
using System.Net.Http;
using System.Text.Json;

namespace MarketMotionStudio.Market;

/// <summary>
/// One coin's market value and price on one day, both in USD.
///
/// The price rides along with the value rather than being fetched from the candle
/// source, because the two are read on the same axis and a value is only meaningful
/// beside the price it was taken at. Asking a second source for the price would put
/// two clocks on one chart: the candle endpoint's day is stamped in the venue's own
/// time and this one's in UTC, and on a market that never closes the two disagree
/// about which day a move happened on.
/// </summary>
public sealed record CryptoCapDay(DateOnly Date, double CapUsd, double PriceUsd);

/// <summary>
/// One coin as the ranking serves it: what the ranking calls it, the ticker the app
/// knows it by, the ranking's own name, and what it is worth now.
///
/// The ticker is kept because it is the only one of the three the app can look a
/// localised name up by — the ranking's names are English trade names, and a coin the
/// ranking has never carried before still reads as itself on the board.
/// </summary>
public sealed record CryptoListing(string Gecko, string Code, string Name, double CapUsd);

/// <summary>
/// Market values for the crypto market, from CoinMetrics' community tier.
///
/// **Why a third source.** The two the crypto pages already have cannot answer this
/// question at all. Yahoo quotes a coin as a currency pair and carries no supply, so
/// nothing it returns can be multiplied into a value. CoinGecko does serve a value
/// series — it is the `market_caps` array of the very request the fallback already
/// makes — but on the public tier it stops at a year: `days=max`, `days=3650` and the
/// `market_chart/range` form were each answered 401 with "Public API users are limited
/// to querying historical data within the past 365 days" (measured 2026-10-11). A year
/// of value history on a coin whose supply moves a percent a year is a chart of the
/// price with a different scale on it, which is not what the page is for.
///
/// **What CoinMetrics gives instead.** `CapMrktCurUSD` — market value, daily, back to
/// 2010-07-18 on btc and 2015-08-08 on eth — and `CapMrktEstUSD`, an estimated value
/// that every coin in its catalogue carries from 2019-06-22. Both are on the community
/// tier: no key, no account, measured 2026-10-11.
///
/// **The one rule the endpoint enforces, and it is not a limit on how many coins.**
/// A request naming several assets is answered 403 if *any* of them lacks *any* metric
/// named: `assets=btc,eth,sol&metrics=CapMrktCurUSD` is refused with "Requested metric
/// 'CapMrktCurUSD' with frequency '1d' for asset 'sol' is not available with supplied
/// credentials", because sol is carried on the estimate alone. Fifteen assets are
/// answered in one reply when the metric is one they all have (measured: 30 rows, 15
/// assets). So the batch asks for the estimate, which every coin has, and a single coin
/// — where there is nothing to keep consistent with — is asked for the exact value
/// first.
///
/// **Depth is per coin and the board says so.** One request carries 4000 rows, measured
/// at 3936 rows for ten years of one coin with no `next_page_token`, so a decade costs
/// one round trip rather than the six the kline endpoint needs for the same span.
/// </summary>
public sealed class CryptoCaps(HttpClient http)
{
    /// <summary>CoinMetrics' community timeseries endpoint.</summary>
    private const string Endpoint =
        "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics";

    /// <summary>CoinGecko's ranking, which is where the board's field comes from.</summary>
    private const string GeckoEndpoint = "https://api.coingecko.com/api/v3/";

    /// <summary>The exact market value. Older and truer, but not every coin has it.</summary>
    private const string ExactMetric = "CapMrktCurUSD";

    /// <summary>The estimated market value, carried for every coin in the catalogue.</summary>
    private const string EstimateMetric = "CapMrktEstUSD";

    /// <summary>
    /// The day the estimate starts, which is the earliest day a *board* can show.
    ///
    /// Not a floor this app chose: 2019-06-22 is where `CapMrktEstUSD` begins for every
    /// asset in the catalogue, read back from `/v4/catalog/assets` on 2026-10-11. A
    /// board that mixed the exact series (2010 on btc) with the estimate (2019 on sol)
    /// would show some coins appearing out of nothing two thirds of the way through,
    /// which reads as coins that did not exist rather than as a source that does not
    /// carry them.
    /// </summary>
    public static readonly DateOnly EstimateFloor = new(2019, 6, 22);

    /// <summary>Rows one request may carry: more than the ten years the pages offer.</summary>
    private const int PageSize = 4000;

    /// <summary>
    /// How many pages one question may walk.
    ///
    /// One page is 4000 rows and the endpoint answers a board **one asset at a time** —
    /// measured 2026-10-11: fifteen assets over two years came back as 4000 rows holding
    /// six of them, with a `next_page_token` pointing at the day the sixth was cut off.
    /// Not following it is not a shorter board, it is a board missing nine of its coins
    /// while every number on it looks right. Twelve pages is thirty years of one coin or
    /// five years of fifteen, past the longest span either page offers.
    /// </summary>
    private const int MaxPages = 12;

    /// <summary>How long the probe waits before deciding the source is not there.</summary>
    private static readonly TimeSpan ProbeTimeout = TimeSpan.FromSeconds(20);

    /// <summary>
    /// How long one request may take before it is given up as "this source is not
    /// answering for these coins".
    ///
    /// Shorter than the client's own 30 seconds on purpose: `AskAsync` answers *null* for
    /// a request that comes to nothing, and the caller's answer to that is another
    /// question — dropping a coin, or asking for it alone. Letting the client be the one
    /// to give up turns the same fact into an exception, and an exception on one of
    /// fifteen coins would take the whole board with it.
    /// </summary>
    private static readonly TimeSpan AskTimeout = TimeSpan.FromSeconds(20);

    /// <summary>
    /// CoinGecko's id for a coin, to CoinMetrics' asset for the same coin.
    ///
    /// The two catalogues spell them differently and neither is derivable — `avalanche-2`
    /// is `avax`, `ripple` is `xrp`, and CoinGecko's ids carry a suffix where CoinMetrics
    /// carries none. A coin not listed here is asked for under its own id, which mostly
    /// misses; a miss is a coin the board cannot carry rather than a wrong coin, because
    /// the endpoint refuses the whole request instead of answering for the ones it knows.
    /// </summary>
    private static readonly Dictionary<string, string> KnownAssets =
        new(StringComparer.OrdinalIgnoreCase)
        {
            ["bitcoin"] = "btc",
            ["ethereum"] = "eth",
            ["binancecoin"] = "bnb",
            ["solana"] = "sol",
            ["ripple"] = "xrp",
            ["dogecoin"] = "doge",
            ["cardano"] = "ada",
            ["tron"] = "trx",
            ["litecoin"] = "ltc",
            ["chainlink"] = "link",
            ["polkadot"] = "dot",
            ["avalanche-2"] = "avax",
            ["tether"] = "usdt",
            ["usd-coin"] = "usdc",
            ["monero"] = "xmr",
            ["zcash"] = "zec",
            ["bitcoin-cash"] = "bch",
            ["stellar"] = "xlm",
            ["uniswap"] = "uni",
            ["sui"] = "sui",
            ["dai"] = "dai",
            ["wrapped-bitcoin"] = "wbtc",
            ["leo-token"] = "leo",
            ["hyperliquid"] = "hype",
            ["ethena-usde"] = "usde",
        };

    /// <summary>The CoinMetrics name for a coin the ranking calls <paramref name="gecko"/>.</summary>
    public static string AssetOf(string gecko) =>
        KnownAssets.TryGetValue(gecko, out var asset) ? asset : gecko.ToLowerInvariant();

    /// <summary>
    /// Whether this machine can reach CoinMetrics at all. One coin, a few days: the
    /// cheapest question that is still the question the pages ask.
    /// </summary>
    public async Task<bool> ReachableAsync(CancellationToken cancellation)
    {
        try
        {
            using var leash = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
            leash.CancelAfter(ProbeTimeout);

            var from = DateOnly.FromDateTime(DateTimeOffset.UtcNow.AddDays(-7).UtcDateTime);

            var to = DateOnly.FromDateTime(DateTimeOffset.UtcNow.UtcDateTime);

            using var response = await http.GetAsync(
                Query([AssetOf("bitcoin")], EstimateMetric, from, to), leash.Token);

            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Every coin's market value day by day, on the estimate, in one request.
    ///
    /// The estimate rather than the exact value for the reason in this type's note: a
    /// board is a comparison, and a comparison where one line starts eight years after
    /// another is not comparing the same stretch. Coins the estimate does not carry are
    /// dropped from the answer rather than failing the fetch — a ranking is served fresh
    /// each time and nothing about it promises that every coin on it is one this source
    /// has heard of.
    /// </summary>
    public async Task<Dictionary<string, List<CryptoCapDay>>> BatchAsync(
        IReadOnlyList<string> assets,
        DateOnly from,
        DateOnly to,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        var board = new Dictionary<string, List<CryptoCapDay>>(StringComparer.OrdinalIgnoreCase);

        if (assets.Count == 0)
        {
            return board;
        }

        var at = from > EstimateFloor ? from : EstimateFloor;

        progress?.Report(string.Format(
            CultureInfo.InvariantCulture, "CoinMetrics · {0} coins", assets.Count));

        var batched = await AskAsync(assets, EstimateMetric, at, to, progress, cancellation);

        if (batched is not null)
        {
            foreach (var (asset, days) in batched)
            {
                board[asset] = days;
            }

            return board;
        }

        // Refused as a batch, so one of them is not carried — and the usual one is a coin
        // the ranking knows and this catalogue does not. Those are the coins `KnownAssets`
        // has no entry for, so the next question puts them aside: one unmapped id would
        // otherwise cost the whole board.
        var mapped = assets.Where(Known).ToArray();
        var others = assets.Where(asset => !Known(asset)).ToArray();

        if (others.Length > 0)
        {
            progress?.Report(string.Format(
                CultureInfo.InvariantCulture, "CoinMetrics · {0} coins", mapped.Length));

            batched = await AskAsync(mapped, EstimateMetric, at, to, progress, cancellation);

            if (batched is not null)
            {
                foreach (var (asset, days) in batched)
                {
                    board[asset] = days;
                }
            }
        }

        // The ones put aside are then asked one at a time, and that is not a courtesy: an
        // id this app cannot translate is *usually* a coin the other catalogue has never
        // heard of, but not always — `usds` and `usd1` are both carried under exactly the
        // names the ranking gives them — and a stablecoin that is carried should not leave
        // a board that is meant to show size for the sake of a name nobody translated.
        //
        // When the batch above was refused too, there is nothing to add these to, so every
        // coin is asked alone: that is the slow path, and it is the one that keeps a board
        // of four coins rather than reporting a fetch that found nothing.
        foreach (var asset in board.Count > 0 ? others : mapped.Concat(others))
        {
            cancellation.ThrowIfCancellationRequested();

            progress?.Report($"CoinMetrics · {asset}");

            var single = await AskAsync([asset], EstimateMetric, at, to, progress, cancellation);

            if (single is null || !single.TryGetValue(asset, out var days))
            {
                continue;
            }

            board[asset] = days;
        }

        return board;
    }

    /// <summary>
    /// One coin's value day by day, as far back as this source carries it.
    ///
    /// The exact value first, because it reaches years further back than the estimate —
    /// 2010 on btc where the estimate starts in 2019. The estimate is asked for anyway
    /// and laid down underneath it, because some coins have both and the exact series
    /// stops: bnb's runs to 2019-04-22 and dot's to 2022-06-03, and a coin whose value
    /// stops being served is not a coin that stopped having one. Where the two disagree
    /// on a day, the exact figure wins.
    /// </summary>
    public async Task<IReadOnlyList<CryptoCapDay>> HistoryAsync(
        string asset,
        DateOnly from,
        DateOnly to,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        progress?.Report($"CoinMetrics · {asset}");

        var estimate = await AskAsync([asset], EstimateMetric, from, to, progress, cancellation);
        var exact = await AskAsync([asset], ExactMetric, from, to, progress, cancellation);

        var days = new SortedDictionary<DateOnly, CryptoCapDay>();

        if (estimate is not null && estimate.TryGetValue(asset, out var estimated))
        {
            foreach (var day in estimated)
            {
                days[day.Date] = day;
            }
        }

        if (exact is not null && exact.TryGetValue(asset, out var truer))
        {
            foreach (var day in truer)
            {
                // Only where the figure is there: the exact series carries a day with a
                // value missing more often than the estimate does, and overwriting a real
                // number with a blank would punch holes in the line to no purpose.
                if (day.CapUsd > 0)
                {
                    days[day.Date] = day;
                }
            }
        }

        return [.. days.Values];
    }

    /// <summary>
    /// The market's largest coins, in order, as the ranking serves them now.
    ///
    /// CoinGecko's ranking rather than a list written into the app, for the same reason
    /// the mainland's market-cap board asks for the ranking: a board drawn from a list
    /// somebody wrote down is a statement about the day they wrote it. Stablecoins are
    /// kept — they are the third and eighth largest things on this market and a board
    /// that hid them would be ranking something other than size.
    /// </summary>
    public async Task<IReadOnlyList<CryptoListing>> RankingAsync(
        int count,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        progress?.Report("CoinGecko · ranking");

        var uri = $"{GeckoEndpoint}coins/markets?vs_currency=usd&order=market_cap_desc" +
                  $"&per_page={count}&page=1&sparkline=false";

        using var response = await http.GetAsync(uri, cancellation);

        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        var rows = new List<CryptoListing>();

        foreach (var row in json.RootElement.EnumerateArray())
        {
            var gecko = Text(row, "id");
            var code = Text(row, "symbol");

            if (gecko.Length == 0 || code.Length == 0)
            {
                continue;
            }

            rows.Add(new CryptoListing(
                gecko,
                code.ToUpperInvariant(),
                Text(row, "name").Length > 0 ? Text(row, "name") : code.ToUpperInvariant(),
                Number(row, "market_cap")));
        }

        return rows;
    }

    /// <summary>The request one batch is made with. A token walks to the next page.</summary>
    private static string Query(IEnumerable<string> assets, string metric, DateOnly from, DateOnly to,
                                string? token = null) =>
        $"{Endpoint}?assets={string.Join(",", assets)}" +
        $"&metrics={metric},PriceUSD&frequency=1d" +
        $"&start_time={Iso(from)}&end_time={Iso(to)}&page_size={PageSize}" +
        (token is null ? "" : $"&next_page_token={Uri.EscapeDataString(token)}");

    /// <summary>Whether this catalogue translates an id into <paramref name="asset"/>.</summary>
    private static bool Known(string asset) => KnownAssets.ContainsValue(asset);

    private static string Iso(DateOnly day) => day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    /// <summary>
    /// One question, walked across as many pages as it takes, or null when it was refused.
    ///
    /// **It follows `next_page_token`.** One page is 4000 rows and the endpoint fills it
    /// one asset at a time, so a fifteen-coin board over two years is three pages; reading
    /// the first one alone is a board with six coins on it, and nothing about those six
    /// says nine are missing.
    ///
    /// Null rather than an exception because a refusal here is a fact about a coin, not
    /// a fault in the page: the endpoint refuses the whole batch when one asset lacks the
    /// metric, and the caller's answer to that is to drop the coin or to ask again with
    /// the other metric — either of which is a decision, not an error to report upward.
    /// </summary>
    private async Task<Dictionary<string, List<CryptoCapDay>>?> AskAsync(
        IReadOnlyList<string> assets,
        string metric,
        DateOnly from,
        DateOnly to,
        IProgress<string>? progress,
        CancellationToken cancellation)
    {
        var board = new Dictionary<string, List<CryptoCapDay>>(StringComparer.OrdinalIgnoreCase);
        string? token = null;

        for (var page = 0; page < MaxPages; page++)
        {
            string body;

            try
            {
                using var leash = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
                leash.CancelAfter(AskTimeout);

                using var response = await http.GetAsync(
                    Query(assets, metric, from, to, token), leash.Token);

                body = await response.Content.ReadAsStringAsync(leash.Token);

                if (!response.IsSuccessStatusCode)
                {
                    // A refusal on the first page is "not these coins"; on a later page it
                    // is the same thing arriving late, and what is already here is kept —
                    // a board that stops a few coins short says so on the status line,
                    // whereas one that throws away everything it had says nothing at all.
                    return board.Count > 0 ? board : null;
                }
            }
            catch (OperationCanceledException) when (!cancellation.IsCancellationRequested)
            {
                return board.Count > 0 ? board : null;
            }

            using var json = JsonDocument.Parse(body);

            if (!json.RootElement.TryGetProperty("data", out var data)
                || data.ValueKind != JsonValueKind.Array)
            {
                return board.Count > 0 ? board : null;
            }

            foreach (var row in data.EnumerateArray())
            {
                var asset = Text(row, "asset");
                var stamp = Text(row, "time");

                if (asset.Length == 0 || stamp.Length < 10
                    || !DateOnly.TryParse(stamp[..10], CultureInfo.InvariantCulture, out var day))
                {
                    continue;
                }

                if (day < from || day > to)
                {
                    continue;
                }

                var cap = Number(row, metric);

                if (cap <= 0)
                {
                    continue;
                }

                if (!board.TryGetValue(asset, out var days))
                {
                    days = [];
                    board[asset] = days;
                }

                days.Add(new CryptoCapDay(day, cap, Number(row, "PriceUSD")));
            }

            token = json.RootElement.TryGetProperty("next_page_token", out var next)
                    && next.ValueKind == JsonValueKind.String
                ? next.GetString()
                : null;

            if (token is null)
            {
                return board;
            }

            progress?.Report(string.Format(
                CultureInfo.InvariantCulture, "CoinMetrics · page {0}", page + 2));
        }

        return board;
    }

    private static string Text(JsonElement row, string name) =>
        row.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString() ?? ""
            : "";

    /// <summary>
    /// A number out of a row, whether it arrives as a number or as a string.
    ///
    /// CoinMetrics quotes its figures as strings — `"CapMrktCurUSD":"1079394515904.969690420738316808"` —
    /// because they are decimals wider than a double and it would rather not round them
    /// for the caller. Measured 2026-10-11: reading only <see cref="JsonValueKind.Number"/>
    /// parses every row of a 200 response into "no value", which the page then reports as
    /// a span the source holds nothing for. The ranking endpoint's own figures are plain
    /// numbers, so both shapes have to be read.
    /// </summary>
    private static double Number(JsonElement row, string name)
    {
        if (!row.TryGetProperty(name, out var value))
        {
            return 0;
        }

        if (value.ValueKind == JsonValueKind.Number)
        {
            return value.GetDouble();
        }

        return value.ValueKind == JsonValueKind.String
               && double.TryParse(value.GetString(), NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed)
            ? parsed
            : 0;
    }
}
