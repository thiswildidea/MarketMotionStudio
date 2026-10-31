using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Windows.Storage;

namespace MarketMotionStudio.Market;

/// <summary>
/// The book's own starting point: what was held **on one morning**, named by the day it belongs to.
///
/// <para>
/// Everything an arbitrary range answers is measured against this one row of figures. Ask "what
/// did I make since June" and the answer is today's worth less June's worth less the money put in
/// between — and June's worth is only knowable if the shares held then are known. They are not
/// anywhere else in this app: <see cref="Portfolio.Holdings"/> is the **current** morning's
/// position and is rewritten every time the book rolls, so it cannot be asked what it used to be.
/// </para>
///
/// <para>
/// This is the missing anchor. With a snapshot and every trade since it, the position on any
/// later day is arithmetic: start from these rows, apply the fills that happened before that day,
/// and nothing else is needed.
/// </para>
/// </summary>
/// <param name="Day">The morning the figures were true on.</param>
/// <param name="Rows">What was held, with the diluted cost beside it, in each venue's currency.</param>
public sealed record HoldingSnapshot(DateOnly Day, IReadOnlyList<Holding> Rows)
{
    /// <summary>Positions worth keeping: a row at zero shares was not held.</summary>
    public IReadOnlyList<Holding> Kept => [.. Rows.Where(r => r.Shares > 0)];

    /// <summary>Whether anything is actually held, and a range therefore has a start to speak of.</summary>
    public bool Empty => Kept.Count == 0;

    /// <summary>How many positions the snapshot carries.</summary>
    public int Count => Kept.Count;
}

/// <summary>What one import of trades did.</summary>
/// <param name="Applied">Rows that were new and are now on the archive.</param>
/// <param name="Duplicates">Rows the archive already carried, ignored.</param>
/// <param name="Before">How many trades were archived before this import.</param>
/// <param name="After">How many are archived now. Smaller than <paramref name="Before"/> only in
/// an overwrite, which is the one mode allowed to lose rows.</param>
public sealed record ArchiveResult(int Applied, int Duplicates, int Before, int After);

/// <summary>
/// The book's history: **the snapshot it starts from, and every trade since.**
///
/// <para>
/// **This is a second store next to <see cref="Portfolio"/>, deliberately and not for tidiness.**
/// The old book is a working set: its journal keeps a hundred and twenty days and is emptied as
/// fills are folded into the current holdings, because a page that draws *today* needs nothing
/// older and a file that grew for ever was worse than one that did not. Every one of those three
/// properties is what makes today's page honest, and every one of them makes "the last twelve
/// months" unanswerable — so much so that answering it from the old store would be inventing:
/// the fills before day minus one hundred and twenty are simply gone, and the account would show
/// a position that never sold as though it never bought.
/// </para>
///
/// <para>
/// So the two answers live apart. The old book still draws the day and still rolls; this one
/// keeps **every** fill it is given, forever, and never folds anything. A fill being folded into
/// today's holdings is not a reason to forget it happened — that forgetfulness is exactly the
/// bug this store exists to prevent. Two files, two questions, and neither can drift into the
/// other's answer.
/// </para>
///
/// <para>
/// **What makes two rows the same trade** is decided once, here, by
/// <see cref="KeyOf"/>: the day, the clock, the name, the side, the price and the size. The name
/// is what a reader recognises their trade by and what a broker's export always carries; leaving
/// any of the others out would silently drop a genuine second fill — the same stock, in the same
/// minute, at a different price is two fills and not a duplicate — while putting the venue's own
/// code in instead would split one trade in two whenever a re-export spells it differently.
/// </para>
/// </summary>
public static class Ledger
{
    private const string BaselineFile = "ledger-baseline.json";

    /// <summary>
    /// The mainland book's own snapshot, kept apart from the other one because it belongs to a
    /// different question. See <see cref="PortfolioScope"/>.
    /// </summary>
    private const string PlainBaselineFile = "ledger-baseline-ashare.json";

    private const string TradeFile = "ledger-trades.json";

    private static bool _loaded;

    private static readonly List<PortfolioTrade> ArchiveRows = [];

    /// <summary>
    /// The starting point of the book **with** the Hong Kong positions in it, or null when the
    /// reader has not set one yet.
    ///
    /// The two baselines are separate files rather than one with a flag inside, for the reason the
    /// whole store is: a book is a statement about one morning, and one that changes its shape
    /// when a switch moves is a book nobody can check. Each is written whole and read whole.
    /// </summary>
    public static HoldingSnapshot? Baseline { get; private set; }

    /// <summary>
    /// The starting point of the **mainland** book alone — no `hk` rows — or null when it has
    /// never been taken.
    ///
    /// Held separately rather than derived on demand, because it is not always the other one minus
    /// its Hong Kong rows: a reader may have entered their mainland positions on a different
    /// morning, at costs copied from a different screen, and asking them to be consistent with a
    /// snapshot they did not type is asking for a number they cannot check. When it has never been
    /// taken it *is* derived from the other — see <see cref="PlainOrDerived"/> — which is the
    /// upgrade path and not the definition.
    /// </summary>
    public static HoldingSnapshot? PlainBaseline { get; private set; }

    /// <summary>
    /// The starting point of one of the two books. The mainland one falls back to a snapshot
    /// derived from the other, so that a book entered before there were two still answers.
    /// </summary>
    public static HoldingSnapshot? BaselineOf(PortfolioScope scope) =>
        scope is PortfolioScope.AShare ? PlainOrDerived() : Baseline;

    /// <summary>The day one of the two books starts on, or the earliest date there is.</summary>
    public static DateOnly BaselineDayOf(PortfolioScope scope)
    {
        EnsureLoaded();

        return BaselineOf(scope)?.Day ?? DateOnly.MinValue;
    }

    /// <summary>Whether one of the two books has a snapshot with positions in it.</summary>
    public static bool HasBaselineOf(PortfolioScope scope)
    {
        EnsureLoaded();

        return BaselineOf(scope) is { Empty: false };
    }

    /// <summary>
    /// The mainland snapshot, or one derived from the other book by dropping its Hong Kong rows.
    ///
    /// Derived only while it has never been set, so that upgrading from one book to two costs the
    /// reader nothing: the mainland curve starts from the same morning they already entered, minus
    /// the positions this scope does not carry.
    /// </summary>
    private static HoldingSnapshot? PlainOrDerived()
    {
        if (PlainBaseline is { } plain)
        {
            return plain;
        }

        if (Baseline is not { Empty: false } withKong)
        {
            return null;
        }

        return new HoldingSnapshot(
            withKong.Day,
            [.. withKong.Rows.Where(r => !r.IsHongKong)]);
    }

    /// <summary>
    /// Reads both files once.
    ///
    /// Missing files are the ordinary first run, not an error: nothing has been archived yet and
    /// the snapshot will be taken when the reader asks for their first range. A file that cannot
    /// be read is treated as missing rather than fatal — history you can re-import costs you one
    /// range; a page that refuses to open costs you the app.
    /// </summary>
    public static void EnsureLoaded()
    {
        if (_loaded)
        {
            return;
        }

        _loaded = true;

        Baseline = Read<StoredBaseline>(BaselineFile)?.ToSnapshot();
        PlainBaseline = Read<StoredBaseline>(PlainBaselineFile)?.ToSnapshot();

        if (Read<StoredArchive>(TradeFile) is { } stored)
        {
            ArchiveRows.AddRange(stored.Trades ?? []);
        }

        Sort();

        // **The mainland snapshot is written down the first time it is derived.** Two books means
        // two files: derived once, it is a snapshot of its own from then on, so a reader who later
        // corrects the Hong Kong one has not said anything about the mainland one — and the
        // mainland curve does not quietly change shape because the other book moved.
        if (PlainBaseline is null && PlainOrDerived() is { } derived)
        {
            PlainBaseline = derived;
            SaveBaseline();
        }
    }

    /// <summary>
    /// Fills both stores from the old book the first time this is ever read.
    ///
    /// Someone upgrading has a book nobody wants to retype and a journal holding the last hundred
    /// and twenty days of fills. Taking those as the starting point costs nothing and *strokes
    /// nothing*: the snapshot is today's holdings at today's date and the fills still in the
    /// journal are copied across, so the first range drawn after upgrading is the one the reader
    /// already expects. What cannot be recovered are fills older than that — folded away and
    /// pruned long ago — and a book like that starts its history where the surviving records do,
    /// which is the honest answer rather than a guess.
    ///
    /// Idempotent: a second call finds a baseline already set and leaves both alone.
    /// </summary>
    public static void SeedFromCurrentBook()
    {
        EnsureLoaded();

        // **The first run is the one that copies the journal across.** A second baseline seeded
        // later — the mainland one, from a book that already has its Hong Kong counterpart — must
        // not archive the journal again: those fills are already on the archive, and adding them
        // beside themselves would double every position the next range is rebuilt from.
        var firstTime = Baseline is null;

        if (!firstTime && PlainBaseline is not null)
        {
            return;
        }

        Portfolio.EnsureLoaded();

        var rows = Portfolio.Holdings.Where(h => h.Shares > 0).ToList();

        // A snapshot taken on a Saturday is Friday's book: the market has not moved since, and
        // naming the Saturday would leave every span clipped to a day that has no trading on it
        // at all — "近一周" answering with zero points is a failure the reader cannot explain
        // away. The weekday falls back to the Friday; a holiday simply draws a shorter span,
        // which is the honest answer either way.
        var today = DateOnly.FromDateTime(DateTime.Today);
        var day = today.DayOfWeek switch
        {
            DayOfWeek.Saturday => today.AddDays(-1),
            DayOfWeek.Sunday => today.AddDays(-2),
            _ => today,
        };

        // Nothing to anchor to is not an error — it is a reader who has not entered a book yet,
        // and they will be asked for a snapshot the first time they want a range.
        if (rows.Count == 0)
        {
            return;
        }

        // Both baselines taken from the same morning: the Hong Kong one carries every row the
        // book holds, and the mainland one the same rows without the `hk` ones. Taken together
        // rather than one derived at read time, so that a reader who later corrects one of them
        // by hand does not find the other silently moving with it.
        Baseline ??= new HoldingSnapshot(day, rows);
        PlainBaseline ??= new HoldingSnapshot(day, [.. rows.Where(r => !r.IsHongKong)]);

        if (firstTime)
        {
            ArchiveRows.AddRange(Portfolio.Trades);
            Sort();
        }

        SaveBaseline();
        SaveArchive();
    }

    /// <summary>The day the history starts on, or the earliest date there is when none is set.</summary>
    public static DateOnly BaselineDay
    {
        get
        {
            EnsureLoaded();

            return Baseline?.Day ?? DateOnly.MinValue;
        }
    }

    /// <summary>Whether a snapshot has been taken, which every range-drawing question hinges on.</summary>
    public static bool HasBaseline
    {
        get
        {
            EnsureLoaded();

            return Baseline is { Empty: false };
        }
    }

    /// <summary>Every archived trade, in the order they happened.</summary>
    public static IReadOnlyList<PortfolioTrade> Archive
    {
        get
        {
            EnsureLoaded();

            return [.. ArchiveRows];
        }
    }

    /// <summary>How many fills the archive carries.</summary>
    public static int Count
    {
        get
        {
            EnsureLoaded();

            return ArchiveRows.Count;
        }
    }

    /// <summary>
    /// What makes two rows one trade — see the note on this class.
    ///
    /// The name is trimmed because an export pads its columns, and lower-cased because two exports
    /// of one fill disagreeing about capitalisation is not two trades either. The numbers are
    /// formatted rather than compared raw so that <c>200</c> and <c>200.00</c> are one row.
    /// </summary>
    public static string KeyOf(PortfolioTrade trade) => string.Join(
        "|",
        trade.Day.Trim(),
        trade.Time.Trim(),
        trade.Name.Trim().ToLowerInvariant(),
        trade.Side.ToString(),
        trade.Price.ToString("0.####", CultureInfo.InvariantCulture),
        trade.Shares.ToString("0.####", CultureInfo.InvariantCulture));

    /// <summary>
    /// Puts trades on the archive.
    ///
    /// <para>
    /// **Appending is the default** because that is what an import is: one file's worth of fills,
    /// usually today's, usually a list the broker has been accumulating. Anything already there is
    /// counted as a duplicate and left alone, so exporting the same week twice — the ordinary way
    /// these files are kept — cannot double a position.
    /// </para>
    ///
    /// <para>
    /// **Overwriting replaces everything**, and it is offered rather than assumed because it is the
    /// one destructive answer here: it is the mode for "this file is my whole history, the archive
    /// has drifted from it, make the archive be this". It is also the only way to remove a row that
    /// was imported in error, which is why the count comes back smaller sometimes and why the page
    /// reports both numbers rather than only one.
    /// </para>
    /// </summary>
    /// <param name="trades">What was imported.</param>
    /// <param name="overwrite">Replace the archive with these rows rather than add to them.</param>
    /// <summary>
    /// How many of these fills the archive already holds.
    ///
    /// **Said before the import, not after.** Re-importing yesterday's list is the ordinary way a
    /// reader gets here — a broker's export is cumulative more often than not — and an import that
    /// reports "0 applied, 46 duplicates ignored" only after the fact leaves them guessing whether
    /// the list was wrong or the record was. Counted by the same fingerprint `Import` dedupes by, so
    /// the number shown and the number skipped cannot disagree.
    /// </summary>
    public static int AlreadyFiled(IEnumerable<PortfolioTrade> trades)
    {
        EnsureLoaded();

        var filed = ArchiveRows.Select(KeyOf).ToHashSet(StringComparer.Ordinal);

        return trades.Count(trade => filed.Contains(KeyOf(trade)));
    }

    public static ArchiveResult Import(IReadOnlyList<PortfolioTrade> trades, bool overwrite)    {
        EnsureLoaded();

        var before = ArchiveRows.Count;

        if (overwrite)
        {
            ArchiveRows.Clear();

            var known = new HashSet<string>(StringComparer.Ordinal);
            var duplicates = 0;

            // Deduplicated even here: a file carrying the same fill twice — a workbook whose
            // footer rows were included, say — would otherwise be archived twice, and a replace
            // is meant to leave the archive *equal* to what was handed over, not a multiple of it.
            foreach (var trade in trades)
            {
                if (!known.Add(KeyOf(trade)))
                {
                    duplicates++;
                    continue;
                }

                ArchiveRows.Add(trade);
            }

            Sort();
            SaveArchive();

            return new ArchiveResult(ArchiveRows.Count, duplicates, before, ArchiveRows.Count);
        }

        var seen = ArchiveRows.Select(KeyOf).ToHashSet(StringComparer.Ordinal);
        var applied = 0;
        var skipped = 0;

        foreach (var trade in trades)
        {
            if (!seen.Add(KeyOf(trade)))
            {
                skipped++;
                continue;
            }

            ArchiveRows.Add(trade);
            applied++;
        }

        Sort();
        SaveArchive();

        return new ArchiveResult(applied, skipped, before, ArchiveRows.Count);
    }

    /// <summary>
    /// Throws the archive away.
    ///
    /// Offered for the reader who imported the wrong file wholesale and wants none of it — the
    /// one case where "remove everything" is the answer being asked for. The snapshot is kept: it
    /// is a separate statement about a separate morning and deleting it here would be a surprise.
    /// </summary>
    public static void ClearArchive()
    {
        EnsureLoaded();

        ArchiveRows.Clear();
        SaveArchive();
    }

    /// <summary>
    /// Writes the snapshot, replacing whatever was there.
    ///
    /// Whole-day replacement rather than row editing, for the reason the holdings dialog found
    /// first: these rows are one morning's picture, and a book with June's count beside July's
    /// cost is a position nobody ever held.
    /// </summary>
    /// <param name="scope">Which of the two books the snapshot is being taken of.</param>
    /// <param name="day">The morning the figures belong to.</param>
    /// <param name="rows">What was held. Rows at zero shares are dropped rather than stored.</param>
    public static void SetBaseline(PortfolioScope scope, DateOnly day, IEnumerable<Holding> rows)
    {
        EnsureLoaded();

        var kept = rows.Where(r => r.Shares > 0).ToList();

        // **Each book is written to its own file and the other is left alone.** Taking the
        // mainland snapshot is not a statement about the Hong Kong positions, and writing both
        // from one dialog would be: the two are entered off two different screens, and a reader
        // who corrects one has not said anything about the other.
        if (scope is PortfolioScope.AShare)
        {
            PlainBaseline = new HoldingSnapshot(day, kept);
        }
        else
        {
            Baseline = new HoldingSnapshot(day, kept);
        }

        SaveBaseline();
    }

    /// <summary>
    /// Rewrites the 港股通 book's baseline with a session's closing figures — the position as the
    /// last sample of the curve holds it, shares and diluted costs both.
    ///
    /// <para>
    /// **The 港股通 book's starting point moves; the mainland one does not.** The A股 baseline is
    /// one morning the reader filed once and the spans are measured from it, so an animation —
    /// which ends on a *different* day's close — must never touch it. The 港股通 book answers about
    /// today only, its yesterday is unrecoverable from any source the app reads, and the one
    /// honest starting point for its next session is where this one ended. So when the curve
    /// reaches its final frame the page hands the session here, and the book the 管理持仓 dialog
    /// opens on next time is the close the reader just watched.
    /// </para>
    ///
    /// <para>
    /// **Identical rows are not written.** Auto-refresh adopts a fresh session every thirty
    /// seconds and each one ends on the same close; rewriting the file for the same numbers would
    /// be disk churn with a timestamp that moves for no reason.
    /// </para>
    /// </summary>
    /// <returns>Whether the file changed — the callers do not react, but the tests read it.</returns>
    public static bool SyncKongClose(PortfolioSession session)
    {
        EnsureLoaded();

        if (session.Moments.Count == 0 ||
            !DateOnly.TryParseExact(session.Day, "yyyy-MM-dd", CultureInfo.InvariantCulture,
                DateTimeStyles.None, out var day))
        {
            return false;
        }

        var last = session.Moments[^1];

        // Names live on the holdings and on the day's fills; a position opened mid-session is in
        // the second list only, and a code with neither spells itself.
        var names = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        foreach (var holding in session.Holdings)
        {
            names[holding.Code] = holding.Name;
        }

        foreach (var trade in session.Trades)
        {
            names.TryAdd(trade.Code, trade.Name);
        }

        var rows = new List<Holding>();

        foreach (var (code, shares) in last.Shares)
        {
            if (shares <= 0)
            {
                continue;
            }

            last.Costs.TryGetValue(code, out var cost);

            rows.Add(new Holding(
                code,
                names.TryGetValue(code, out var name) ? name : code,
                shares,
                cost));
        }

        if (rows.Count == 0)
        {
            return false;
        }

        if (Baseline is { } current && current.Day == day &&
            current.Rows.Count == rows.Count &&
            current.Rows.All(row => rows.FirstOrDefault(n =>
                string.Equals(n.Code, row.Code, StringComparison.OrdinalIgnoreCase)) is
                { } twin && twin.Shares == row.Shares &&
                Math.Abs(twin.Cost - row.Cost) < 1e-9))
        {
            return false;
        }

        Baseline = new HoldingSnapshot(day, rows);
        SaveBaseline();

        return true;
    }

    /// <summary>
    /// When the archived fills start and finish, or null with nothing archived.
    ///
    /// The earliest fill matters more than the snapshot day for one thing only: a history with no
    /// trades is a flat holding, and a page can say so rather than drawing it.
    /// </summary>
    public static (DateOnly First, DateOnly Last)? TradedSpan()
    {
        EnsureLoaded();

        if (ArchiveRows.Count == 0)
        {
            return null;
        }

        var days = ArchiveRows.Select(t => ParseDay(t.Day))
            .Where(d => d != DateOnly.MinValue)
            .ToList();

        return days.Count == 0 ? null : (days.Min(), days.Max());
    }

    /// <summary>Reads `yyyy-MM-dd` as a date; the earliest date there is when it is not one.</summary>
    private static DateOnly ParseDay(string text) =>
        DateOnly.TryParseExact(text.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture,
            DateTimeStyles.None, out var day)
            ? day
            : DateOnly.MinValue;

    /// <summary>
    /// The day column of a snapshot file, in whatever spelling the reader's editor saved it in.
    ///
    /// <para>
    /// **The app writes `2026-10-30`, but the reader types what their broker screen shows.** A
    /// hand-made file saying `2026/10/29` is not malformed — it is a Windows short date, and
    /// refusing every row of it over four characters of punctuation reads as "导入没反应" with a
    /// rejection notice the dialog whispers at the bottom (实测：斜杠日期整份被拒，列表原地不动).
    /// The exporter keeps its strict form; the importer is the one that has to be polite.
    /// </para>
    /// </summary>
    private static bool TryReadDay(string text, out DateOnly day) =>
        DateOnly.TryParseExact(
            text.Trim(),
            ["yyyy-MM-dd", "yyyy/M/d", "yyyy-M-d", "yyyy.M.d", "yyyy年M月d日"],
            CultureInfo.InvariantCulture,
            DateTimeStyles.None,
            out day);

    // ---- files ------------------------------------------------------------------------

    private static readonly JsonSerializerOptions Format = new()
    {
        WriteIndented = true,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    private static string Path_(string file) =>
        Path.Combine(ApplicationData.Current.LocalFolder.Path, file);

    private static T? Read<T>(string file) where T : class
    {
        try
        {
            var path = Path_(file);

            return File.Exists(path) ? JsonSerializer.Deserialize<T>(File.ReadAllText(path)) : null;
        }
        catch (Exception)
        {
            return null;
        }
    }

    private static void Write(string file, object body)
    {
        try
        {
            File.WriteAllText(Path_(file), JsonSerializer.Serialize(body, Format));
        }
        catch (Exception)
        {
            // Remembering the history is worth a lot and worth failing a page over nothing.
        }
    }

    private static void SaveBaseline()
    {
        if (Baseline is { } snapshot)
        {
            Write(BaselineFile, new StoredBaseline(
                snapshot.Day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
                [.. snapshot.Rows]));
        }

        if (PlainBaseline is { } plain)
        {
            Write(PlainBaselineFile, new StoredBaseline(
                plain.Day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
                [.. plain.Rows]));
        }
    }

    private static void SaveArchive() => Write(TradeFile, new StoredArchive([.. ArchiveRows]));

    /// <summary>
    /// Clock order, always.
    ///
    /// The arithmetic that rebuilds a position walks these in sequence and has no way to detect
    /// being handed them out of order — a sell read before its buy clamps against holdings that
    /// are not there yet and quietly under-reports every position it touches. Sorting on the way
    /// in is cheaper than defending against every caller, and the same reason the old journal is
    /// kept sorted.
    /// </summary>
    private static void Sort()
    {
        var sorted = ArchiveRows
            .OrderBy(t => t.Day, StringComparer.Ordinal)
            .ThenBy(t => t.MinuteOfDay)
            .ThenBy(t => t.Time, StringComparer.Ordinal)
            .ThenBy(t => t.Code, StringComparer.OrdinalIgnoreCase)
            .ToList();

        ArchiveRows.Clear();
        ArchiveRows.AddRange(sorted);
    }

    private sealed record StoredBaseline(string Day, List<Holding> Rows)
    {
        public HoldingSnapshot ToSnapshot() =>
            new(ParseDay(Day), Rows);
    }

    private sealed record StoredArchive(List<PortfolioTrade> Trades);

    // ---- sheets -----------------------------------------------------------------------

    private const string TradeHeader = "day,time,code,name,side,price,shares";

    private const string SnapshotHeader = "day,code,name,shares,cost";

    /// <summary>
    /// The whole archive as a file: `day,time,code,name,side,price,shares`.
    ///
    /// A fixed English header for the reason the holdings sheet has one: a file written on a
    /// machine running Japanese has to open correctly on one running German, and a header that
    /// followed the interface would make the same bytes mean different things in two places.
    /// The side is written as `buy` or `sell` for the same reason, and both English and Chinese
    /// spellings are accepted back, because a list a reader has been keeping in a spreadsheet by
    /// hand is the most likely thing to come back through this door.
    /// </summary>
    public static string TradesToCsv(IEnumerable<PortfolioTrade> rows)
    {
        var text = new StringBuilder(TradeHeader);

        foreach (var t in rows)
        {
            text.Append("\r\n")
                .Append(t.Day).Append(',')
                .Append(Quote(t.Time)).Append(',')
                .Append(Quote(t.Code)).Append(',')
                .Append(Quote(t.Name)).Append(',')
                .Append(t.Side == TradeSide.Buy ? "buy" : "sell").Append(',')
                .Append(t.Price.ToString("0.####", CultureInfo.InvariantCulture)).Append(',')
                .Append(t.Shares.ToString("0.####", CultureInfo.InvariantCulture));
        }

        return text.ToString();
    }

    /// <summary>The snapshot as a file: `day,code,name,shares,cost`.</summary>
    public static string SnapshotToCsv(HoldingSnapshot snapshot)
    {
        var stamp = snapshot.Day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        var text = new StringBuilder(SnapshotHeader);

        foreach (var row in snapshot.Kept)
        {
            text.Append("\r\n")
                .Append(stamp).Append(',')
                .Append(Quote(row.Code)).Append(',')
                .Append(Quote(row.Name)).Append(',')
                .Append(row.Shares.ToString("0.####", CultureInfo.InvariantCulture)).Append(',')
                .Append(row.Cost.ToString("0.####", CultureInfo.InvariantCulture));
        }

        return text.ToString();
    }

    private static string Quote(string value) =>
        value.Contains(',') || value.Contains('"')
            ? $"\"{value.Replace("\"", "\"\"")}\""
            : value;

    /// <summary>
    /// A snapshot read back from the file <see cref="SnapshotToCsv"/> wrote.
    ///
    /// <para>
    /// **The export has to be readable, or it is a backup that cannot be restored.** A snapshot is
    /// the one thing in this app a reader cannot recreate by pressing fetch: it is what they were
    /// holding on a morning they chose, and re-entering twenty rows by hand is how the fourth
    /// decimal differs. So the file the dialog exports is also a file it accepts.
    /// </para>
    ///
    /// <para>
    /// **Every row has to be readable, or none of it is applied.** A snapshot with two of its
    /// twenty positions missing is worse than no snapshot at all: the curves start from a book the
    /// reader does not hold, and nothing on the page can say which two rows fell out. The line
    /// numbers come back so the reader can fix the file, exactly as the sheet importer does.
    /// </para>
    ///
    /// <para>
    /// **One day for the whole file.** A snapshot is one morning; a file whose rows disagree about
    /// which one is not a snapshot, it is a pile of trades that belong in the archive. The earliest
    /// date is taken when the header carries none, and a file with several is refused.
    /// </para>
    /// </summary>
    /// <param name="text">The file's whole text.</param>
    public static SnapshotRead SnapshotFromCsv(string text)
    {
        var rows = new List<Holding>();
        var rejected = new List<int>();
        var days = new SortedSet<DateOnly>();
        var malformed = false;

        var lines = text.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n');

        for (var i = 0; i < lines.Length; i++)
        {
            var line = lines[i].Trim();

            if (line.Length == 0)
            {
                continue;
            }

            var fields = CsvLine.Split(line);

            // The header, which this app writes and therefore recognises: the dates below it are
            // the only thing that says whether the file is one.
            if (i == 0 && fields.Count >= 2 &&
                fields[0].TrimStart('\uFEFF').Equals("day", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (fields.Count < 5 ||
                !TryReadDay(fields[0], out var day) ||
                fields[1].Trim().Length == 0 ||
                !double.TryParse(fields[3], NumberStyles.Float, CultureInfo.InvariantCulture, out var shares) ||
                !double.TryParse(fields[4], NumberStyles.Float, CultureInfo.InvariantCulture, out var cost))
            {
                // The line number a reader can act on: one-based, counting every line of the file,
                // blanks included, so it matches what their editor shows.
                rejected.Add(i + 1);
                malformed = true;

                continue;
            }

            days.Add(day);
            rows.Add(new Holding(fields[1].Trim(), fields[2].Trim(), shares, cost));
        }

        if (rows.Count == 0)
        {
            return new SnapshotRead(null, 0, rejected);
        }

        // **Rows may disagree about the day; the snapshot takes the latest.** A hand-kept book
        // prices each line the last time that line moved — this very file carries nine rows of
        // 10-30 and 理想汽车 of 10-29, held throughout (实测：整份拒掉后列表仍是九行，
        // 「导入列表不完全显示」). An earlier date on a row is provenance, not a claim that the
        // shares did not exist later: the reader is looking at today's book, so the snapshot is
        // the latest morning the file mentions, and every row rides on it.
        return new SnapshotRead(
            malformed ? null : new HoldingSnapshot(days.Max, rows),
            rows.Count,
            rejected);
    }

}

/// <summary>What reading a snapshot file produced.</summary>
/// <param name="Snapshot">The snapshot, or null when the file cannot be applied as one.</param>
/// <param name="Rows">How many positions were read, whether or not they may be applied.</param>
/// <param name="Rejected">
/// One-based line numbers that could not be read. Non-empty means nothing is applied.
/// </param>
public sealed record SnapshotRead(HoldingSnapshot? Snapshot, int Rows, IReadOnlyList<int> Rejected)
{
    /// <summary>Whether the file can replace the snapshot as it stands.</summary>
    public bool Ready => Snapshot is not null && Rejected.Count == 0;
}
