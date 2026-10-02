using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// One trading day and how far the instrument moved on it, in per cent.
///
/// The sign is the point of the page: a board of the largest moves is a board of *moves*, and
/// −7.7% is as large a move as +8.1%. The day is carried by its date, which is both the row's
/// name on the frame and the only thing that identifies it — a day has no ticker.
/// </summary>
public sealed record ExtremeDay(DateOnly Date, double ChangePercent);

/// <summary>The board's shape: how many days the frame draws and how many it considers.</summary>
public static class ExtremeDayBoard
{
    /// <summary>How many rows the frame draws.</summary>
    public const int Board = 15;

    /// <summary>
    /// How many candidate days the field carries.
    ///
    /// More than the board draws, so that the membership can change: a day that arrives late
    /// and is larger than the fifteenth takes its place and pushes someone out. With the field
    /// the same size as the board the frame would only ever fill up, never reorder.
    /// </summary>
    public const int Field = 24;

    /// <summary>
    /// The fewest trading days a range must have. Below this the board is mostly the range's
    /// own first weeks, and the "largest moves" are the moves of a quiet month.
    /// </summary>
    public const int FewestDays = 60;
}

/// <summary>
/// Loads one instrument's daily closes and turns them into a board of its largest single-day
/// moves.
///
/// **Every row is a day, not an instrument, and that inverts the usual series.** A race gives
/// each racer a value that changes day by day; here a racer is one day and its value never
/// changes — it is the move that day made. What moves is *membership*: a day's value is zero
/// until that day arrives, so the board fills up as the years pass, and a day larger than the
/// fifteenth pushes whoever was fifteenth off the bottom.
///
/// The zero before a day arrives is why the renderer is asked to leave empty rows out
/// (`HideEmptyRows`): ranked by magnitude, twenty-four candidates of which only five have
/// happened still fill a fifteen-row frame, and ten of those rows would read 0.00%.
///
/// **The change is the change in the adjusted close**, which for an index is the index and for
/// a single stock is its total return — a stock that goes ex-dividend does not show a fall that
/// nobody suffered, which an unadjusted series would report as the largest move of the decade.
/// Indices are what this page is asked about, and the distinction is the one the manual states.
/// </summary>
public static class ExtremeDaySeries
{
    /// <summary>
    /// The days of the largest moves in <paramref name="start"/>…<paramref name="end"/>, as a
    /// race whose rows are those days.
    /// </summary>
    public static async Task<SectorRaceSeries> LoadAsync(
        TencentKline kline,
        MarketProfile market,
        RaceEntry instrument,
        DateOnly start, DateOnly end,
        IProgress<string> progress, CancellationToken cancellation)
    {
        // The walk, not one request: a range of years is more than one page of bars, and the
        // walk is the piece that knows how to ask for the next one — see HistoryWalk.
        var closes = await HistoryWalk.ClosesAsync(
            kline, instrument.Code, InstrumentNames.Display(instrument.Code, instrument.Name),
            start, end, progress, cancellation);

        if (closes.Count < ExtremeDayBoard.FewestDays)
        {
            throw new InvalidOperationException(Strings.Get("ExtremeDaysTooFew"));
        }

        var dates = closes.Keys.ToArray();
        var moves = new double[dates.Length];

        for (var i = 1; i < dates.Length; i++)
        {
            var before = closes[dates[i - 1]];

            // A non-positive close is not a price. The adjusted series does not produce one,
            // but a board whose largest move is an artefact of a bad row would be believed.
            if (before > 0)
            {
                moves[i] = ((closes[dates[i]] / before) - 1) * 100;
            }
        }

        // The field: the largest moves either way, then in the order they happened. The order
        // matters twice — it sets which row gets which colour ramp on the way in, and it is the
        // order the board fills in, so the frame tells the story in the order it happened
        // rather than in order of size.
        var chosen = Enumerable.Range(1, dates.Length - 1)
            .Where(i => moves[i] != 0)
            .OrderByDescending(i => Math.Abs(moves[i]))
            .ThenBy(i => dates[i])
            .Take(ExtremeDayBoard.Field)
            .OrderBy(i => i)
            .ToArray();

        if (chosen.Length < 2)
        {
            throw new InvalidOperationException(Strings.Get("ExtremeDaysTooFew"));
        }

        var entries = new List<RaceEntry>();
        var returns = new List<double[]>();

        foreach (var i in chosen)
        {
            // A date is its own name in every language, which is the one thing on this board
            // that needs no translating: `INST*` keys name instruments, and a day is not one.
            var label = dates[i].ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

            entries.Add(new RaceEntry(label, label));

            var row = new double[dates.Length];

            for (var d = i; d < dates.Length; d++)
            {
                row[d] = moves[i];
            }

            returns.Add(row);
        }

        // The amount slot carries the same numbers: the board is drawn on the return metric and
        // nothing reads the other one, but the series type is built for two measures off one
        // fetch and a second array of zeros would be a claim that a turnover exists here.
        return new SectorRaceSeries(entries, dates, returns, returns);
    }

    /// <summary>
    /// The standings by size, biggest move first — what the page reports after a fetch.
    ///
    /// Not `SectorRaceSeries.Standings`, which orders by the signed value: on a board of moves
    /// the largest fall is first by size and last by sign, and a status line that called the
    /// biggest drop the bottom of the list would be read as a bug.
    /// </summary>
    public static (int Index, double Value)[] ByMagnitude(SectorRaceSeries series) =>
        [.. Enumerable.Range(0, series.Racers)
            .Select(k => (Index: k, Value: series.Returns[k][^1]))
            .OrderByDescending(s => Math.Abs(s.Value))
            .ThenBy(s => s.Index)];
}
