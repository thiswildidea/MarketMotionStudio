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
/// One line of a person's holdings: how much of it, and what it cost.
///
/// <para>
/// <see cref="Cost"/> is the **diluted** cost (摊薄成本), which is the figure the broker app these
/// rows are read off shows, and the reason it is that one rather than a weighted average is
/// arithmetic rather than preference. The two screenshots this page was built from are one day
/// apart: 超图软件 went into the day holding 5,900 shares, bought 3,000 at 9.80, sold 5,900 at
/// 10.05, and ended at 3,000 shares with a cost of 6.544. A weighted average would still say
/// 8.869 — it only ever moves on a purchase — so the 6.544 can only be the diluted figure, in
/// which a sale's proceeds are netted off what the remaining shares cost. Reversing it gives a
/// starting cost of 8.394, which is where the stock actually traded the day before. 中望软件
/// gives the same answer from the same arithmetic (700 shares at 33.476, two sales, 300 left at
/// 14.444). Importing a broker's trades and then showing a cost the broker does not show would
/// make every number on this page disagree with the app the reader reconciles it against.
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
/// **The holdings are the state, not a replay of the journal.** Recomputing the book from every
/// trade ever imported would mean keeping every trade ever imported, and would still be wrong for
/// the first position — which was entered by hand from a screenshot rather than bought in front of
/// this app. So the book is what is stored; the journal is what makes a re-import harmless and
/// what lets the intraday curve reconstruct this morning's position (today's holdings, minus
/// today's confirmed trades) without a second copy of history.
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
    /// <param name="Applied">Trades that were new and have been folded into the book.</param>
    /// <param name="Duplicates">Trades already in the journal, ignored.</param>
    /// <param name="Unmatched">Sells of an instrument that is not held, ignored.</param>
    public sealed record ImportResult(int Applied, int Duplicates, int Unmatched);

    /// <summary>
    /// Folds a day's trades into the book, once.
    ///
    /// Applied in clock order rather than in the order the list happens to arrive: the cost of a
    /// position is path-dependent when both a purchase and a sale touch it on the same day, and
    /// the broker's own figures are the ones that follow the clock. (超图软件 on the sample day:
    /// buying first and selling after leaves 6.544, selling first would not.)
    /// </summary>
    public static ImportResult Apply(IReadOnlyList<PortfolioTrade> trades)
    {
        EnsureLoaded();

        var known = Journal.Select(t => t.Fingerprint).ToHashSet(StringComparer.Ordinal);

        var applied = 0;
        var duplicates = 0;
        var unmatched = 0;

        foreach (var trade in trades.OrderBy(t => t.Day, StringComparer.Ordinal)
                                    .ThenBy(t => t.MinuteOfDay)
                                    .ThenBy(t => t.Time, StringComparer.Ordinal))
        {
            if (!known.Add(trade.Fingerprint))
            {
                duplicates++;
                continue;
            }

            var holding = Find(trade.Code);

            if (trade.Side == TradeSide.Sell && (holding is null || holding.Shares <= 0))
            {
                // Not folded in, and not journalled either: the reader will fix the buy that is
                // missing and import again, and a journal entry would then make that sale look
                // like a duplicate and drop it a second time.
                unmatched++;
                continue;
            }

            var shares = holding?.Shares ?? 0;
            var cost = holding?.Cost ?? 0;
            var name = holding?.Name ?? trade.Name;

            if (trade.Side == TradeSide.Buy)
            {
                var after = shares + trade.Shares;
                cost = after > 0 ? ((shares * cost) + (trade.Shares * trade.Price)) / after : trade.Price;
                shares = after;
            }
            else
            {
                // Selling more than is held is a typo or a missing purchase. Clamped rather than
                // refused: the trade did happen, and a book that says so is closer to the truth
                // than one that ignores the sale.
                var sold = Math.Min(trade.Shares, shares);
                var after = shares - sold;

                cost = after > 0 ? ((shares * cost) - (sold * trade.Price)) / after : 0;
                shares = after;
            }

            Put(new Holding(trade.Code, name, Math.Round(shares, 4), Math.Round(cost, 4)));
            Journal.Add(trade);
            applied++;
        }

        Prune();
        Save();

        return new ImportResult(applied, duplicates, unmatched);
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

    /// <summary>
    /// How many shares of each code were held when a day opened: today's book with today's trades
    /// undone.
    ///
    /// This is the one use of the journal that is not about duplicates, and it is why the journal
    /// outlives a page's session. A curve that started from *now* would hold this afternoon's
    /// position all morning — after a day like 超图软件's, where 5,900 shares became 3,000, it
    /// would report the morning's move on two thirds of the shares that were actually exposed to
    /// it.
    /// </summary>
    public static Dictionary<string, double> OpeningShares(string day)
    {
        var opening = Holdings.ToDictionary(h => h.Code, h => h.Shares, StringComparer.OrdinalIgnoreCase);

        foreach (var trade in Journal.Where(t => t.Day == day))
        {
            opening.TryGetValue(trade.Code, out var held);

            var before = trade.Side == TradeSide.Buy ? held - trade.Shares : held + trade.Shares;

            if (before <= 0)
            {
                opening.Remove(trade.Code);
            }
            else
            {
                opening[trade.Code] = before;
            }
        }

        return opening;
    }

    /// <summary>Drops journal entries older than the window, so the file cannot grow forever.</summary>
    private static void Prune()
    {
        var cutoff = DateTime.Today.AddDays(-JournalDays).ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

        Journal.RemoveAll(t => string.CompareOrdinal(t.Day, cutoff) < 0);
    }

    /// <summary>
    /// The reader's positions on the day this page was built — read off the closing holdings
    /// screenshot, which shows ten rows of which one (顺丰控股) is closed and therefore not a
    /// position at all.
    ///
    /// Costs are the diluted ones the broker shows, in each venue's own currency: the two Hong
    /// Kong rows are in dollars. 大秦铁路 is carried at 5.804 against a price of 4.930 because it
    /// is mid ex-dividend on that screenshot — the broker says so itself ("除权除息中 清算后重新
    /// 计算"), and carrying the pre-adjustment figure is what the screenshot actually says.
    /// </summary>
    private static readonly Holding[] Seed =
    [
        new("sz300036", "超图软件", 3000, 6.544),
        new("sh688083", "中望软件", 300, 14.444),
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
