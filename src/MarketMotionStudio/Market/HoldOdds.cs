using System.Globalization;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// Runs every entry a holder could have made inside a range, not the range's own two ends.
///
/// The fourteenth page says what a holding earned across one range, which is one entry and one
/// exit and says nothing about the ones between them. A board drawn on the range's ends answers
/// "was this decade good"; the question a holder actually faces — walk in on a month picked at
/// random, hold for the same length of time, how often does that work — is a different question
/// with a different answer. Over the last ten years the Nasdaq fund was ahead on all eighty-four
/// of its three-year entries and the Hong Kong fund on forty per cent of them, while the two
/// boards that already exist rank those same two holdings by ten years of total return.
///
/// **Adjusted, for the reason the asset race gives and this board inherits.** An entry's outcome is
/// what its holder had at the end of it, and a fund's distributions never appear in its price: a
/// money-market fund's price is flat while its holder earned a fifth, and a fund that split its
/// units shows a cliff no holder went over. Unadjusted, an entry that paid out for three years and
/// went nowhere would be counted as one that lost.
///
/// **Every entry, overlapping.** A three-year hold sampled once a month across ten years is
/// eighty-four entries, not eight, and they share months — which is the point. A single entry is
/// luck; eighty-four of them are a rate. Nothing here thins them out to make them independent:
/// dropping from eighty-four samples to three would leave a rate with three observations in it,
/// and a rate built on three observations is the luck this board exists to measure.
///
/// **An entry counts from the month it finishes.** A hold bought in the last month of the range has
/// not finished, and counting it as a loss would put every row on a downward slope across the last
/// three years for no reason but the calendar. So the board's first month is the first one on which
/// anything could have finished, and its axis is a set of finishing months.
///
/// **A rate built on too few entries is not on the board.** One entry is 0% or 100%, and either
/// number would sit at an end of a ranking it has not earned, so a row joins on the month its sixth
/// entry finishes. The rate still moves after that — that is the picture — but it moves because the
/// record changed and not because one month flipped.
///
/// **Each holding's entries start on its own first month.** A fund launched in 2019 has no 2016
/// entry to have won or lost, and the rule the index race established holds here: absence is not an
/// outcome.
/// </summary>
public static class HoldOdds
{
    private const string Period = "month";

    /// <summary>More months than the endpoint answers in one request: it returns what it has.</summary>
    private const int MonthsWanted = 430;

    /// <summary>Less than a year of months and a rate is a single throw.</summary>
    public const int FewestMonths = 12;

    /// <summary>
    /// How many finished entries before a rate is drawn at all.
    ///
    /// Six, because below that the number is one or two observations wearing a per cent sign, and a
    /// ranking sorted on it would reorder on every frame for a reason the picture cannot show. The
    /// cost is a row missing from the first few months of the board; the alternative is a board
    /// whose opening seconds are noise.
    /// </summary>
    public const int FewestWindows = 6;

    /// <summary>
    /// The share of each holding's finished entries that gained, month by month.
    ///
    /// Drawn on the race renderer's return metric, which is the one whose labels end in %: a rate
    /// is a percentage of entries and reads as one. The amount slot carries the same numbers —
    /// the series type is built for two measures off one fetch, and an array of zeros would be a
    /// claim that a second measure exists.
    /// </summary>
    public static async Task<SectorRaceSeries> LoadAsync(
        TencentKline kline,
        IReadOnlyList<RaceEntry> assets,
        DateOnly start, DateOnly end,
        int holdMonths,
        IProgress<string> progress, CancellationToken cancellation)
    {
        var perAsset = new List<Dictionary<DateOnly, double>>(assets.Count);

        for (var i = 0; i < assets.Count; i++)
        {
            var entry = assets[i];

            progress.Report(string.Format(
                CultureInfo.InvariantCulture, "{0} ({1}/{2})",
                InstrumentNames.Display(entry.Code, entry.Name), i + 1, assets.Count));

            // Adjusted, not raw: see the class note. The one call whose name cannot be mistaken
            // for the other one — a raw series here counts a distribution as a loss.
            var bars = await kline.TotalReturnBarsAsync(
                entry.Code, Period, start, end, MonthsWanted, cancellation);

            var byMonth = new Dictionary<DateOnly, double>();

            // The last bar in a month is the month: a request that straddles one returns it
            // twice, and the earlier of the two is the partial.
            foreach (var bar in bars)
            {
                if (bar.Close <= 0 || bar.Date < start || bar.Date > end)
                {
                    continue;
                }

                byMonth[MonthEnd(bar.Date.Year, bar.Date.Month)] = bar.Close;
            }

            perAsset.Add(byMonth);
        }

        var all = perAsset
            .SelectMany(d => d.Keys)
            .Distinct()
            .OrderBy(d => d)
            .ToArray();

        var hold = Math.Max(1, holdMonths);

        // The board's months are the ones an entry can have finished on, so the first `hold`
        // months of the range are off it: nothing bought inside them has come to an end yet, and
        // a board that opened on them would open empty.
        var days = all.Length - hold;

        if (days < FewestMonths)
        {
            throw new InvalidOperationException(Strings.Get("HoldOddsTooFew"));
        }

        var dates = all.Skip(hold).ToArray();

        var rates = new List<double[]>();
        var starts = new List<int>();

        for (var k = 0; k < assets.Count; k++)
        {
            var row = new double[days];

            // Its own first quoted month inside the range. Everything before it is absence, not
            // an outcome: a fund launched in 2019 has no entry in 2016 to have won or lost.
            var own = -1;

            for (var i = 0; i < all.Length && own < 0; i++)
            {
                if (perAsset[k].ContainsKey(all[i]))
                {
                    own = i;
                }
            }

            if (own < 0)
            {
                rates.Add(row);
                starts.Add(int.MaxValue);
                continue;
            }

            // A month the source skips holds the month before it — the hole is the source's, not
            // the holding's, and an entry priced at zero would read as a total loss.
            var closes = new double[all.Length];
            var last = perAsset[k][all[own]];

            for (var i = own; i < all.Length; i++)
            {
                if (perAsset[k].TryGetValue(all[i], out var close) && close > 0)
                {
                    last = close;
                }

                closes[i] = last;
            }

            // Every entry, filed against the month it finishes and nowhere else: counting it on
            // the month it was bought would let the board report an outcome that had not happened
            // yet, which on this board is the difference between a rate and a forecast.
            var winsAt = new int[all.Length];
            var endsAt = new int[all.Length];

            for (var i = own; i + hold < all.Length; i++)
            {
                if (closes[i] <= 0)
                {
                    continue;
                }

                endsAt[i + hold]++;

                if (closes[i + hold] > closes[i])
                {
                    winsAt[i + hold]++;
                }
            }

            var begun = -1;
            var running = 0;
            var won = 0;

            for (var t = 0; t < days; t++)
            {
                running += endsAt[hold + t];
                won += winsAt[hold + t];

                // Not drawn until there are enough entries for the number to mean a rate. Until
                // then the row is off the board rather than at 0% on it — see the class note.
                if (running >= FewestWindows)
                {
                    row[t] = (won * 100.0) / running;

                    if (begun < 0)
                    {
                        begun = t;
                    }
                }
            }

            rates.Add(row);
            starts.Add(begun < 0 ? int.MaxValue : begun);
        }

        if (starts.All(s => s == int.MaxValue))
        {
            throw new InvalidOperationException(Strings.Get("HoldOddsTooFew"));
        }

        // Named in the interface's own language: the source answers these codes with Chinese
        // names, and `INST*` is how a frame drawn on an English interface still reads "CSI 300
        // ETF".
        var entries = assets
            .Select(e => new RaceEntry(e.Code, InstrumentNames.Display(e.Code, e.Name)))
            .ToArray();

        return new SectorRaceSeries(entries, dates, rates, rates, starts);
    }

    /// <summary>
    /// The closing standings, best rate first, over the rows that were ever on the board.
    ///
    /// Not <see cref="SectorRaceSeries.Standings"/>, which includes every racer: a holding with no
    /// finished entry inside the range holds a final rate of zero, and a status line that called it
    /// the bottom of the list would be naming a holding the picture never showed.
    /// </summary>
    public static (int Index, double Value)[] Standings(SectorRaceSeries series)
    {
        var last = series.Days - 1;
        var outList = new List<(int Index, double Value)>();

        for (var k = 0; k < series.Racers; k++)
        {
            if (series.StartOf(k) <= last)
            {
                outList.Add((k, series.Returns[k][last]));
            }
        }

        return [.. outList.OrderByDescending(s => s.Value).ThenBy(s => s.Index)];
    }

    /// <summary>How many of the group's holdings ever finished an entry inside the range.</summary>
    public static int Quoted(SectorRaceSeries series) =>
        Enumerable.Range(0, series.Racers).Count(k => series.StartOf(k) < int.MaxValue);

    private static DateOnly MonthEnd(int year, int month) =>
        new(year, month, DateTime.DaysInMonth(year, month));
}
