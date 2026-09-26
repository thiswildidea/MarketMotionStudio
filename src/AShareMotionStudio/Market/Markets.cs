using AShareMotionStudio.Localization;

namespace AShareMotionStudio.Market;

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
public sealed record MarketProfile(
    MarketId Id,
    string NameKey,
    double AmountToYi,
    VolumeBasis Volume,
    bool WholeMarketTurnover,
    bool Intraday,
    RosterList[] Rosters,
    RaceEntry[] BroadIndices)
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
            BroadIndices: MonthlySeries.BroadIndices),

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
            BroadIndices: HongKongIndices),

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
            BroadIndices: UnitedStatesIndices),
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
