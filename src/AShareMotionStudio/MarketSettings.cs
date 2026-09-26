using AShareMotionStudio.Market;
using Windows.Storage;

namespace AShareMotionStudio;

/// <summary>
/// Which market the app is pointed at, and how long a change to it takes to show.
///
/// Stored the same way as the language and the theme, because it is the same kind of
/// choice: one a person makes once and then expects to hold.
///
/// A change needs a restart, and for the same reason the language does. The pages
/// build their lists — rosters, index presets, the picker's pool — as they are
/// constructed, and the shell keeps them alive after that so the work in them is not
/// thrown away by a visit to another page. Rebuilding one list on the spot would
/// leave the others stale, which reads as a setting that half-took.
/// </summary>
public static class MarketSettings
{
    private const string SettingKey = "Market";

    public static MarketId Current
    {
        get => Read();
        set => ApplicationData.Current.LocalSettings.Values[SettingKey] = (int)value;
    }

    private static MarketId Read()
    {
        var stored = ApplicationData.Current.LocalSettings.Values[SettingKey];

        // An out-of-range value is one the app no longer has a market for — a build
        // that dropped one, or a hand-edited setting. Falling back to A-shares is
        // both the default and the only market every page can serve.
        return stored is int number && System.Enum.IsDefined(typeof(MarketId), number)
            ? (MarketId)number
            : MarketId.AShare;
    }
}
