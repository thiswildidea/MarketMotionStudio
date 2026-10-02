using System.Collections.ObjectModel;
using System.Linq;
using MarketMotionStudio.Market;

namespace MarketMotionStudio.Pages;

/// <summary>
/// One list of a person's own, shared by every roster board that offers it.
///
/// Four boards draw themselves across a roster the app ships — twelve world indices, eight
/// domestic funds — and a reader's own holdings are the roster none of them could carry. This is
/// that roster: typed in once, and every board that offers it reads the same list.
///
/// **Shared as one collection, not as four copies read at four different times.** Each page used
/// to read what it needed in its own constructor, which is how the favourites row works, and it
/// means a stock added here is absent from a page that was already built. The collection below is
/// the single one every picker binds to, so adding one there shows it here without either page
/// doing anything.
///
/// **Not the sector race's typed list.** That one is kept per market, because a race drawn from
/// the market in force cannot draw a code the market in force does not quote. These four boards
/// are the opposite — the market setting does not govern them — so this list is deliberately
/// cross-market, and a Shanghai share, a Hong Kong one and a New York one can sit on it together.
/// </summary>
public static class Watchlist
{
    /// <summary>
    /// How a roster menu names this list. Every board's menu carries it under this one tag, so a
    /// preference saved on one board is the same choice on another.
    /// </summary>
    public const string RosterKey = "Stocks";

    /// <summary>Fewer than three and a ranking of it is a comparison, not a board.</summary>
    public const int Fewest = 3;

    /// <summary>More than this and a vertical frame is a barcode. The sector race's own ceiling.</summary>
    public const int Most = 16;

    private const string Key = "Picks";

    private static readonly StudioPreferences Store = new("Watchlist.");

    private static bool _loaded;

    /// <summary>
    /// The picks, in the order they were added. Bound by every picker, so a change made on one
    /// board is on the others the moment it is made.
    /// </summary>
    public static ObservableCollection<RaceEntry> Picks { get; } = [];

    /// <summary>
    /// Reads the stored list once. Idempotent: the four boards each construct a picker, and the
    /// second one to do so must not put the stored picks back over the ones already bound.
    /// </summary>
    public static void EnsureLoaded()
    {
        if (_loaded)
        {
            return;
        }

        _loaded = true;

        var raw = Store.GetString(Key, string.Empty);

        if (raw.Length == 0)
        {
            return;
        }

        foreach (var entry in raw.Split(';'))
        {
            var parts = entry.Split('|');

            if (parts.Length == 2 && parts[0].Length > 0)
            {
                Picks.Add(new RaceEntry(parts[0], parts[1]));
            }
        }
    }

    /// <summary>
    /// Writes the list back. Called from whichever board changed it, and the change is on all of
    /// them — see the class note.
    /// </summary>
    public static void Save() =>
        Store.Save(Key, string.Join(";", Picks.Select(p => $"{p.Code}|{p.Name}")));

    /// <summary>
    /// Whether a code is on the list. Compared as the source spells it: the search endpoint
    /// answers in one case and the bars endpoint reads another, and a code added twice under two
    /// spellings would be fetched twice and race against itself.
    /// </summary>
    public static bool Has(string code) =>
        Picks.Any(p => string.Equals(p.Code, code, System.StringComparison.OrdinalIgnoreCase));

    /// <summary>
    /// Adds a pick, unless it is already there or the list is full.
    /// </summary>
    public static bool Add(string code, string name)
    {
        EnsureLoaded();

        if (Has(code) || Picks.Count >= Most)
        {
            return false;
        }

        Picks.Add(new RaceEntry(code, name.Length > 0 ? name : code.ToUpperInvariant()));
        Save();

        return true;
    }

    /// <summary>
    /// Drops a pick by code.
    /// </summary>
    public static void Remove(string code)
    {
        var at = Picks.ToList().FindIndex(p => string.Equals(p.Code, code, System.StringComparison.OrdinalIgnoreCase));

        if (at >= 0)
        {
            Picks.RemoveAt(at);
            Save();
        }
    }

    /// <summary>
    /// Corrects a pick's name to what the bars endpoint calls it. A name typed from a search
    /// result can carry spaces the vendor put there («五 粮 液») or be the one venue's spelling
    /// of a company the app names in the language it is running in.
    /// </summary>
    public static void Rename(string code, string name)
    {
        for (var i = 0; i < Picks.Count; i++)
        {
            if (!string.Equals(Picks[i].Code, code, System.StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (Picks[i].Name != name)
            {
                Picks[i] = new RaceEntry(Picks[i].Code, name);
                Save();
            }

            return;
        }
    }
}
