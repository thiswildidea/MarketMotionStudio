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
/// Which of the two books the portfolio pages are reading.
///
/// <para>
/// **Two books, because two questions are asked and one answer will not serve both.** The
/// mainland holdings are the book the reader looks at every morning, and the account they belong
/// to is an A-share one. The Hong Kong positions are held through 港股通: same person, same
/// broker app, a different venue with a different currency, a different fee schedule and a
/// different settlement story. Putting both in one curve is not wrong arithmetic, it is two
/// answers wearing one axis — and it is the reason a 200-share Hong Kong sale could move a
/// mainland day by more than all of the mainland's own trades put together.
/// </para>
///
/// <para>
/// **The two differ in more than which rows they carry.** <see cref="AShare"/> is a book with a
/// history, so it can be asked about a week, a month or a year, and it is answered from the
/// snapshot plus the fills since it. <see cref="WithKong"/> is a book about **today only**: the
/// Hong Kong side is walked from this morning's opening through today's fills, and there is no
/// snapshot to rebuild a past day from — which is why the span picker is hidden under it rather
/// than shown and answered wrong.
/// </para>
///
/// <para>
/// Each carries **its own baseline**, because they start from different mornings' figures for
/// different reasons: the Hong Kong one is today's opening position, and the mainland one is the
/// snapshot the reader took. Switching the scope switches the baseline with it.
/// </para>
/// </summary>
public enum PortfolioScope
{
    /// <summary>
    /// The mainland holdings alone: `sh`, `sz` and `bj`. Hong Kong rows and Hong Kong fills are
    /// left out of the baseline, out of the replay and out of the list.
    /// </summary>
    AShare = 0,

    /// <summary>
    /// The mainland holdings **and** the Hong Kong ones bought through 港股通, drawn for today
    /// from the position the day opened on.
    /// </summary>
    WithKong = 1,
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

    /// <summary>
    /// Whether this fill was made in Hong Kong.
    ///
    /// The mainland book asks this of every archived fill so that it can leave them out: a fill
    /// in another currency, at another fee schedule, on shares the mainland baseline does not
    /// hold. The archive itself keeps them — history is history — and the other book reads it
    /// whole.
    /// </summary>
    [JsonIgnore]
    public bool IsHongKong => Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase);

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
/// During a session the book is the morning's and every fill walks it forward minute by minute;
/// the journal is what makes a re-import harmless and what lets the curve walk the position
/// through the day.
///
/// <para>
/// **At the day's end the book rolls forward** (<see cref="RollForward"/>): once the app is
/// quit — and, as a net for a hard kill, again at the next start — every fill from a session
/// before today is folded into the book at its diluted cost and taken out of the journal. The
/// stored book is then the latest closing, so the next morning's import replays on top of it
/// without anyone copying a holdings screen by hand. Folded fills are remembered by
/// fingerprint, which is also what keeps a re-import of an already-folded day from applying
/// a second time.
/// </para>
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

    /// <summary>
    /// Fingerprints of trades already folded into the book, so folding the same day twice — or
    /// folding a list that was already folded — does not move the book a second time. A folded
    /// trade leaves the journal, so without this the only way to tell "already folded" from
    /// "never imported" would be to guess, and guessing wrong would double the position.
    /// </summary>
    private static readonly HashSet<string> Folded = [];

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

                if (stored.Folded is { } folded)
                {
                    foreach (var fingerprint in folded)
                    {
                        Folded.Add(fingerprint);
                    }
                }
                }

                // The net for a hard kill: whatever a quit failed to roll forward — or a session
                // that ended under task manager — rolls here, before any page can build a session
                // on a book that is no longer the latest morning.
                RollForward();

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
                new Book([.. Holdings], [.. Journal], [.. Folded]), BookJson);

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

    /// <summary>
    /// Replaces the whole book in one go, dropping any row that ends up at zero shares.
    ///
    /// **The dialog needs this because it edits the day's *closing*, while the book holds its
    /// opening.** A reader who changes one row has said "the position is these numbers" about the
    /// day they are looking at; the other nine rows then have to move with it, or the book becomes
    /// a mix of two moments — nine morning figures beside one evening figure, a book nobody ever
    /// held. So the first edit writes the whole snapshot, and the single row follows it in.
    /// </summary>
    public static void ReplaceAll(IEnumerable<Holding> rows)
    {
        EnsureLoaded();

        Holdings.Clear();

        foreach (var row in rows)
        {
            if (row.Shares > 0)
            {
                Holdings.Add(row);
            }
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

        // Both journals of truth: a fill still waiting folds is a duplicate by its journal entry,
        // and a fill already rolled into the book has left the journal — without the folded set,
        // re-importing yesterday's list after a quit would apply it a second time on top of a
        // book that already carries it.
        var known = Journal.Select(t => t.Fingerprint)
            .Concat(Folded)
            .ToHashSet(StringComparer.Ordinal);

        // **The same fill wears a different fingerprint when it is imported under a different
        // date.** The dialog stamps with its day picker, and a list pasted "for yesterday" on the
        // wrong morning becomes a fresh-looking row whose Day part no longer matches anything —
        // yet the fill itself was folded long ago, and applying it again moves the book twice.
        // Folded fingerprints therefore keep a **dayless** shadow (time, code, side, price, size),
        // and an import matching it counts as a duplicate. A genuinely identical fill on another
        // day — same stock, size, price and clock to the second — is rare past believing in a
        // per-day order list, and losing one costs far less than doubling a position.
        var foldedFills = Folded
            .Select(fp => string.Join("|", fp.Split('|').Skip(1)))
            .ToHashSet(StringComparer.Ordinal);

        var applied = 0;
        var duplicates = 0;
        var fresh = new List<string>();

        foreach (var trade in trades.OrderBy(t => t.Day, StringComparer.Ordinal)
                                    .ThenBy(t => t.MinuteOfDay)
                                    .ThenBy(t => t.Time, StringComparer.Ordinal))
        {
            var fill = string.Join(
                "|",
                trade.Time,
                trade.Code.ToLowerInvariant(),
                trade.Side.ToString(),
                trade.Price.ToString("0.####", CultureInfo.InvariantCulture),
                trade.Shares.ToString("0.####", CultureInfo.InvariantCulture));

            if (known.Contains(trade.Fingerprint) || foldedFills.Contains(fill))
            {
                duplicates++;
                continue;
            }

            known.Add(trade.Fingerprint);

            Journal.Add(trade);
            fresh.Add(trade.Fingerprint);
            applied++;
        }

        Prune();
        Save();

        return new ImportResult(applied, duplicates, Oversold(fresh));
    }

    /// <summary>
    /// Folds a day's fills into the book — the morning's position becomes the evening's — and
    /// **takes them out of the journal** so the curve does not walk the same fills a second time.
    ///
    /// **Why this exists.** Importing only ever adds to the journal (see <see cref="Apply"/>): the
    /// book is the opening and is meant to be copied in by hand each morning. But a reader who
    /// imports the day's orders after the close expects the holdings they look at to be the day's
    /// closing, not its open — "I sold 2,900, why does it still say 3,000?" This is the button for
    /// that: it rolls the book forward so 管理持仓 shows what was actually held at the end of the
    /// day, and removes the day's fills from the journal so the curve for that day draws flat at the
    /// new book instead of doubling the move.
    ///
    /// **Idempotent.** Trades still in the journal are applied once and removed; trades already
    /// folded are skipped; trades never imported are applied straight to the book. Folding the same
    /// day twice, or folding a list that was folded before, moves nothing twice.
    /// </summary>
    public static int FoldIntoBook(IReadOnlyList<PortfolioTrade> trades) => Fold(trades);

    /// <summary>
    /// Folds every fill of a day that is still in the journal into the book. Used when the orders
    /// were imported earlier and the reader now wants to roll the book forward without re-pasting
    /// the list.
    /// </summary>
    public static int FoldDay(string day) =>
        Fold([.. Journal.Where(t => string.Equals(t.Day, day, StringComparison.Ordinal))]);

    /// <summary>Whether a day still has fills in the journal that have not been folded into the book.</summary>
    public static bool HasUnfoldedTrades(string day)
    {
        EnsureLoaded();

        return Journal.Any(t =>
            string.Equals(t.Day, day, StringComparison.Ordinal) && !Folded.Contains(t.Fingerprint));
    }

    /// <summary>
    /// Folds every fill from a session **before today** into the book, so the stored book becomes
    /// the latest closing and the next import replays on top of it.
    ///
    /// Today's fills stay where they are: the page is still drawing today, and its replay needs
    /// them in the journal. They roll the next time the app starts. Called when the app quits and
    /// again when it loads — the same fold twice moves nothing twice, and a quit that never got
    /// the chance (task manager, crash, power) is caught by the load.
    /// </summary>
    public static void RollForward()
    {
        var cutoff = DateTime.Today.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

        Fold([.. Journal.Where(t => string.CompareOrdinal(t.Day, cutoff) < 0)]);
    }

    /// <summary>
    /// Starts the book again from a snapshot: the holdings become the snapshot's rows, the journal
    /// becomes the fills dated on or after its day, and nothing is left marked folded.
    ///
    /// **Why the journal is rebuilt and the marks cleared.** The book and the archive are two
    /// halves of one story — the snapshot is the morning it starts, and every fill since is what
    /// turns it into today's position. Swapping in a new snapshot while keeping a journal that was
    /// folded *against the old one* leaves the app holding a position built from a book that no
    /// longer exists: the curve redraws from the new start while the list still shows the old
    /// finish. That is exactly the disagreement a reader reports as "导入以后界面没变" (实测：换掉
    /// 起点后曲线重算，持仓列表原地不动).
    ///
    /// Fills stamped before the snapshot's day are dropped: the snapshot already carries their
    /// effect, and replaying them would count the same shares twice.
    /// </summary>
    /// <param name="day">The morning — or, for a closing book, the evening — the figures belong to.</param>
    /// <param name="rows">What was held.</param>
    /// <param name="archive">Every fill the ledger has archived, all books together.</param>
    /// <param name="closeBook">
    /// Whether the rows are a <em>closing</em> figure — a book photographed after that day's last
    /// print rather than before its first. The 港股通 book is one: its baseline is rewritten off the
    /// curve's final frame, so the day's own fills are already inside the rows, and keeping them in
    /// the journal would apply them a second time at the next roll (buy 100, rebase on the close,
    /// roll tomorrow → 200). Strictly-after rather than on-or-after, then — with a morning book the
    /// day's fills still lie ahead of it and belong in the journal, which is the default.
    /// </param>
    public static void Rebase(
        DateOnly day,
        IReadOnlyList<Holding> rows,
        IReadOnlyList<PortfolioTrade> archive,
        bool closeBook = false)
    {
        EnsureLoaded();

        var stamp = day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

        Holdings.Clear();

        foreach (var row in rows.Where(r => r.Shares > 0))
        {
            Holdings.Add(row);
        }

        var kept = archive
            .Where(t => string.CompareOrdinal(t.Day, stamp) > (closeBook ? 0 : -1))
            .GroupBy(t => t.Fingerprint, StringComparer.Ordinal)
            .Select(group => group.First())
            .OrderBy(t => t.Day, StringComparer.Ordinal)
            .ThenBy(t => t.MinuteOfDay)
            .ThenBy(t => t.Time, StringComparer.Ordinal)
            .ToList();

        Journal.Clear();
        Journal.AddRange(kept);

        // A fingerprint left here would keep the next roll from applying a fill this book has not
        // seen yet — the marks describe the old book, and that book is gone.
        Folded.Clear();

        Save();
    }

    /// <summary>
    /// Records that the book was just corrected **by hand**, which outranks every fill still
    /// waiting to roll: the numbers the reader typed are the position as it really is, and letting
    /// tomorrow's roll apply the same fills on top of them would move the book twice.
    ///
    /// The fills stay in the journal — the day's replay still needs them — and are marked folded,
    /// which is exactly what keeps the roll from applying them again.
    /// </summary>
    public static void MarkManualEdit()
    {
        EnsureLoaded();

        var unfolded = Journal
            .Select(t => t.Fingerprint)
            .Where(fp => !Folded.Contains(fp))
            .ToList();

        if (unfolded.Count == 0)
        {
            return;
        }

        foreach (var fingerprint in unfolded)
        {
            Folded.Add(fingerprint);
        }

        Save();
    }

    /// <summary>
    /// The most recent day that still has fills to fold, or null when there is nothing left.
    ///
    /// **The dialog needs this because its date is the day the page is drawing, not the day the
    /// fills are on.** Filled in after the close, the page is already on the new session, so a
    /// date-picker-only gate would leave the fold button greyed out on the one day the reader has
    /// anything to fold — they see a dead button and report that the import "did not save".
    /// </summary>
    public static string? LatestUnfoldedDay()
    {
        EnsureLoaded();

        var days = Journal
            .Where(t => !Folded.Contains(t.Fingerprint))
            .Select(t => t.Day)
            .ToList();

        return days.Count == 0 ? null : days.Max(StringComparer.Ordinal);
    }

    /// <summary>
    /// Applies the given trades to the book at their diluted cost, marks them folded, and removes
    /// them from the journal so the curve cannot replay them. Shared by <see cref="FoldIntoBook"/>
    /// and <see cref="FoldDay"/>.
    /// </summary>
    private static int Fold(IReadOnlyList<PortfolioTrade> requested)
    {
        EnsureLoaded();

        var fresh = requested.Where(t => !Folded.Contains(t.Fingerprint)).ToList();

        if (fresh.Count == 0)
        {
            return 0;
        }

        var fees = FeeTable.Default;

        foreach (var group in fresh.GroupBy(t => t.Code, StringComparer.OrdinalIgnoreCase))
        {
            var code = group.Key;
            var held = Find(code);
            var shares = held?.Shares ?? 0;
            var cost = held?.Cost ?? 0;
            var name = held?.Name ?? group.First().Name;

            foreach (var trade in group
                         .OrderBy(t => t.Day, StringComparer.Ordinal)
                         .ThenBy(t => t.MinuteOfDay)
                         .ThenBy(t => t.Time, StringComparer.Ordinal))
            {
                var gross = trade.Shares * trade.Price;
                var fee = trade.Side == TradeSide.Buy
                    ? fees.OnBuy(trade.Code, gross)
                    : fees.OnSell(trade.Code, gross);

                cost = IntradayPnl.Diluted(cost, shares, trade.Shares, trade, fee);
                shares = trade.Side == TradeSide.Buy
                    ? shares + trade.Shares
                    : Math.Max(0, shares - trade.Shares);
            }

            if (shares <= 0)
            {
                Remove(code);
            }
            else
            {
                Put(new Holding(code, name, shares, cost));
            }
        }

        foreach (var trade in fresh)
        {
            Folded.Add(trade.Fingerprint);
        }

        var fingerprints = fresh.Select(t => t.Fingerprint).ToHashSet(StringComparer.Ordinal);

        Journal.RemoveAll(t => fingerprints.Contains(t.Fingerprint));

        Prune();
        Save();

        return fresh.Count;
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

    /// <summary>
    /// Fingerprints of the fills the book **already carries** — folded by the roll, or superseded
    /// by a hand edit — as a copy the loader can hold while it works off the UI thread.
    ///
    /// <para>
    /// The loader needs them because folding and hand-editing leave two different things in the
    /// same journal. A fill that has been folded has left the journal and can only be re-imported
    /// (see <see cref="Apply"/>); but a fill superseded by a hand edit **stays** in the journal, so
    /// the day's replay can still draw its marker and count it. Its money is already inside the
    /// book's shares and cost, though, so applying it again would move the position twice — once
    /// by hand, once by replay. Told which fills are settled, the loader draws them and leaves the
    /// arithmetic alone.
    /// </para>
    /// </summary>
    public static IReadOnlySet<string> Settled
    {
        get
        {
            EnsureLoaded();

            return new HashSet<string>(Folded, StringComparer.Ordinal);
        }
    }

    /// <summary>Drops journal entries older than the window, so the file cannot grow forever.</summary>
    private static void Prune()
    {
        var cutoff = DateTime.Today.AddDays(-JournalDays).ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

        Journal.RemoveAll(t => string.CompareOrdinal(t.Day, cutoff) < 0);

        // A folded fingerprint carries its day first, so the same cutoff prunes it.
        Folded.RemoveWhere(fp => fp.Length >= 10 && string.CompareOrdinal(fp.Substring(0, 10), cutoff) < 0);
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
    private sealed record Book(List<Holding> Holdings, List<PortfolioTrade> Trades, List<string> Folded);
}
