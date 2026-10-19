using System.Collections.ObjectModel;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using Windows.Storage;

namespace MarketMotionStudio.Market;

/// <summary>Which way a trade went.</summary>
public enum TradeSide
{
    Buy,
    Sell,
}

/// <summary>
/// One line of a person's holdings **as they stood when the day opened**: how much of it, and
/// what it cost.
///
/// <para>
/// The book is the morning's, not the evening's. It is copied off the broker's holdings screen at
/// the open — that is the screenshot the reader has — and the day's fills move it forward from
/// there. Deriving the opening by undoing the day's trades (which this page used to do) needs the
/// book to be the *closing* position, and then a book entered from the morning screenshot is read
/// backwards on top of itself: 超图软件's 5,900 shares at the open, plus a 3,000 buy and a 5,900
/// sale, came out as 8,800 shares held at 09:30 — two thirds of the day's move reported on shares
/// nobody held.
/// </para>
///
/// <para>
/// <see cref="Cost"/> is the **diluted** cost (摊薄成本) the broker shows. Over a day like
/// 超图软件's — 5,900 in, 3,000 bought at 9.80, 5,900 sold at 10.05 — the broker's closing cost
/// would read 6.544, because a sale's proceeds are netted off what the remaining shares cost. This
/// book keeps the morning's figure instead: it is the one beside the 5,900 on the screenshot the
/// reader typed it from, and the one that makes <c>shares × (price − cost)</c> agree with the
/// broker's 持仓盈亏 for the position they actually carried into the day.
/// </para>
///
/// <para>
/// It is kept in the venue's own currency — a Hong Kong holding is priced in dollars and its cost
/// is too. Converting on the way in would freeze one day's rate into a figure that is meant to
/// last for years.
/// </para>
/// </summary>
/// <param name="Code">The instrument, in the quote endpoint's spelling — `sz300036`, `hk01024`.</param>
/// <param name="Name">The name as the source spells it; displayed through <see cref="InstrumentNames"/>.</param>
/// <param name="Shares">Shares held. Zero is not stored — a closed position is removed.</param>
/// <param name="Cost">Diluted cost per share, in the venue's currency.</param>
public sealed record Holding(string Code, string Name, double Shares, double Cost)
{
    /// <summary>What the position is carried at, in the venue's currency.</summary>
    public double Basis => Shares * Cost;

    /// <summary>
    /// Whether this is a Hong Kong listing, which is the only currency question the two markets
    /// this page carries raise.
    /// </summary>
    [JsonIgnore]
    public bool IsHongKong => Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase);
}

/// <summary>
/// One executed trade, as imported from the broker's own list.
///
/// The day and the clock are both kept: the day decides which session the trade belongs to, and
/// the clock is what lets the intraday curve hold the *old* position until the minute the trade
/// actually happened. A trade filed at 09:30 rather than at its own minute would move the whole
/// morning's profit onto the afternoon.
/// </summary>
/// <param name="Day">`yyyy-MM-dd`.</param>
/// <param name="Time">`HH:mm:ss`, the exchange's own stamp.</param>
/// <param name="Code">The instrument.</param>
/// <param name="Name">Its name at import time, for a journal that can still be read later.</param>
/// <param name="Side">Buy or sell.</param>
/// <param name="Price">The price it filled at, per share, in the venue's currency.</param>
/// <param name="Shares">How many shares changed hands.</param>
public sealed record PortfolioTrade(
    string Day, string Time, string Code, string Name, TradeSide Side, double Price, double Shares)
{
    /// <summary>
    /// What makes two imports of the same list the same trade.
    ///
    /// Importing yesterday's file again is the ordinary case — the reader exports the day's
    /// orders after every close, and the list they paste is cumulative more often than not.
    /// Applying it twice would double the position, and there is nothing on the page afterwards
    /// that would say so. Day, minute, code, side, price and size together are as close to unique
    /// as an order list gets: a genuine second fill of the same size at the same price in the same
    /// second is not a thing that happens.
    /// </summary>
    [JsonIgnore]
    public string Fingerprint => string.Join(
        "|",
        Day,
        Time,
        Code.ToLowerInvariant(),
        Side,
        Price.ToString("0.####", CultureInfo.InvariantCulture),
        Shares.ToString("0.####", CultureInfo.InvariantCulture));

    /// <summary>Minutes since midnight, for ordering a day's trades. Zero when unreadable.</summary>
    [JsonIgnore]
    public int MinuteOfDay => TimeOfDay(Time);

    /// <summary>Reads `HH:mm:ss` (or `HH:mm`) as minutes since midnight; zero if it is neither.</summary>
    public static int TimeOfDay(string clock)
    {
        var parts = clock.Split(':');

        return parts.Length >= 2 &&
               int.TryParse(parts[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out var h) &&
               int.TryParse(parts[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out var m)
            ? (h * 60) + m
            : 0;
    }
}

/// <summary>
/// The holdings and the trades behind them, kept in one file in the app's own state.
///
/// **The book is the opening position of the day being drawn; the journal moves it forward.**
/// Every morning the reader copies the broker's holdings screen into the book, and every evening
/// pastes that day's fills in. Neither of the two is derived from the other: recomputing the book
/// from every trade ever imported would mean keeping every trade ever imported, and would still be
/// wrong for the first position — which was entered by hand rather than bought in front of this
/// app. So the book is stored as entered and importing never edits it; the journal is what makes a
/// re-import harmless and what lets the curve walk the position through the day.
/// </summary>
public static class Portfolio
{
    private const string FileName = "portfolio.json";

    /// <summary>How many days of journal are kept. Enough for a re-import, not an archive.</summary>
    private const int JournalDays = 120;

    private static bool _loaded;

    /// <summary>The book, in the order the reader entered it. Bound by the page's list.</summary>
    public static ObservableCollection<Holding> Holdings { get; } = [];

    private static readonly List<PortfolioTrade> Journal = [];

    /// <summary>Reads the stored book once; seeds the reader's own positions the first time.</summary>
    public static void EnsureLoaded()
    {
        if (_loaded)
        {
            return;
        }

        _loaded = true;

        var path = Path.Combine(ApplicationData.Current.LocalFolder.Path, FileName);

        try
        {
            if (File.Exists(path))
            {
                var stored = JsonSerializer.Deserialize<Book>(File.ReadAllText(path));

                if (stored is not null)
                {
                    foreach (var holding in stored.Holdings)
                    {
                        Holdings.Add(holding);
                    }

                    Journal.AddRange(stored.Trades);
                }

                return;
            }
        }
        catch (Exception)
        {
            // A corrupt or unreadable file is replaced by the seed rather than taking the page
            // down. Losing a book that can be re-entered from the broker app is a small loss;
            // a page that will not open is a total one.
            Holdings.Clear();
            Journal.Clear();
        }

        foreach (var holding in Seed)
        {
            Holdings.Add(holding);
        }

        Save();
    }

    /// <summary>Writes the book and the journal. Small, so synchronously and from the UI thread.</summary>
    public static void Save()
    {
        try
        {
            var path = Path.Combine(ApplicationData.Current.LocalFolder.Path, FileName);

            var json = JsonSerializer.Serialize(
                new Book([.. Holdings], [.. Journal]), BookJson);

            File.WriteAllText(path, json);
        }
        catch (Exception)
        {
            // Remembering the book is worth a lot and worth failing a page over nothing.
        }
    }

    private static readonly JsonSerializerOptions BookJson = new()
    {
        WriteIndented = true,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    /// <summary>Finds a holding by code, or null.</summary>
    public static Holding? Find(string code) =>
        Holdings.FirstOrDefault(h => string.Equals(h.Code, code, StringComparison.OrdinalIgnoreCase));

    /// <summary>Adds a holding, or replaces the one with the same code.</summary>
    public static void Put(Holding holding)
    {
        var at = Holdings.ToList().FindIndex(h =>
            string.Equals(h.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

        if (holding.Shares <= 0)
        {
            if (at >= 0)
            {
                Holdings.RemoveAt(at);
            }

            Save();
            return;
        }

        if (at >= 0)
        {
            Holdings[at] = holding;
        }
        else
        {
            Holdings.Add(holding);
        }

        Save();
    }

    /// <summary>Drops a holding by code. Does not touch the journal — history stays history.</summary>
    public static void Remove(string code)
    {
        var at = Holdings.ToList().FindIndex(h =>
            string.Equals(h.Code, code, StringComparison.OrdinalIgnoreCase));

        if (at >= 0)
        {
            Holdings.RemoveAt(at);
            Save();
        }
    }

    /// <summary>What a day's import did, so the page can say it rather than leaving it to be guessed.</summary>
    /// <param name="Applied">Trades that were new and are now on the journal.</param>
    /// <param name="Duplicates">Trades already in the journal, ignored.</param>
    /// <param name="Unmatched">Sells that sold more than the book held when they happened.</param>
    public sealed record ImportResult(int Applied, int Duplicates, int Unmatched);

    /// <summary>
    /// Puts a day's fills on the journal, once, and **leaves the book alone**.
    ///
    /// The book is the morning's position; folding the day's fills into it would turn it into the
    /// evening's, and the next load would then walk the position through the day a second time.
    /// That is not a hypothetical: it is why a sale used to move the book's cost and why the page's
    /// numbers stopped agreeing with the broker's.
    ///
    /// Clock order is kept in the journal — a curve reads them in order, and a same-day round trip
    /// only adds up if the buy is seen before the sell.
    /// </summary>
    public static ImportResult Apply(IReadOnlyList<PortfolioTrade> trades)
    {
        EnsureLoaded();

        var known = Journal.Select(t => t.Fingerprint).ToHashSet(StringComparer.Ordinal);

        var applied = 0;
        var duplicates = 0;
        var fresh = new List<string>();

        foreach (var trade in trades.OrderBy(t => t.Day, StringComparer.Ordinal)
                                    .ThenBy(t => t.MinuteOfDay)
                                    .ThenBy(t => t.Time, StringComparer.Ordinal))
        {
            if (!known.Add(trade.Fingerprint))
            {
                duplicates++;
                continue;
            }

            Journal.Add(trade);
            fresh.Add(trade.Fingerprint);
            applied++;
        }

        Prune();
        Save();

        return new ImportResult(applied, duplicates, Oversold(fresh));
    }

    /// <summary>
    /// How many of the fills just imported sold more than the book held at that moment.
    ///
    /// Reported rather than refused: the fill happened, and the honest reading of "sold 100 shares
    /// of something the morning's screenshot does not list" is that the book is missing a row — a
    /// position bought before the app existed, or a screenshot scrolled past it. Refusing the
    /// import would drop the rest of the day's fills along with it. The page shows the count as a
    /// warning; the curve books no cash for the shares that were not there.
    /// </summary>
    private static int Oversold(IReadOnlyCollection<string> fingerprints)
    {
        if (fingerprints.Count == 0)
        {
            return 0;
        }

        var counted = 0;

        foreach (var day in Journal.Where(t => fingerprints.Contains(t.Fingerprint))
                                   .Select(t => t.Day)
                                   .Distinct(StringComparer.Ordinal))
        {
            var running = Holdings.ToDictionary(h => h.Code, h => h.Shares, StringComparer.OrdinalIgnoreCase);

            foreach (var trade in Journal.Where(t => t.Day == day)
                                         .OrderBy(t => t.MinuteOfDay)
                                         .ThenBy(t => t.Time, StringComparer.Ordinal))
            {
                running.TryGetValue(trade.Code, out var held);

                if (trade.Side == TradeSide.Sell &&
                    held < trade.Shares &&
                    fingerprints.Contains(trade.Fingerprint))
                {
                    counted++;
                }

                running[trade.Code] = trade.Side == TradeSide.Buy
                    ? held + trade.Shares
                    : Math.Max(0, held - trade.Shares);
            }
        }

        return counted;
    }

    /// <summary>
    /// Everything still journalled, oldest day first.
    ///
    /// Handed to the loader whole, and the loader picks the day it ended up drawing out of it.
    /// Asking for "today's" first — which is what the page did — drops the fills of the day the
    /// frame is actually showing whenever that day is not today, and that is every morning before
    /// the market opens: the page draws the last session that traded, and the trades stamped on
    /// that session are exactly the ones it needs. The curve would draw the day with no fills on
    /// it, the count would read zero, and nothing on the page would say why.
    ///
    /// A copy rather than the list itself: the loader runs off the UI thread, and `Prune` can
    /// drop a day out from under it.
    /// </summary>
    public static IReadOnlyList<PortfolioTrade> Trades => [.. Journal];

    /// <summary>Drops journal entries older than the window, so the file cannot grow forever.</summary>
    private static void Prune()
    {
        var cutoff = DateTime.Today.AddDays(-JournalDays).ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

        Journal.RemoveAll(t => string.CompareOrdinal(t.Day, cutoff) < 0);
    }

    /// <summary>
    /// The reader's positions **at the open** on 2026-10-19, read off the broker's holdings
    /// screen before the bell.
    ///
    /// Costs are the diluted ones the broker shows, in each venue's own currency: the two Hong
    /// Kong rows are in dollars. 大秦铁路 is carried at 5.804 against a price of 4.930 because it
    /// is mid ex-dividend on that screenshot — the broker says so itself ("除权除息中 清算后重新
    /// 计算"), and carrying the pre-adjustment figure is what the screenshot actually says.
    ///
    /// **The three that traded that day are in at their morning size**, not at the size the
    /// evening left behind: 超图软件 5,900 (bought 3,000 at 09:24, sold 5,900 at 09:35), 中望软件
    /// 700 (sold 200 twice), 顺丰控股 100 (sold out at 09:40). A position that was sold flat is
    /// still a position at 09:30, and leaving it out turns its sale into money the page has no
    /// shares to charge for — the old book dropped it the moment the row hit zero shares, and the
    /// day then reported ¥3,180 of profit that was really just the sale of a holding it never knew
    /// about.
    /// </summary>
    private static readonly Holding[] Seed =
    [
        new("sz300036", "超图软件", 5900, 8.387),
        new("sz002352", "顺丰控股", 100, 24.545),
        new("sh688083", "中望软件", 700, 33.448),
        new("sz002739", "儒意电影", 100, 2.497),
        new("sh600258", "首旅酒店", 100, 8.979),
        new("sh513180", "恒生科技ETF华夏", 10000, 0.528),
        new("sh601006", "大秦铁路", 2200, 5.804),
        new("hk01024", "快手-W", 600, 34.062),
        new("sz000858", "五粮液", 400, 83.422),
        new("hk02015", "理想汽车-W", 600, 54.954),
    ];

    /// <summary>The shape the file is written in. Two lists, named, so the file can be read.</summary>
    private sealed record Book(List<Holding> Holdings, List<PortfolioTrade> Trades);
}
