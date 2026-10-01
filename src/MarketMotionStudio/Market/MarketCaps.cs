using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The candidates a market-cap race is drawn from: a wide field per market, and the board shows
/// whichever fifteen of them were largest at each moment.
///
/// **A field, not a board.** The first version of this page fixed fifteen listings and ranked
/// those fifteen against each other, which is a different thing from a market-cap board: nobody
/// could enter it and nobody could leave, so "did 工商银行 ever lose the top spot" had an answer
/// and "who is on this board now" did not. The reason was cost — a daily series is about 640
/// calendar days to a request, so a wide field over ten years is thousands of requests — and the
/// reason was wrong: **the monthly endpoint returns three hundred bars in one reply**, which is
/// twenty-five years, on every venue this app quotes. A hundred listings then cost a hundred
/// requests, and the board can be rebuilt from scratch month by month.
///
/// **Wide enough that nobody who belonged is missing.** The field is not the top fifteen of today;
/// it is the companies that have been near the top of this market at any point in the window —
/// today's leaders, the four state banks, the insurers, the oil majors, and the ones that fell out
/// of fashion (万科, 上汽, 中国重工). Every code here was read back from the snapshot endpoint
/// before being written down, and the values are in NOTES.
/// </summary>
public static class MarketCapLists
{
    /// <summary>How many rows the board shows.</summary>
    public const int Board = 15;

    /// <summary>
    /// The mainland's **archive**: companies that have been near the top of this market at any
    /// point in the window, kept for the ones today's ranking no longer carries.
    ///
    /// Not the field itself — the field is today's ranking (see <see cref="FieldAsync"/>) and this
    /// is what is added to it. It exists because a board that runs ten years needs the companies
    /// that were large *then*: 万科 and 中国重工 and 上汽 are nowhere near the top two hundred
    /// today, and without them the left-hand end of the video is a history that is missing the
    /// companies that were in it.
    ///
    /// Two entries here are also in today's top ten — 长鑫科技 and 中国海油 — and they are kept
    /// anyway, because this list is also the fallback when the ranking endpoint cannot be reached,
    /// and a fallback that is missing the largest company on the market is not a fallback.
    /// </summary>
    public static readonly RaceEntry[] AShare =
    [
        new("sh688825", "长鑫科技"),
        new("sh600938", "中国海油"),
        new("sh601398", "工商银行"),
        new("sh601939", "建设银行"),
        new("sh601288", "农业银行"),
        new("sh601988", "中国银行"),
        new("sh600941", "中国移动"),
        new("sh601857", "中国石油"),
        new("sh600028", "中国石化"),
        new("sh600519", "贵州茅台"),
        new("sz300750", "宁德时代"),
        new("sh601138", "工业富联"),
        new("sh600036", "招商银行"),
        new("sh601628", "中国人寿"),
        new("sh601088", "中国神华"),
        new("sh601318", "中国平安"),
        new("sh601899", "紫金矿业"),
        new("sz002594", "比亚迪"),
        new("sh600900", "长江电力"),
        new("sz000333", "美的集团"),
        new("sh601728", "中国电信"),
        new("sh600030", "中信证券"),
        new("sh600276", "恒瑞医药"),
        new("sh601601", "中国太保"),
        new("sz002415", "海康威视"),
        new("sz300059", "东方财富"),
        new("sz000858", "五粮液"),
        new("sz000001", "平安银行"),
        new("sh600309", "万华化学"),
        new("sz000651", "格力电器"),
        new("sh601668", "中国建筑"),
        new("sh601336", "新华保险"),
        new("sh600887", "伊利股份"),
        new("sh600809", "山西汾酒"),
        new("sh600050", "中国联通"),
        new("sh601111", "中国国航"),
        new("sh601633", "长城汽车"),
        new("sh601390", "中国中铁"),
        new("sh600585", "海螺水泥"),
        new("sh601012", "隆基绿能"),
        new("sh601186", "中国铁建"),
        new("sz002304", "洋河股份"),
        new("sh600000", "浦发银行"),
        new("sh601166", "兴业银行"),
        new("sh600016", "民生银行"),
        new("sh601818", "光大银行"),
        new("sh601169", "北京银行"),
        new("sh600104", "上汽集团"),
        new("sz000002", "万科A"),
        new("sh601766", "中国中车"),
        new("sh601989", "中国重工"),
        new("sh600150", "中国船舶"),
        new("sh600031", "三一重工"),
        new("sz000725", "京东方A"),
        new("sz002475", "立讯精密"),
        new("sh603259", "药明康德"),
        new("sh600438", "通威股份"),
        new("sh600690", "海尔智家"),
        new("sz000568", "泸州老窖"),
        new("sh600048", "保利发展"),
        new("sz000063", "中兴通讯"),
        new("sh601225", "陕西煤业"),
        new("sh601658", "邮储银行"),
        new("sh601998", "中信银行"),
    ];

    /// <summary>Hong Kong's field: the two internet giants, the insurers, the H-share lines of the state banks, and the property developers that used to lead it.</summary>
    public static readonly RaceEntry[] HongKong =
    [
        new("hk00700", "腾讯控股"),
        new("hk09988", "阿里巴巴"),
        new("hk03690", "美团"),
        new("hk00005", "汇丰控股"),
        new("hk01299", "友邦保险"),
        new("hk01398", "工商银行"),
        new("hk00939", "建设银行"),
        new("hk03988", "中国银行"),
        new("hk00857", "中国石油股份"),
        new("hk00386", "中国石油化工股份"),
        new("hk00941", "中国移动"),
        new("hk01810", "小米集团"),
        new("hk09618", "京东集团"),
        new("hk09999", "网易"),
        new("hk00388", "香港交易所"),
        new("hk00981", "中芯国际"),
        new("hk02020", "安踏体育"),
        new("hk01109", "华润置地"),
        new("hk00016", "新鸿基地产"),
        new("hk00001", "长和"),
        new("hk00883", "中国海洋石油"),
        new("hk00762", "中国联通"),
        new("hk01024", "快手"),
        new("hk09961", "携程集团"),
        new("hk09888", "百度集团"),
        new("hk06618", "京东健康"),
        new("hk02331", "李宁"),
        new("hk01088", "中国神华"),
        new("hk00902", "华能国际电力股份"),
        new("hk06862", "海底捞"),
        new("hk00291", "华润啤酒"),
        new("hk01093", "石药集团"),
        new("hk01177", "中国生物制药"),
        new("hk02628", "中国人寿"),
        new("hk00788", "中国铁塔"),
    ];

    /// <summary>
    /// New York's field, with the venue suffix the chart endpoint wants.
    ///
    /// The two endpoints disagree about the code and neither says so: the chart endpoint reads
    /// `usAAPL.OQ` and *silently* returns nothing for the bare ticker, while the snapshot endpoint
    /// is the other way round. Carrying the suffixed form is what settles it — the chart call gets
    /// its code in one request, and `StockDirectory.SnapshotCode` strips the venue for the snapshot
    /// call, which is the one place that conversion has to happen.
    ///
    /// The venues were read back from the snapshot endpoint rather than assumed; the field's own
    /// entry in NOTES records them.
    /// </summary>
    public static readonly RaceEntry[] UnitedStates =
    [
        new("usAAPL.OQ", "苹果"),
        new("usMSFT.OQ", "微软"),
        new("usNVDA.OQ", "英伟达"),
        new("usGOOGL.OQ", "谷歌"),
        new("usAMZN.OQ", "亚马逊"),
        new("usMETA.OQ", "Meta"),
        new("usTSLA.OQ", "特斯拉"),
        new("usAVGO.OQ", "博通"),
        new("usLLY.N", "礼来"),
        new("usJPM.N", "摩根大通"),
        new("usV.N", "Visa"),
        new("usXOM.N", "埃克森美孚"),
        new("usWMT.OQ", "沃尔玛"),
        new("usORCL.N", "甲骨文"),
        new("usBRK.B.N", "伯克希尔B"),
        new("usUNH.N", "联合健康"),
        new("usMA.N", "万事达"),
        new("usCOST.OQ", "好市多"),
        new("usHD.N", "家得宝"),
        new("usPG.N", "宝洁"),
        new("usJNJ.N", "强生"),
        new("usNFLX.OQ", "奈飞"),
        new("usAMD.OQ", "超威半导体"),
        new("usCRM.N", "赛富时"),
        new("usADBE.OQ", "Adobe"),
        new("usKO.N", "可口可乐"),
        new("usPEP.OQ", "百事可乐"),
        new("usDIS.N", "迪士尼"),
        new("usINTC.OQ", "英特尔"),
        new("usCSCO.OQ", "思科"),
        new("usPFE.N", "辉瑞"),
        new("usBA.N", "波音"),
        new("usGE.N", "GE航天航空"),
        new("usT.N", "美国电话电报"),
        new("usCVX.N", "雪佛龙"),
        new("usMRK.N", "默沙东"),
        new("usABBV.N", "艾伯维"),
        new("usBAC.N", "美国银行"),
        new("usWFC.N", "富国银行"),
        new("usC.N", "花旗集团"),
        new("usGS.N", "高盛"),
        new("usMS.N", "摩根士丹利"),
        new("usBLK.N", "贝莱德"),
    ];

    public static RaceEntry[] Of(MarketId id) => id switch
    {
        MarketId.HongKong => HongKong,
        MarketId.UnitedStates => UnitedStates,
        _ => AShare,
    };

    /// <summary>
    /// The candidates a fetch runs on: **today's ranking, plus the archive.**
    ///
    /// The mainland gets its top two hundred asked for at fetch time, so a company that listed last
    /// month is on the board without anybody editing a list — which is the defect this replaced.
    /// The archive is added to it, minus whatever the ranking already carried.
    ///
    /// **Hong Kong and New York get the archive alone**, and that is a limitation rather than a
    /// decision: Sina's ranking serves the mainland (`node=hs_a`) and answers `[]` for `hk_stock`
    /// and `us_stock`, and Tencent has no ranking at all. Their fields were each read back from the
    /// snapshot endpoint instead, and they are what this app has. A market the source cannot feed
    /// does not get a page — but these two can be fed, just not re-ranked daily, so they keep a
    /// board with a fixed field.
    /// </summary>
    public static async Task<IReadOnlyList<RaceEntry>> FieldAsync(
        MarketId id, IProgress<string> progress, CancellationToken cancellation)
    {
        var archive = Of(id);

        if (id is not MarketId.AShare)
        {
            return archive;
        }

        var ranked = await RankingSource.LargestAsync(progress, cancellation);

        var carried = ranked.Select(e => e.Code).ToHashSet(StringComparer.OrdinalIgnoreCase);

        return [.. ranked, .. archive.Where(e => !carried.Contains(e.Code))];
    }

    /// <summary>The unit word for a bar's value label: 亿元, 亿港元 or 亿美元, by market.</summary>
    public static string UnitKey(MarketId id) => id switch
    {
        MarketId.HongKong => "MarketCapUnitHkd",
        MarketId.UnitedStates => "MarketCapUnitUsd",
        _ => "MarketCapUnitCny",
    };
}

/// <summary>
/// Builds a market-cap board: one batched snapshot for today's scale, one monthly request per
/// listing for the years behind it, and every month's market value for every candidate.
///
/// **Why monthly.** A daily series is about 640 calendar days to a request, so ten years of a
/// sixty-two-listing field is six requests each — three hundred and seventy, for a board whose
/// subject moves a few times a year. The monthly series returns three hundred bars in a *single*
/// reply, twenty-five years, on all three venues: the field costs one request each and the whole
/// board is refetched in about eighty. The resolution that buys is the resolution the subject has
/// — a market-cap ranking is a slow variable, and the renderer interpolates between the months it
/// is given anyway.
///
/// **How a past market value is known.** The source serves today's total market value and nothing
/// else: a share count's own history is not served at all, so each month's value is
/// `today's value × the adjusted price ratio`. That is exact as far as the adjusted series is
/// exact — a bonus issue or a split moves the price and the share count by the same factor and the
/// adjusted series cancels it. **A dividend is not cancelled**, because the adjusted series
/// reinvests it, so a heavy payer's past value reads low and it looks like it grew faster than it
/// did. The manual and the settings panel both say so.
/// </summary>
public static class MarketCapSeries
{
    /// <summary>
    /// Months asked for in one request. The endpoint serves three hundred; a hundred and eighty is
    /// fifteen years, which is past every span this page offers and short of the point where a
    /// larger reply is worth its size.
    /// </summary>
    private const int MonthsWanted = 180;

    /// <summary>
    /// The period the field is measured on. Monthly, for the reason in the type's own note.
    /// </summary>
    private const string Period = "month";

    public static async Task<SectorRaceSeries> LoadAsync(
        TencentKline kline,
        StockDirectory directory,
        MarketId market,
        DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation)
    {
        // Today's ranking first, so the field is the market's current order rather than a list
        // somebody wrote down. See MarketCapLists.FieldAsync.
        var field = await MarketCapLists.FieldAsync(market, progress, cancellation);

        if (field.Count < MarketCapLists.Board)
        {
            throw new InvalidOperationException(Strings.Get("MarketCapTooFew"));
        }

        // One request for the whole field rather than one per entrant.
        progress.Report(Strings.Get("MarketCapSnapshotting"));

        var snapshot = await directory.SnapshotsAsync([.. field.Select(e => e.Code)], cancellation);

        var closes = new List<(RaceEntry Entry, SortedDictionary<DateOnly, double> Days)>();

        for (var i = 0; i < field.Count; i++)
        {
            var entry = field[i];

            progress.Report(string.Format(
                CultureInfo.InvariantCulture, "{0} ({1}/{2})", entry.Name, i + 1, field.Count));

            var bars = await kline.CandleBarsAsync(entry.Code, Period, start, end, MonthsWanted, cancellation);

            var days = new SortedDictionary<DateOnly, double>();

            foreach (var bar in bars)
            {
                if (bar.Close > 0)
                {
                    days[bar.Date] = bar.Close;
                }
            }

            // A listing with no rows in the window is not an error here, and must not be: a field
            // this wide spans listings that did not exist yet at the range's start. It reads as
            // zero for every month, which is what "not on the board yet" looks like on a bar chart.
            closes.Add((entry, days));
        }

        // A listing the snapshot endpoint did not answer for has no scale at all, and a code that
        // cannot be quoted is this file's bug rather than a fact about the window.
        foreach (var (entry, _) in closes)
        {
            if (!snapshot.TryGetValue(entry.Code, out var s) || s.TotalCapYi <= 0)
            {
                throw new InvalidOperationException(
                    Strings.Format("MarketCapSnapshotMissing", entry.Name));
            }
        }

        // One entry per calendar month, dated on the month's last bar anyone has.
        //
        // Not the plain union of every date that appeared: a monthly row is dated on the month's
        // last *trading* day, and a listing that was suspended for a fortnight has its last
        // trading day somewhere in the middle — so the union of sixty-two listings' monthly dates
        // is not 120 dates but 139, and nineteen of those "periods" advance a single listing while
        // the other sixty-one carry a stale value. The board would visibly stutter in those
        // months. Right after it ran, a ten-year board reported 139 periods for a hundred and
        // twenty months.
        var dates = closes
            .SelectMany(c => c.Days.Keys)
            .GroupBy(d => (d.Year, d.Month))
            .Select(g => g.Max())
            .OrderBy(d => d)
            .ToArray();

        if (dates.Length < 5)
        {
            throw new InvalidOperationException(Strings.Get("SectorTooFewSharedDays"));
        }

        var caps = new List<double[]>();

        foreach (var (entry, days) in closes)
        {
            var latest = snapshot[entry.Code].TotalCapYi;
            var newest = days.Count > 0 ? days.Values.Last() : 0;
            var row = new double[dates.Length];
            var held = 0.0;

            for (var i = 0; i < dates.Length; i++)
            {
                if (days.TryGetValue(dates[i], out var close))
                {
                    held = close;
                }

                // Carried forward rather than dropped, so a suspension reads as a flat bar
                // instead of a company that vanished for a month. Before the first bar it is zero,
                // which is the listing not existing yet.
                row[i] = newest > 0 ? latest * held / newest : 0;
            }

            caps.Add(row);
        }

        var entriesOut = closes.Select(c => c.Entry).ToArray();

        // The race model carries two measures; this page has one, and it lives in both slots so
        // that any path through the renderer reads the same numbers.
        return new SectorRaceSeries(entriesOut, dates, caps, caps);
    }
}
