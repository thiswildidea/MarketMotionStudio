using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>One company that is listed twice: an A share and an H share of the same firm.</summary>
/// <param name="A">The mainland code, in the quote source's shape (`sh601398`).</param>
/// <param name="H">The Hong Kong code (`hk01398`).</param>
/// <param name="Name">The company's name, in Chinese, for the <c>INST*</c> key lookup.</param>
public sealed record AhPair(string A, string H, string Name);

/// <summary>
/// The A+H companies: one company, two listings, two currencies, two prices.
///
/// **The list is built in, and this is the one page where that cannot be helped.** A ranking
/// endpoint answers "which companies are largest"; nothing in either source answers "which
/// mainland listings also have a Hong Kong listing" — the 沪港通/深港通 nodes in Sina's own tree
/// carry no children, and Tencent has no equivalent at all. So the pairs are written down.
///
/// What keeps a written-down list honest is that it can be checked: every code in it was read
/// back from the quote endpoint on 2026-10-02, and the one pair that failed is why that check
/// exists — 海通证券 was still in the market when this page was designed and is not any more,
/// its H shares delisted after the merger into 国泰海通. A field of seventy minus one, and the
/// minus one would have been a row that stayed empty forever.
///
/// The list is deliberately the well-known names rather than every pair that exists. A frame
/// draws fifteen rows, and the premium is a story about the large, familiar, dual-listed
/// companies — a hundred and forty small pairs would add rows nobody has heard of to a ranking
/// whose top is already crowded with banks, insurers, oil and brokers.
/// </summary>
public static class AhPairs
{
    /// <summary>How many rows the frame draws.</summary>
    public const int Board = 15;

    /// <summary>
    /// The fewest months a pair must have to be carried at all. Two years: below that there is
    /// nothing to race, and a listing whose H shares appeared last quarter would spend the whole
    /// video as a row that is not there.
    /// </summary>
    public const int FewestMonths = 24;

    public static readonly AhPair[] All =
    [
        new("sh601398", "hk01398", "工商银行"),
        new("sh601939", "hk00939", "建设银行"),
        new("sh601288", "hk01288", "农业银行"),
        new("sh601988", "hk03988", "中国银行"),
        new("sh600036", "hk03968", "招商银行"),
        new("sh601328", "hk03328", "交通银行"),
        new("sh601658", "hk01658", "邮储银行"),
        new("sh601998", "hk00998", "中信银行"),
        new("sh600016", "hk01988", "民生银行"),
        new("sh601818", "hk06818", "光大银行"),
        new("sh601628", "hk02628", "中国人寿"),
        new("sh601318", "hk02318", "中国平安"),
        new("sh601601", "hk02601", "中国太保"),
        new("sh601336", "hk01336", "新华保险"),
        new("sh601319", "hk01339", "中国人保"),
        new("sh601857", "hk00857", "中国石油"),
        new("sh600028", "hk00386", "中国石化"),
        new("sh600938", "hk00883", "中国海油"),
        new("sh601088", "hk01088", "中国神华"),
        new("sh601898", "hk01898", "中煤能源"),
        new("sh600188", "hk01171", "兖矿能源"),
        new("sh601600", "hk02600", "中国铝业"),
        new("sh601899", "hk02899", "紫金矿业"),
        new("sh600362", "hk00358", "江西铜业"),
        new("sh603993", "hk03993", "洛阳钼业"),
        new("sz000898", "hk00347", "鞍钢股份"),
        new("sh600808", "hk00323", "马钢股份"),
        new("sh601390", "hk00390", "中国中铁"),
        new("sh601186", "hk01186", "中国铁建"),
        new("sh601800", "hk01800", "中国交建"),
        new("sh601618", "hk01618", "中国中冶"),
        new("sh601766", "hk01766", "中国中车"),
        new("sh601238", "hk02238", "广汽集团"),
        new("sh601633", "hk02333", "长城汽车"),
        new("sz002594", "hk01211", "比亚迪"),
        new("sz000338", "hk02338", "潍柴动力"),
        new("sh601111", "hk00753", "中国国航"),
        new("sh600115", "hk00670", "中国东航"),
        new("sh600029", "hk01055", "南方航空"),
        new("sh600585", "hk00914", "海螺水泥"),
        new("sh601992", "hk02009", "金隅集团"),
        new("sh600011", "hk00902", "华能国际"),
        new("sh601991", "hk00991", "大唐发电"),
        new("sh600027", "hk01071", "华电国际"),
        new("sz003816", "hk01816", "中国广核"),
        new("sh601607", "hk02607", "上海医药"),
        new("sh600196", "hk02196", "复星医药"),
        new("sh600332", "hk00874", "白云山"),
        new("sz000756", "hk00719", "新华制药"),
        new("sz000513", "hk01513", "丽珠集团"),
        new("sh603259", "hk02359", "药明康德"),
        new("sz300759", "hk03759", "康龙化成"),
        new("sz300347", "hk03347", "泰格医药"),
        new("sh600690", "hk06690", "海尔智家"),
        new("sz000333", "hk00300", "美的集团"),
        new("sh601888", "hk01880", "中国中免"),
        new("sh600660", "hk03606", "福耀玻璃"),
        new("sh601919", "hk01919", "中远海控"),
        new("sh600026", "hk01138", "中远海能"),
        new("sh600999", "hk06099", "招商证券"),
        new("sh600030", "hk06030", "中信证券"),
        new("sh601211", "hk02611", "国泰海通"),
        new("sz000776", "hk01776", "广发证券"),
        new("sh601688", "hk06886", "华泰证券"),
        new("sh601881", "hk06881", "中国银河"),
        new("sh600958", "hk03958", "东方证券"),
        new("sh601788", "hk06178", "光大证券"),
        new("sz000166", "hk06806", "申万宏源"),
        new("sz000002", "hk02202", "万科A"),
    ];
}

/// <summary>
/// Builds the premium race: one horizontal bar per company, ranked by how much more expensive
/// its mainland listing is than its Hong Kong one.
///
/// **The measure.** `premium = A ÷ (H × 港元兑人民币) − 1`. One company, one share, two prices —
/// so unlike a market-cap board, nothing here is derived from a today's-number times a ratio.
/// Both legs are actual traded prices on the same calendar month, and the currency is the only
/// conversion in the page. That is also why this page is the reason
/// <see cref="TencentKline.RawBarsAsync"/> exists: a backward-adjusted series anchors its
/// earliest bar and inflates every later one, so ICBC's A share comes back at 13.34 against a
/// screen price of 8.28, and a premium computed from two such series reads +245% on a stock
/// trading at +26%. **Two markets adjusted separately cannot be compared.**
///
/// **Why monthly.** The same reason the market-cap board is monthly — the endpoint returns a
/// whole history in one reply — and one more of its own: the exchange rate has to line up with
/// both legs, and the rate series only reaches back to 2016. A daily premium would buy nothing
/// on a spread that moves a few points a year, and would cost two hundred requests to page.
///
/// **The axis is a month, keyed by year and month.** Both legs and the rate are all dated
/// wherever their own venue closed the month — the A share on 2026-09-30, the rate on
/// 2026-10-02 for a month that has not settled — so an intersection on the date itself finds
/// 94 months where there are 110. See the same defect in <c>MarketCapSeries</c>, which reported
/// 139 periods for 120 months.
/// </summary>
public static class AhPremiumSeries
{
    /// <summary>
    /// Months asked for in one request. The endpoint serves three hundred; this is the ceiling
    /// the rate series has, so asking for more would only add rows no pair can use.
    /// </summary>
    private const int MonthsWanted = 180;

    /// <summary>The period everything on this page is measured on.</summary>
    private const string Period = "month";

    /// <summary>
    /// The rate that turns Hong Kong dollars into the mainland's. The quote source serves eight
    /// pairs and this is the one the page needs; it is fetched once and used by every pair.
    /// </summary>
    private const string RateCode = "whHKDCNY";

    public static async Task<SectorRaceSeries> LoadAsync(
        TencentKline kline,
        DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation)
    {
        progress.Report(Strings.Get("AhPremiumReadingRate"));

        var rate = ByMonth(await kline.RawBarsAsync(RateCode, Period, start, end, MonthsWanted, cancellation));

        if (rate.Count == 0)
        {
            throw new InvalidOperationException(Strings.Get("AhPremiumNoRate"));
        }

        var loaded = new List<(AhPair Pair, SortedDictionary<DateOnly, double> Premiums)>();

        for (var i = 0; i < AhPairs.All.Length; i++)
        {
            var pair = AhPairs.All[i];

            progress.Report(string.Format(
                CultureInfo.InvariantCulture, "{0} ({1}/{2})", pair.Name, i + 1, AhPairs.All.Length));

            var a = ByMonth(await kline.RawBarsAsync(pair.A, Period, start, end, MonthsWanted, cancellation));
            var h = ByMonth(await kline.RawBarsAsync(pair.H, Period, start, end, MonthsWanted, cancellation));

            var premiums = new SortedDictionary<DateOnly, double>();

            foreach (var month in a.Keys)
            {
                // A month the rate has no close for is a month with no premium: the ratio is not
                // defined without it, and guessing a rate would be inventing the measure.
                if (!h.TryGetValue(month, out var hong) || !rate.TryGetValue(month, out var fx) ||
                    hong <= 0 || fx <= 0 || a[month] <= 0)
                {
                    continue;
                }

                premiums[month] = ((a[month] / (hong * fx)) - 1) * 100;
            }

            if (premiums.Count >= AhPairs.FewestMonths)
            {
                loaded.Add((pair, premiums));
            }
        }

        // The axis: every month any carried pair has a premium for. A union rather than an
        // intersection, so that one company's late Hong Kong listing does not shorten the video
        // for the other sixty-eight — see the note on this type.
        var months = loaded
            .SelectMany(l => l.Premiums.Keys)
            .Distinct()
            .OrderBy(d => d)
            .ToArray();

        if (months.Length < 2 || loaded.Count < 2)
        {
            throw new InvalidOperationException(Strings.Get("AhPremiumTooFew"));
        }

        // Trimmed at both ends to months at least one pair can speak about. The rate trades on
        // days the mainland does not, so the union can otherwise open or close on a month whose
        // only contributor was the currency itself.
        var first = loaded.Min(l => l.Premiums.Keys.First());
        var last = loaded.Max(l => l.Premiums.Keys.Last());

        var axis = months.Where(m => m >= first && m <= last).ToArray();

        // A pair that does not reach the axis's first month is dropped rather than carried at
        // zero. Zero is not "no data" here — it is *parity*, a real and common premium, and a
        // pair sitting at 0% in 2017 because its H shares did not exist until 2024 would read
        // as a company trading exactly level for seven years. The count the page reports is
        // therefore the count it drew, and a shorter span carries more pairs.
        var field = new List<(AhPair Pair, SortedDictionary<DateOnly, double> Premiums)>();

        foreach (var entry in loaded)
        {
            if (entry.Premiums.Keys.First() > axis[0])
            {
                continue;
            }

            // Gaps inside the span are a suspension, and the previous month's premium is what
            // "no trade this month" means — the same rule the rest of this app uses for a
            // halted listing.
            var filled = new SortedDictionary<DateOnly, double>();
            var carried = entry.Premiums.Values.First();

            foreach (var month in axis)
            {
                if (entry.Premiums.TryGetValue(month, out var value))
                {
                    carried = value;
                }

                filled[month] = carried;
            }

            field.Add((entry.Pair, filled));
        }

        if (field.Count < 2)
        {
            throw new InvalidOperationException(Strings.Get("AhPremiumTooFew"));
        }

        var entries = new List<RaceEntry>(field.Count);
        var returns = new List<double[]>(field.Count);
        var amounts = new List<double[]>(field.Count);

        foreach (var (pair, filled) in field)
        {
            entries.Add(new RaceEntry(pair.A, InstrumentNames.Display(pair.A, pair.Name)));
            returns.Add([.. filled.Values]);
            amounts.Add([.. filled.Values]);
        }

        return new SectorRaceSeries(entries, axis, returns, amounts);
    }

    /// <summary>
    /// One close per calendar month, taken from the month's last settlement and dated on the
    /// month's last calendar day.
    ///
    /// The date is synthesised rather than taken from the bars precisely because the bars
    /// disagree: an A-share month closes on the last trading day, a Hong Kong one on the last
    /// business day, the rate on the last banking day, and none of the three is the same day in
    /// every month. Keying on the month and dating it on its own last day is what makes the three
    /// line up — and it is what makes the frame's date read `2026-09-30` rather than one venue's
    /// accident.
    /// </summary>
    private static SortedDictionary<DateOnly, double> ByMonth(IReadOnlyList<TencentKline.CandleBar> bars)
    {
        var byMonth = new SortedDictionary<DateOnly, double>();

        foreach (var bar in bars)
        {
            if (bar.Close > 0)
            {
                byMonth[MonthEnd(bar.Date.Year, bar.Date.Month)] = bar.Close;
            }
        }

        return byMonth;
    }

    private static DateOnly MonthEnd(int year, int month) =>
        new(year, month, DateTime.DaysInMonth(year, month));
}
