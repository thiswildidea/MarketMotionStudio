using System.Text.Json;
using Windows.Storage;

namespace MarketMotionStudio.Market;

/// <summary>
/// The coins a search brought in, kept between runs.
///
/// Kept apart from the twelve in <see cref="CryptoAsset.All"/>, which are a hand-picked list with
/// a span that was measured: what is here was found by name and is only as good as the source that
/// answered. A machine that never searches has none, and the pickers then show exactly the twelve
/// they always did.
///
/// Its own store rather than a page's <c>StudioPreferences</c>, and that is the point: three
/// crypto pages share these coins, and a key prefixed per page would keep three copies of the same
/// list, each remembering only what its own page searched.
///
/// A remembered coin is the code, the name to show it by and the two source ids — the same four
/// fields a listed one carries — so a coin added here is fetched, named and drawn exactly like the
/// twelve. It is written as it is added rather than debounced: adding a coin is a decision made
/// once, not a slider being dragged.
/// </summary>
public static class CryptoRegistry
{
    private const string Key = "crypto.found";

    private static bool _loaded;

    /// <summary>Reads the remembered coins, once per process.</summary>
    public static void EnsureLoaded()
    {
        if (_loaded)
        {
            return;
        }

        _loaded = true;

        try
        {
            if (ApplicationData.Current.LocalSettings.Values[Key] is not string body || body.Length == 0)
            {
                return;
            }

            if (JsonSerializer.Deserialize<List<Dictionary<string, string>>>(body) is not { } stored)
            {
                return;
            }

            foreach (var coin in stored)
            {
                var code = coin.GetValueOrDefault("code");
                var yahoo = coin.GetValueOrDefault("yahoo");

                if (string.IsNullOrWhiteSpace(code) || string.IsNullOrWhiteSpace(yahoo))
                {
                    continue;
                }

                CryptoAsset.Register(new CryptoAsset(
                    code,
                    coin.GetValueOrDefault("name") is { Length: > 0 } name ? name : code,
                    yahoo,
                    coin.GetValueOrDefault("gecko") ?? string.Empty));
            }
        }
        catch (Exception)
        {
            // A store that will not parse costs the remembered coins, not the page. The twelve are
            // still listed, and the next search writes the list again.
        }
    }

    /// <summary>Adds a coin and writes the list down.</summary>
    public static void Remember(CryptoAsset asset)
    {
        CryptoAsset.Register(asset);
        Save();
    }

    private static void Save()
    {
        try
        {
            var stored = new List<Dictionary<string, string>>();

            foreach (var coin in CryptoAsset.Extra)
            {
                stored.Add(new Dictionary<string, string>
                {
                    ["code"] = coin.Code,
                    ["name"] = coin.Name,
                    ["yahoo"] = coin.Yahoo,
                    ["gecko"] = coin.Gecko,
                });
            }

            ApplicationData.Current.LocalSettings.Values[Key] = JsonSerializer.Serialize(stored);
        }
        catch (Exception)
        {
            // Local settings can refuse — a quota, a corrupt container. Remembering a searched coin
            // is a convenience, and losing it is not worth failing the page over.
        }
    }
}
