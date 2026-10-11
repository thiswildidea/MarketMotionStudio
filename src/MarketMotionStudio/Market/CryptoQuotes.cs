using System.Net.Http;
using System.Text.Json;

namespace MarketMotionStudio.Market;

/// <summary>
/// One coin this app can draw, under both of the sources that carry it.
///
/// The three names are three different things and none of them is a display string.
/// <paramref name="Code"/> is what the app calls the coin by everywhere else — the
/// picker's key, the preference it remembers, the resource key its name is looked up
/// under (<c>INSTBTC</c>). The other two are what each source calls it, and they are
/// not derived from one another: Yahoo wants <c>BTC-USD</c>, CoinGecko wants
/// <c>bitcoin</c>, and guessing either from the ticker is how a request ends up
/// asking about a different coin or about none.
///
/// <paramref name="Name"/> is the source's own English, kept as the fallback for a
/// language that has no entry for the code. It is never shown when the entry exists:
/// see <see cref="InstrumentNames"/>.
/// </summary>
public sealed record CryptoAsset(string Code, string Name, string Yahoo, string Gecko)
{
    /// <summary>
    /// The coins offered, in the order the picker shows them: by size of following
    /// rather than by market capitalisation on some day, which would make the list a
    /// statement about that day.
    ///
    /// Twelve, and a list rather than a search, for the same reason the built-in
    /// stock rosters are lists: the two sources spell these coins differently and a
    /// name typed into a box reaches neither. Everything on it has daily history on
    /// Yahoo back past 2017, measured 2026-10-11 — the youngest, SOL, starts
    /// 2020-04-10, which is what bounds the longest span the pages offer.
    /// </summary>
    public static readonly CryptoAsset[] All =
    [
        new("BTC", "Bitcoin", "BTC-USD", "bitcoin"),
        new("ETH", "Ethereum", "ETH-USD", "ethereum"),
        new("BNB", "BNB", "BNB-USD", "binancecoin"),
        new("SOL", "Solana", "SOL-USD", "solana"),
        new("XRP", "XRP", "XRP-USD", "ripple"),
        new("DOGE", "Dogecoin", "DOGE-USD", "dogecoin"),
        new("ADA", "Cardano", "ADA-USD", "cardano"),
        new("TRX", "TRON", "TRX-USD", "tron"),
        new("LTC", "Litecoin", "LTC-USD", "litecoin"),
        new("LINK", "Chainlink", "LINK-USD", "chainlink"),
        new("DOT", "Polkadot", "DOT-USD", "polkadot"),
        new("AVAX", "Avalanche", "AVAX-USD", "avalanche-2"),
    ];

    /// <summary>The name to show: the current language's entry, or the source's own English.</summary>
    public string Display => InstrumentNames.Display(Code, Name);

    /// <summary>The asset a code names, or null when the code is not one of ours.</summary>
    public static CryptoAsset? Of(string code) =>
        Array.Find(All, asset => string.Equals(asset.Code, code, StringComparison.OrdinalIgnoreCase));

    /// <summary>Whether a code is one of ours, which is what keeps it out of a stock request.</summary>
    public static bool IsCrypto(string code) => Of(code) is not null;
}

/// <summary>
/// Which of the two sources answered.
///
/// Two, because neither is dependable on its own and they fail for opposite reasons.
/// Yahoo carries ten years of real candles anywhere it can be reached at all, but it
/// is an undocumented endpoint and answers a machine it does not like with a 429 or
/// with nothing. CoinGecko is a documented, keyed-by-nothing public API with a stated
/// limit, and that limit is the price: **365 days, and only the close** (measured
/// 2026-10-11 — <c>days=max</c> is refused outright for a caller without a key, and
/// the OHLC endpoint coarsens to one candle every four days past a month).
/// </summary>
public enum CryptoSource
{
    /// <summary>Yahoo's chart endpoint: ten years of daily open/high/low/close and volume.</summary>
    Yahoo = 0,

    /// <summary>CoinGecko's market chart: a year of daily closes, no open, high or low.</summary>
    CoinGecko = 1,
}

/// <summary>
/// The route to a cryptocurrency's daily history, over whichever of the two sources
/// this machine can reach.
///
/// **The first question is not "what was the price" but "is either source there".**
/// Both of them are outside the mainland's reach — measured 2026-10-11, Yahoo answers
/// from abroad and CoinGecko answers from nowhere else — so a machine inside it has no
/// crypto pages to show, and saying so is the whole feature: three navigation items
/// that offer data they cannot fetch are three items that fail. <see cref="ReachableAsync"/>
/// answers that once per process, with a short leash (see <see cref="ProbeTimeout"/>),
/// and the window asks it before it puts the pages in the menu.
///
/// A coin trades every day of the year, and that changes two things the stock pages
/// were written around. There are no holidays to step over, so a span is calendar days
/// and the axis has no gaps a viewer has to be told about. And there is no adjustment:
/// no dividend, no split, so the close *is* the return and nothing here asks a source
/// for an adjusted series — which is also why the two sources are interchangeable in a
/// way a stock's adjusted and unadjusted series never are.
///
/// What is not interchangeable is the shape of the bar. Yahoo gives four prices a
/// candle can be drawn from; CoinGecko gives one, and a candle drawn from one price is
/// a candle whose body and wicks are a lie. <see cref="GivesCandles"/> says which
/// arrived, and the candle page offers only the styles that shape can carry.
/// </summary>
public sealed class CryptoQuotes(HttpClient http)
{
    /// <summary>Yahoo's chart endpoint. The ticker goes in the path, the range in the query.</summary>
    private const string YahooEndpoint = "https://query1.finance.yahoo.com/v8/finance/chart/";

    /// <summary>CoinGecko's public API root.</summary>
    private const string GeckoEndpoint = "https://api.coingecko.com/api/v3/";

    /// <summary>
    /// How long the longest span Yahoo is asked for is, in days.
    ///
    /// Ten years, and it is a request limit rather than the source's: Yahoo answers a
    /// wider window with the coin's whole history (BTC's begins 2014-09-17), but a
    /// decade of daily candles is three thousand six hundred bars, and a frame nine
    /// hundred pixels wide cannot draw them — the same reasoning that caps the stock
    /// candle page's daily spans at ten years.
    /// </summary>
    public const int YahooMostDays = 3650;

    /// <summary>
    /// How far back CoinGecko answers, in days.
    ///
    /// Measured 2026-10-11: <c>days=max</c> is refused with error 10012 for a caller
    /// without a key, and 365 is accepted. A longer span is not fetched in two pieces
    /// either — two requests are two chances to be throttled, and a chart that starts
    /// where the source starts is an honest chart. The page clips its own range to this
    /// when this is the source in force.
    /// </summary>
    public const int GeckoMostDays = 365;

    /// <summary>
    /// How long a probe waits before it decides the source is not there.
    ///
    /// Twelve seconds, and the number is measured rather than picked. The first request
    /// out of a cold start pays for DNS, the handshake and TLS before any of the coin's
    /// own data moves, and was timed at seven and a half seconds on a machine that
    /// reaches Yahoo perfectly well — whose second request to the same host took just
    /// over one. At six seconds that machine was judged unreachable and quietly handed
    /// the fallback, which carries a year where the primary carries ten.
    ///
    /// The patience is spent mostly on machines that can be served. One that cannot
    /// reach the source gets silence, but silence that arrives quickly: the connection
    /// is refused or dropped rather than left hanging, so it does not cost the full
    /// twelve.
    ///
    /// Multiplied by <see cref="ProbeAttempts"/>, and that is not the same kind of
    /// waiting: the probe runs while the window is already up and being used, and the
    /// fourth market is simply not in the list until it answers. A launch never waits
    /// for it.
    /// </summary>
    private static readonly TimeSpan ProbeTimeout = TimeSpan.FromSeconds(12);

    /// <summary>
    /// How many times each source is asked before it is called absent.
    ///
    /// Two, and the second one is the whole point: **the first request a process makes is
    /// the one that pays for the connection** — DNS, the proxy handshake, the TLS
    /// negotiation — and on a machine that reaches Yahoo perfectly well, that first
    /// request is the one most likely to run past a six-second leash. Measured
    /// 2026-10-11, three launches in a row over the same VPN: two answered in under a
    /// second, one lost it and took all three pages out of the menu for the rest of the
    /// run. A menu that loses three pages once in three launches is worse than a menu
    /// that takes one extra second to decide, and the second ask costs nothing at all
    /// when the first one answered.
    ///
    /// It is a retry of the *question*, not of the fetch: nothing is drawn from it, and
    /// a source that answers the second time was never away.
    /// </summary>
    private const int ProbeAttempts = 2;

    /// <summary>
    /// How long two CoinGecko requests are kept apart.
    ///
    /// Its free tier answers a burst by throttling the caller — measured 2026-10-11,
    /// the seventeenth id asked for inside a minute came back 429 — and a throttled
    /// fetch is a fetch that fails halfway through a comparison of six coins. So the
    /// requests are spaced, which is why six coins over this source takes a minute and
    /// why Yahoo is asked first wherever Yahoo answers.
    /// </summary>
    private static readonly TimeSpan GeckoSpacing = TimeSpan.FromSeconds(8);

    private static readonly SemaphoreSlim GeckoGate = new(1, 1);

    private static DateTimeOffset _geckoLast = DateTimeOffset.MinValue;

    private static readonly SemaphoreSlim ProbeGate = new(1, 1);

    private CryptoSource? _source;

    private bool _probed;

    /// <summary>
    /// Which source is in force, or null when neither answered. Only meaningful once
    /// <see cref="ReachableAsync"/> has been asked; see there.
    /// </summary>
    public CryptoSource? Source => _source;

    /// <summary>
    /// Whether a source has answered in this process — asked after
    /// <see cref="ReachableAsync"/>, and false before it, which is what keeps a page
    /// that was hidden from the menu from being reached by a tag alone.
    /// </summary>
    public bool Answered => _source is not null;

    /// <summary>
    /// Whether the bars carry four prices rather than one.
    ///
    /// Read after a fetch, and it decides what the candle page may offer: a style that
    /// draws a body and two wicks out of a single close draws a shape the coin never
    /// made. False is not a failure, it is CoinGecko's answer, and the page says so.
    /// </summary>
    public bool GivesCandles => _source is not CryptoSource.CoinGecko;

    /// <summary>
    /// Whether either source answered, caching the answer for the process.
    ///
    /// One probe per launch is the point: the answer does not change while the app is
    /// open, and asking again per page would put a six-second silence in front of every
    /// fetch. <paramref name="force"/> exists for the one case where the answer can
    /// change underneath us — a machine that was inside the mainland when it started and
    /// is not any more, which the settings page can be asked about by hand.
    /// </summary>
    public async Task<bool> ReachableAsync(bool force = false, CancellationToken cancellation = default)
    {
        await ProbeGate.WaitAsync(cancellation);

        try
        {
            if (_probed && !force)
            {
                return _source is not null;
            }

            _source = await ProbeAsync(cancellation);
            _probed = true;

            return _source is not null;
        }
        finally
        {
            ProbeGate.Release();
        }
    }

    /// <summary>
    /// Asks Yahoo first, then CoinGecko, each inside the probe's own leash.
    ///
    /// Yahoo first because it is the source that can answer the pages properly: ten
    /// years and four prices, where the fallback has a year and one. The fallback is
    /// only asked when Yahoo did not answer, so a machine that reaches both is never
    /// quietly given the poorer series.
    /// </summary>
    private async Task<CryptoSource?> ProbeAsync(CancellationToken cancellation)
    {
        for (var attempt = 0; attempt < ProbeAttempts; attempt++)
        {
            if (await YahooRespondsAsync(cancellation))
            {
                return CryptoSource.Yahoo;
            }
        }

        for (var attempt = 0; attempt < ProbeAttempts; attempt++)
        {
            if (await GeckoRespondsAsync(cancellation))
            {
                return CryptoSource.CoinGecko;
            }
        }

        return null;
    }

    /// <summary>
    /// One small request to Yahoo, answered yes or no rather than with data.
    ///
    /// Five days of one coin: the cheapest question the endpoint can be asked that is
    /// still the real one. A cheaper endpoint on the same host would answer about the
    /// host and not about the query the pages actually send, which is the difference
    /// between "the network is up" and "the pages will work".
    /// </summary>
    private async Task<bool> YahooRespondsAsync(CancellationToken cancellation)
    {
        try
        {
            using var leash = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
            leash.CancelAfter(ProbeTimeout);

            var uri = $"{YahooEndpoint}BTC-USD?range=5d&interval=1d";
            using var response = await http.GetAsync(uri, leash.Token);

            return response.IsSuccessStatusCode;
        }
        catch (OperationCanceledException) when (!cancellation.IsCancellationRequested)
        {
            // The probe's own leash ran out, which is the answer "not there" — the
            // silence described on `ProbeTimeout`. A cancellation the caller asked for
            // is not ours to reinterpret and falls through.
            return false;
        }
        catch (HttpRequestException)
        {
            return false;
        }
    }

    /// <summary>CoinGecko's own liveness endpoint, read the same way.</summary>
    private async Task<bool> GeckoRespondsAsync(CancellationToken cancellation)
    {
        try
        {
            using var leash = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
            leash.CancelAfter(ProbeTimeout);

            using var response = await http.GetAsync($"{GeckoEndpoint}ping", leash.Token);

            return response.IsSuccessStatusCode;
        }
        catch (OperationCanceledException) when (!cancellation.IsCancellationRequested)
        {
            return false;
        }
        catch (HttpRequestException)
        {
            return false;
        }
    }

    /// <summary>
    /// One coin's daily bars over a range, from whichever source answered.
    ///
    /// An empty list is an answer and not a failure: a coin listed after the range
    /// began, or a range the source hold nothing for, has no bars in it, and the
    /// callers say so in words rather than throwing. See <see cref="CryptoCandleLoader"/>
    /// for where an empty list becomes a sentence on the page.
    /// </summary>
    public async Task<IReadOnlyList<TencentKline.CandleBar>> BarsAsync(
        CryptoAsset asset, DateOnly from, DateOnly to,
        IProgress<string>? progress, CancellationToken cancellation)
    {
        if (to < from)
        {
            throw new ArgumentException("The start date must fall on or before the end date.", nameof(from));
        }

        var source = await SourceAsync(cancellation);

        return source == CryptoSource.Yahoo
            ? await YahooBarsAsync(asset, from, to, progress, cancellation)
            : await GeckoBarsAsync(asset, from, to, progress, cancellation);
    }

    /// <summary>
    /// The closes over a range, keyed by day — the shape the plan and holding pages
    /// walk, and the same shape <see cref="HistoryWalk"/> produces for stocks, so the
    /// two pages that consume it need no branch of their own.
    /// </summary>
    public async Task<SortedList<DateOnly, double>> ClosesAsync(
        string code, string display, DateOnly start, DateOnly end,
        IProgress<string>? progress, CancellationToken cancellation)
    {
        var asset = CryptoAsset.Of(code)
            ?? throw new ArgumentException($"Not a coin this app offers: {code}", nameof(code));

        var bars = await BarsAsync(asset, start, end, progress, cancellation);

        var closes = new SortedList<DateOnly, double>(bars.Count);

        foreach (var bar in bars)
        {
            // A non-positive close is not a price. The sources have not served one, but
            // a bar that bought nothing at it would divide by zero downstream, and the
            // cost of the check is a comparison.
            if (bar.Close > 0)
            {
                closes.TryAdd(bar.Date, bar.Close);
            }
        }

        return closes;
    }

    /// <summary>The source in force, probing first when nothing has asked yet.</summary>
    private async Task<CryptoSource> SourceAsync(CancellationToken cancellation)
    {
        if (_source is { } known)
        {
            return known;
        }

        if (!await ReachableAsync(false, cancellation))
        {
            throw new InvalidOperationException("Neither cryptocurrency source answered.");
        }

        return _source!.Value;
    }

    /// <summary>
    /// Yahoo's daily candles for one coin.
    ///
    /// The reply is a parallel set of arrays — one of timestamps, one each for the
    /// open, high, low, close and volume — rather than an array of bars, so the bar is
    /// assembled here by index. A row any of the four prices is missing on is dropped
    /// rather than filled: Yahoo leaves a hole where it has no figure, and a zero in a
    /// price series is a fall of a hundred per cent that never happened.
    ///
    /// The timestamps are UTC midnights and the coin's own clock is UTC, so the day a
    /// bar belongs to is read straight off it with no offset to apply and no session
    /// boundary to respect — see the note on the class.
    /// </summary>
    private async Task<IReadOnlyList<TencentKline.CandleBar>> YahooBarsAsync(
        CryptoAsset asset, DateOnly from, DateOnly to,
        IProgress<string>? progress, CancellationToken cancellation)
    {
        progress?.Report($"Yahoo · {asset.Code}");

        var uri = $"{YahooEndpoint}{Uri.EscapeDataString(asset.Yahoo)}" +
                  $"?period1={Stamp(from)}&period2={Stamp(to)}&interval=1d";

        using var response = await http.GetAsync(uri, cancellation);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
        using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

        var chart = json.RootElement.GetProperty("chart");

        // A delisted or misspelled ticker is a 200 with an error inside it, not a
        // status code — and `result` is null when it is, so the two are read together
        // or the null is dereferenced two lines later.
        if (chart.TryGetProperty("error", out var error) && error.ValueKind == JsonValueKind.Object)
        {
            var said = error.TryGetProperty("description", out var text) ? text.GetString() : null;
            throw new InvalidOperationException($"{asset.Code}: {said ?? "the chart source reported an error"}");
        }

        if (!chart.TryGetProperty("result", out var results) || results.ValueKind != JsonValueKind.Array
            || results.GetArrayLength() == 0 || results[0].ValueKind != JsonValueKind.Object)
        {
            throw new InvalidOperationException($"{asset.Code}: the chart source carried no series.");
        }

        var result = results[0];

        if (!result.TryGetProperty("timestamp", out var stamps) || stamps.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidOperationException($"{asset.Code}: the chart source carried no days.");
        }

        var quote = result.GetProperty("indicators").GetProperty("quote")[0];
        var opens = Values(quote, "open");
        var highs = Values(quote, "high");
        var lows = Values(quote, "low");
        var closes = Values(quote, "close");
        var volumes = Values(quote, "volume");

        var bars = new List<TencentKline.CandleBar>(stamps.GetArrayLength());

        for (var i = 0; i < stamps.GetArrayLength(); i++)
        {
            var day = DateOnly.FromDateTime(DateTimeOffset.FromUnixTimeSeconds(stamps[i].GetInt64()).UtcDateTime);

            if (day < from || day > to)
            {
                continue;
            }

            var open = opens[i];
            var high = highs[i];
            var low = lows[i];
            var close = closes[i];

            if (open is null || high is null || low is null || close is null)
            {
                continue;
            }

            // The volume's unit is not stated by the source and is not the same figure
            // as a stock's lot count, so it is carried unconverted: the only thing a
            // frame makes of it is how tall today's bar is against the tallest one in
            // the range, and a unit cancels in that.
            bars.Add(new TencentKline.CandleBar(day, open.Value, high.Value, low.Value, close.Value, volumes[i] ?? 0));
        }

        return bars;
    }

    /// <summary>
    /// CoinGecko's daily closes for one coin, as bars whose four prices are the one price.
    ///
    /// The fallback's shape, and the reason <see cref="GivesCandles"/> exists: it
    /// carries a day and a price and nothing else, so a bar built from it has no body
    /// and no wicks to draw — only a point a line can pass through. Filling the other
    /// three with the same number is what keeps <see cref="TencentKline.CandleBar"/>
    /// the one bar type in the app, and the candle page is told which shape it holds
    /// rather than left to discover it.
    ///
    /// The span is clipped to <see cref="GeckoMostDays"/> here rather than by the
    /// caller, because the source refuses a longer one outright and a refusal is not
    /// something a page can talk its way out of.
    /// </summary>
    private async Task<IReadOnlyList<TencentKline.CandleBar>> GeckoBarsAsync(
        CryptoAsset asset, DateOnly from, DateOnly to,
        IProgress<string>? progress, CancellationToken cancellation)
    {
        var start = to.AddDays(-(GeckoMostDays - 1));

        if (start < from)
        {
            start = from;
        }

        var days = Math.Max(1, to.DayNumber - start.DayNumber + 1);

        progress?.Report($"CoinGecko · {asset.Code}");

        await GeckoGate.WaitAsync(cancellation);

        try
        {
            var wait = GeckoSpacing - (DateTimeOffset.UtcNow - _geckoLast);

            if (wait > TimeSpan.Zero)
            {
                await Task.Delay(wait, cancellation);
            }

            var uri = $"{GeckoEndpoint}coins/{Uri.EscapeDataString(asset.Gecko)}" +
                      $"/market_chart?vs_currency=usd&days={days}&interval=daily";

            using var response = await http.GetAsync(uri, cancellation);

            // A throttled caller is told so in the status, and there is no waiting it
            // out inside one fetch: the page's own timeout is minutes and the spacing
            // above is seconds. Named rather than swallowed, because "no bars" and
            // "asked too often" are different things to tell a person.
            response.EnsureSuccessStatusCode();

            await using var stream = await response.Content.ReadAsStreamAsync(cancellation);
            using var json = await JsonDocument.ParseAsync(stream, cancellationToken: cancellation);

            if (!json.RootElement.TryGetProperty("prices", out var prices)
                || prices.ValueKind != JsonValueKind.Array)
            {
                throw new InvalidOperationException($"{asset.Code}: the market chart carried no prices.");
            }

            var bars = new List<TencentKline.CandleBar>(prices.GetArrayLength());

            foreach (var row in prices.EnumerateArray())
            {
                if (row.ValueKind != JsonValueKind.Array || row.GetArrayLength() < 2)
                {
                    continue;
                }

                var day = DateOnly.FromDateTime(
                    DateTimeOffset.FromUnixTimeMilliseconds(row[0].GetInt64()).UtcDateTime);

                if (day < start || day > to || row[1].ValueKind != JsonValueKind.Number)
                {
                    continue;
                }

                var close = row[1].GetDouble();

                bars.Add(new TencentKline.CandleBar(day, close, close, close, close, 0));
            }

            return bars;
        }
        finally
        {
            _geckoLast = DateTimeOffset.UtcNow;
            GeckoGate.Release();
        }
    }

    /// <summary>
    /// One of the parallel price arrays, read as nullable doubles.
    ///
    /// Nullable because the source leaves holes and a hole is not a zero: see the
    /// note on <see cref="YahooBarsAsync"/>. An array the reply left out entirely reads
    /// as all holes rather than as a missing property to throw on, because a reply with
    /// no volume still has days and prices worth drawing.
    /// </summary>
    private static double?[] Values(JsonElement quote, string name)
    {
        if (!quote.TryGetProperty(name, out var values) || values.ValueKind != JsonValueKind.Array)
        {
            return [];
        }

        var read = new double?[values.GetArrayLength()];
        var at = 0;

        foreach (var value in values.EnumerateArray())
        {
            read[at++] = value.ValueKind == JsonValueKind.Number ? value.GetDouble() : null;
        }

        return read;
    }

    /// <summary>A day as the Unix seconds Yahoo's range parameters are written in: its UTC midnight.</summary>
    private static long Stamp(DateOnly day) =>
        new DateTimeOffset(day.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero).ToUnixTimeSeconds();
}
