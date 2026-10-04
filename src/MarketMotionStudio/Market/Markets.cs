using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// Which market the app is pointed at.
///
/// The default is <see cref="AShare"/>: every page was built against it, it is the
/// one the app is named for, and it is the only one whose whole-market turnover the
/// source can quote.
/// </summary>
public enum MarketId
{
    AShare = 0,
    HongKong = 1,
    UnitedStates = 2,
}

/// <summary>
/// How the volume field of a bar is to be read into lots (手).
/// </summary>
public enum VolumeBasis
{
    /// <summary>
    /// Lots for most listings, shares on the STAR board. Told apart from the amount
    /// beside the volume rather than from the code — see <c>StockSeries</c>.
    /// </summary>
    Detect,

    /// <summary>
    /// Always shares. The US amount is quoted in dollars rather than in 万元, so the
    /// ratio the detection reads cannot be formed and the answer has to be given.
    /// </summary>
    Shares,
}

/// <summary>A named list of entrants a race or a matrix can be run on.</summary>
/// <param name="LabelKey">The resource key naming the list in the interface.</param>
/// <param name="Entries">The entrants, in roster order.</param>
public sealed record RosterList(string LabelKey, RaceEntry[] Entries);

/// <summary>
/// Everything that differs between the markets this app can be pointed at.
///
/// Held as data rather than as branches through the pages because the differences
/// are few, fixed and factual: which codes belong, what the amount field is
/// measured in, and which lists the source can actually quote. A page asks the
/// profile instead of knowing any of it, so a market that cannot supply a figure
/// is one the profile simply does not carry.
/// </summary>
/// <param name="Id">Which market this is.</param>
/// <param name="NameKey">Resource key for the market's name, as the interface lists it.</param>
/// <param name="AmountToYi">What the amount field is divided by to reach 亿 of the venue's currency.</param>
/// <param name="Volume">How the volume field is read.</param>
/// <param name="WholeMarketTurnover">
/// Whether the source quotes a turnover figure covering the whole market. Only the
/// A-share exchanges have codes for it; see <see cref="WholeMarket"/>.
/// </param>
/// <param name="Intraday">
/// Whether the minute endpoint serves this market. It serves Shanghai, Shenzhen and
/// Hong Kong, and answers a US code with an empty body.
/// </param>
/// <param name="Rosters">The sector lists on offer. At least one, or the race page has nothing to run.</param>
/// <param name="BroadIndices">One-tap instruments for the matrix and the calendar.</param>
/// <param name="DcaInstruments">One-tap instruments for the plan page: the things a plan is plausibly started on.</param>
/// <param name="PositionInstruments">
/// One-tap instruments for the position page: the names a long-term holding is
/// plausibly a story about — household stocks people actually say they have held,
/// plus an index or tracker for asking what the market itself did.
/// </param>
/// <param name="CandleInstruments">
/// One-tap instruments for the candle page: an index, a stock and a fund from this
/// market, because "what did it do" is asked about all three and the source quotes
/// all three out of the same endpoint.
/// </param>
/// <param name="CurrencyKey">
/// Resource key for the venue's currency unit, which the plan's and the position's
/// subtitles name — an amount invested is an amount *of something*, and the three
/// venues do not agree on what.
/// </param>
public sealed record MarketProfile(
    MarketId Id,
    string NameKey,
    double AmountToYi,
    VolumeBasis Volume,
    bool WholeMarketTurnover,
    bool Intraday,
    RosterList[] Rosters,
    RaceEntry[] BroadIndices,
    RaceEntry[] DcaInstruments,
    RaceEntry[] PositionInstruments,
    RaceEntry[] CandleInstruments,
    string CurrencyKey)
{
    public string Name => Strings.Get(NameKey);

    /// <summary>
    /// Whether the amount field is quoted in 万元, as it is everywhere but New York.
    ///
    /// Named rather than left for callers to compare against a number, because what a
    /// caller wants to know is which unit a label has to name, not what a divisor is.
    /// </summary>
    public bool AmountInWan => AmountToYi is 10_000;

    /// <summary>
    /// Whether the minute-*candle* endpoint serves this market, which is not the same
    /// question <see cref="Intraday"/> answers.
    ///
    /// That one is about `day/query`, which carries a price, a cumulative volume and a
    /// cumulative amount and does serve Hong Kong. This one is about `kline/mkline`,
    /// which carries open, high, low and close and serves Shanghai and Shenzhen alone:
    /// measured 2026-10-04, `hk00700` and `hkHSI` come back with `"data": []`, exactly as
    /// a US code does. So the K-line page can offer minute candles on the A-share market
    /// and nowhere else, and a Hong Kong daily chart cannot be drilled into.
    /// </summary>
    public bool MinuteCandles => Id is MarketId.AShare;

    /// <summary>
    /// Whether a code belongs to this market. Tested on the venue prefix, which is
    /// the only part of a code that says where it is quoted: a six-digit number
    /// carries its venue nowhere a reader can see it.
    /// </summary>
    public bool Accepts(string code) => code.Length >= 3 && Id switch
    {
        MarketId.AShare => code.StartsWith("sh") || code.StartsWith("sz") || code.StartsWith("bj"),
        MarketId.HongKong => code.StartsWith("hk"),
        _ => code.StartsWith("us"),
    };
}

/// <summary>
/// The three markets, as the source can actually quote them.
///
/// Every code below was fetched from the quote endpoint and read back before being
/// written here, for the reason the A-share lists give in <see cref="SectorLists"/>:
/// an unquotable code in a built-in list is a defect nobody who presses fetch can
/// work around.
/// </summary>
public static class Markets
{
    /// <summary>
    /// The Hang Seng sub-indices: the only sector breakdown the source offers for
    /// Hong Kong. Four of them, and they do partition the index — 工商 is the
    /// remainder once finance, property and utilities are taken out, so it is a
    /// coarse grouping rather than an industry classification. Coarse is what the
    /// source has; a fifth list would be invented.
    /// </summary>
    public static readonly RaceEntry[] HangSengSectors =
    [
        new("hkHSF", "金融"),
        new("hkHSP", "地产"),
        new("hkHSU", "公用事业"),
        new("hkHSC", "工商"),
    ];

    /// <summary>
    /// The nine S&amp;P 500 sector SPDRs plus real estate: the US counterpart of the
    /// CSI Level-1 industries, and like them mutually exclusive and collectively
    /// exhaustive over the index. ETFs rather than indices because the source quotes
    /// no US sector index.
    /// </summary>
    public static readonly RaceEntry[] SpdrSectors =
    [
        new("usXLK.AM", "科技"),
        new("usXLF.AM", "金融"),
        new("usXLV.AM", "医疗"),
        new("usXLY.AM", "可选消费"),
        new("usXLP.AM", "必需消费"),
        new("usXLI.AM", "工业"),
        new("usXLE.AM", "能源"),
        new("usXLB.AM", "材料"),
        new("usXLU.AM", "公用事业"),
        new("usXLRE.AM", "房地产"),
    ];

    /// <summary>Hong Kong's indices and the listings people look up by name.</summary>
    public static readonly RaceEntry[] HongKongIndices =
    [
        new("hkHSI", "恒生指数"),
        new("hkHSCEI", "国企指数"),
        new("hkHSTECH", "恒生科技"),
        new("hk00700", "腾讯控股"),
        new("hk09988", "阿里巴巴"),
        new("hk03690", "美团"),
        new("hk00005", "汇丰控股"),
        new("hk01299", "友邦保险"),
    ];

    /// <summary>
    /// The plans the A-share market offers one tap for: the broad ETFs people
    /// actually start a plan on, the gold ETF that is the non-equity arm of the
    /// same habit, and the two indices for asking what the *market* would have
    /// returned. Every code fetched and read back before being written here.
    /// </summary>
    public static readonly RaceEntry[] ASharePlans =
    [
        new("sh510300", "沪深300ETF"),
        new("sh510500", "中证500ETF"),
        new("sz159915", "创业板ETF"),
        new("sh518880", "黄金ETF"),
        new("sh513100", "纳指ETF"),
        new("sh000001", "上证指数"),
        new("sz399006", "创业板指"),
    ];

    /// <summary>Hong Kong's plans: the tracker funds and the indices they follow.</summary>
    public static readonly RaceEntry[] HongKongPlans =
    [
        new("hk02800", "盈富基金"),
        new("hk02828", "恒生中国企业"),
        new("hk03067", "安硕恒生科技"),
        new("hkHSI", "恒生指数"),
        new("hkHSTECH", "恒生科技指数"),
    ];

    /// <summary>The US plans: the broad ETFs and the gold trust.</summary>
    public static readonly RaceEntry[] UnitedStatesPlans =
    [
        new("usSPY.AM", "标普500ETF"),
        new("usQQQ.OQ", "纳指100ETF"),
        new("usDIA.AM", "道琼斯ETF"),
        new("usIWM.AM", "罗素2000ETF"),
        new("usGLD.AM", "黄金ETF"),
    ];

    /// <summary>
    /// The A-share holdings: household names people actually say they have held for
    /// years — the question this page is asked with is usually "what if I'd held
    /// 中国平安 since 2015" — plus the broad tracker and the index for the market
    /// itself. Every code fetched and read back before being written here.
    /// </summary>
    public static readonly RaceEntry[] AShareHoldings =
    [
        new("sh601318", "中国平安"),
        new("sh600519", "贵州茅台"),
        new("sh600036", "招商银行"),
        new("sh600900", "长江电力"),
        new("sz000858", "五粮液"),
        new("sh510300", "沪深300ETF"),
        new("sh000001", "上证指数"),
    ];

    /// <summary>Hong Kong's holdings: the tracker, the names, and the index.</summary>
    public static readonly RaceEntry[] HongKongHoldings =
    [
        new("hk00700", "腾讯控股"),
        new("hk00005", "汇丰控股"),
        new("hk02800", "盈富基金"),
        new("hkHSI", "恒生指数"),
    ];

    /// <summary>The US holdings: the compounding classics and the index trackers.</summary>
    public static readonly RaceEntry[] UnitedStatesHoldings =
    [
        new("usAAPL.OQ", "苹果"),
        new("usBRK.B.N", "伯克希尔B"),
        new("usSPY.AM", "标普500ETF"),
        new("usQQQ.OQ", "纳指100ETF"),
        new("usGLD.AM", "黄金ETF"),
    ];

    /// <summary>
    /// The A-share candles: an index, the names people look up, and the funds — one
    /// of each kind the page is asked about, all already carried by
    /// <see cref="InstrumentNames"/> in every language.
    /// </summary>
    public static readonly RaceEntry[] AShareCandles =
    [
        new("sh000001", "上证指数"),
        new("sz399006", "创业板指"),
        new("sh600519", "贵州茅台"),
        new("sh601318", "中国平安"),
        new("sh510300", "沪深300ETF"),
        new("sz159915", "创业板ETF"),
    ];

    /// <summary>Hong Kong's candles: the index, the names, and the tracker funds.</summary>
    public static readonly RaceEntry[] HongKongCandles =
    [
        new("hkHSI", "恒生指数"),
        new("hkHSTECH", "恒生科技"),
        new("hk00700", "腾讯控股"),
        new("hk00005", "汇丰控股"),
        new("hk02800", "盈富基金"),
        new("hk03067", "安硕恒生科技"),
    ];

    /// <summary>The US candles: the indices, the names, and the funds.</summary>
    public static readonly RaceEntry[] UnitedStatesCandles =
    [
        new("usDJI", "道琼斯"),
        new("usIXIC", "纳斯达克"),
        new("usAAPL.OQ", "苹果"),
        new("usNVDA.OQ", "英伟达"),
        new("usSPY.AM", "标普500ETF"),
        new("usQQQ.OQ", "纳指100ETF"),
    ];

    /// <summary>The US indices and the listings people look up by name.</summary>
    public static readonly RaceEntry[] UnitedStatesIndices =
    [
        new("usDJI", "道琼斯"),
        new("usIXIC", "纳斯达克"),
        new("usINX", "标普500"),
        new("usSPY.AM", "标普500ETF"),
        new("usQQQ.OQ", "纳指100ETF"),
        new("usAAPL.OQ", "苹果"),
        new("usNVDA.OQ", "英伟达"),
        new("usMSFT.OQ", "微软"),
    ];

    private static readonly MarketProfile[] Profiles =
    [
        new(
            MarketId.AShare,
            "MarketAShare",
            // The amount field is 万元 across the A-share exchanges, so ten thousand
            // of it is one 亿.
            AmountToYi: 10_000,
            Volume: VolumeBasis.Detect,
            WholeMarketTurnover: true,
            Intraday: true,
            Rosters:
            [
                new("SectorListLevel1", SectorLists.Level1),
                new("SectorListTheme", SectorLists.Themes),
            ],
            BroadIndices: MonthlySeries.BroadIndices,
            DcaInstruments: ASharePlans,
            PositionInstruments: AShareHoldings,
            CandleInstruments: AShareCandles,
            CurrencyKey: "DcaCurrencyCny"),

        new(
            MarketId.HongKong,
            "MarketHongKong",
            // Hong Kong amounts are 万元 too — verified against a listing whose
            // amount divided by its volume comes back as its closing price.
            AmountToYi: 10_000,
            Volume: VolumeBasis.Detect,
            // Whole-market turnover is the one thing Hong Kong cannot supply: the
            // source's HK codes are the Hang Seng indices, and each carries the
            // turnover of its own constituents, not of the exchange. Adding them
            // would double-count everything in more than one.
            WholeMarketTurnover: false,
            Intraday: true,
            Rosters: [new("SectorListHangSeng", HangSengSectors)],
            BroadIndices: HongKongIndices,
            DcaInstruments: HongKongPlans,
            PositionInstruments: HongKongHoldings,
            CandleInstruments: HongKongCandles,
            CurrencyKey: "DcaCurrencyHkd"),

        new(
            MarketId.UnitedStates,
            "MarketUnitedStates",
            // Dollars, not 万元: a US bar's amount divided by its volume comes back
            // as its price in dollars, so a hundred million of it is one 亿.
            AmountToYi: 100_000_000,
            Volume: VolumeBasis.Shares,
            // The US index "turnover" the source reports is its volume multiplied by
            // the index level — a number with no meaning, since the level of the Dow
            // is not a price anyone paid. There is no whole-market figure to show.
            WholeMarketTurnover: false,
            // The minute endpoint answers a US code with an empty body and code -1.
            Intraday: false,
            Rosters: [new("SectorListSpdr", SpdrSectors)],
            BroadIndices: UnitedStatesIndices,
            DcaInstruments: UnitedStatesPlans,
            PositionInstruments: UnitedStatesHoldings,
            CandleInstruments: UnitedStatesCandles,
            CurrencyKey: "DcaCurrencyUsd"),
    ];

    /// <summary>
    /// The markets, in the order the settings page lists them: the one this app was
    /// built for first, then the two the same pages can be pointed at.
    /// </summary>
    public static readonly MarketId[] All = [MarketId.AShare, MarketId.HongKong, MarketId.UnitedStates];

    public static MarketProfile Of(MarketId id) => Profiles[(int)id];

    /// <summary>
    /// Whether the whole-market turnover page has anything to draw for a market.
    ///
    /// The page's subject is the turnover of an entire market; a figure for one
    /// index's constituents is a different thing wearing the same axis, so where
    /// the source has no whole-market figure the page is not offered at all.
    /// </summary>
    public static bool WholeMarket(MarketId id) => Of(id).WholeMarketTurnover;

    /// <summary>
    /// The exchange suffixes a US ticker can carry, in the order worth trying.
    ///
    /// A bare ticker is not quotable: the endpoint answers <c>usAAPL</c> with a
    /// single bar from 2011, which is worse than an error because it looks like a
    /// listing that barely trades. Nasdaq first because it is the venue most
    /// tickers people search for are on.
    /// </summary>
    public static readonly string[] UsSuffixes = [".OQ", ".N", ".AM"];

    /// <summary>
    /// Whether a US code carries no exchange suffix and so has to be guessed at.
    /// </summary>
    public static bool IsBareUsTicker(string code) =>
        code.StartsWith("us") && !code.AsSpan(2).Contains('.');

    /// <summary>
    /// Puts a code into the shape the quote endpoint accepts.
    ///
    /// The search endpoint answers in lower case — <c>usaapl.oq</c> — while the
    /// chart endpoint refuses anything but <c>usAAPL.OQ</c>, and answers with no
    /// bars rather than with an error, so a code taken from search and passed
    /// straight through reads as an instrument with no history.
    /// </summary>
    public static string Canonize(string code) =>
        code.StartsWith("us", StringComparison.OrdinalIgnoreCase)
            ? "us" + code[2..].ToUpperInvariant()
            : code.ToLowerInvariant();

    /// <summary>
    /// Whether a code is quoted on a mainland exchange — `sh`, `sz` or `bj`.
    ///
    /// The watchlist is deliberately cross-market: a Shanghai share, a Hong Kong one and a New
    /// York one can sit on it together, because the four roster boards that read it are not
    /// governed by the market setting. **Turnover is the exception.** It is a sum of money, and
    /// each venue reports it in its own unit — 万元 in Shanghai, 万港元 in Hong Kong, dollars in
    /// New York — so adding a Hong Kong name into an A-share turnover basket is adding a
    /// different currency to a total the frame will label 亿元 without saying anything.
    ///
    /// Not a conversion: there is no rate on hand that would make the sum honest, and a total
    /// converted at today's rate is a different number from a total converted at each day's.
    /// </summary>
    public static bool IsMainland(string code)
    {
        var canon = Canonize(code);

        return canon.StartsWith("sh", StringComparison.Ordinal)
            || canon.StartsWith("sz", StringComparison.Ordinal)
            || canon.StartsWith("bj", StringComparison.Ordinal);
    }

    /// <summary>
    /// Every entrant a market's rosters offer, deduplicated and in order: the
    /// custom picker's candidate pool.
    /// </summary>
    public static IReadOnlyList<RaceEntry> Union(MarketId id)
    {
        var seen = new HashSet<string>();
        var pool = new List<RaceEntry>();

        foreach (var entry in Of(id).Rosters.SelectMany(r => r.Entries).Concat(Of(id).BroadIndices))
        {
            if (seen.Add(entry.Code))
            {
                pool.Add(entry);
            }
        }

        return pool;
    }
}
