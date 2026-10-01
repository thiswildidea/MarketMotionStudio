using System.Globalization;
using System.Text;
using System.Text.Json;
using MarketMotionStudio.Localization;

namespace MarketMotionStudio.Market;

/// <summary>
/// The market's largest listings **as they stand today**, asked of a ranking endpoint rather than
/// remembered in a list.
///
/// The page used to carry a hand-written field of sixty-two names, and a hand-written field is
/// wrong the moment somebody lists. It was: 长鑫科技 listed, became the largest company on the
/// mainland at 3.7 trillion, and the board did not know it existed — a defect no amount of care in
/// writing the list could have prevented, because the list was written before the company listed.
///
/// **Why not the quote source this app already uses.** Tencent serves quotes and bars and no
/// ranking at all — three candidate paths were tried (`stock.gtimg.cn`'s `rank`, the
/// `cgi-bin/rank/pt` and `cgi-bin/rank/hs` boards, and `appstock/app/rankList`), and all three
/// answer with an empty list or a 400. Sina's `Market_Center.getHQNodeData` answers with the whole
/// market sorted by market value, in pages of a hundred, **and in the same code shape the quote
/// source uses** — `sh688825`, not a vendor-specific identifier — so nothing has to be translated.
///
/// **A ranking is asked for once per fetch**, which is the whole of this app's traffic to it: the
/// endpoint is a ranking service and hammering it is how a ranking service stops answering.
/// </summary>
public static class RankingSource
{
    private const string Endpoint =
        "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData";

    /// <summary>Entries per request. A hundred is what the endpoint returns for any larger ask.</summary>
    private const int PerPage = 100;

    /// <summary>
    /// Pages to ask for. Two hundred listings reaches down to about 800 亿 — far below any board
    /// that shows fifteen rows, and far enough that a company which has fallen out of the top
    /// fifteen since the range began is still in the field.
    /// </summary>
    private const int Pages = 2;

    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(30) };

    /// <summary>
    /// The mainland's listings, largest first.
    ///
    /// Throws rather than returning a short list: a caller that gets three names back cannot tell
    /// a quiet market from a broken request, and the page has a hand-checked field to fall back on.
    /// </summary>
    public static async Task<RaceEntry[]> LargestAsync(
        IProgress<string> progress, CancellationToken cancellation)
    {
        var found = new List<RaceEntry>();
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        for (var page = 1; page <= Pages; page++)
        {
            progress.Report(Strings.Format("MarketCapRanking", found.Count));

            var url = string.Format(
                CultureInfo.InvariantCulture,
                "{0}?page={1}&num={2}&sort=mktcap&asc=0&node=hs_a&_s_r_a=page",
                Endpoint, page, PerPage);

            using var response = await Http.GetAsync(url, cancellation);
            response.EnsureSuccessStatusCode();

            // GBK, like the quote source: the header claims utf-8 and the bytes are not.
            var bytes = await response.Content.ReadAsByteArrayAsync(cancellation);
            var body = Gbk.GetString(bytes);

            using var json = JsonDocument.Parse(body);

            if (json.RootElement.ValueKind != JsonValueKind.Array)
            {
                throw new InvalidOperationException(
                    $"{Endpoint}: expected an array, got {json.RootElement.ValueKind}.");
            }

            foreach (var row in json.RootElement.EnumerateArray())
            {
                if (!row.TryGetProperty("symbol", out var symbol) ||
                    !row.TryGetProperty("name", out var name))
                {
                    continue;
                }

                var code = symbol.GetString();
                var display = name.GetString();

                if (string.IsNullOrWhiteSpace(code) || string.IsNullOrWhiteSpace(display))
                {
                    continue;
                }

                // The node is `hs_a`, which is the mainland's A-shares, but the ranking is a
                // market-wide one and the profile's own filter is the thing that decides what this
                // app will quote — the same check the search box and the pages apply.
                if (!Markets.Of(MarketId.AShare).Accepts(code))
                {
                    continue;
                }

                if (seen.Add(code))
                {
                    found.Add(new RaceEntry(code, Clean(display)));
                }
            }
        }

        if (found.Count < 20)
        {
            throw new InvalidOperationException(
                $"The ranking endpoint returned {found.Count} usable listings.");
        }

        return [.. found];
    }

    /// <summary>
    /// A name with its ex-rights flag taken off.
    ///
    /// On the ex-dividend day a quote source prefixes the name — `XD中国移`, `XR…`, `DR…` — and the
    /// prefix is gone the next morning. Carried into a frame it names a company that does not
    /// exist, and the frame is watched for weeks after the morning it was exported. Only those
    /// three: a leading `N` and `C` mean new and recently listed, which are facts about the company
    /// rather than about the day.
    /// </summary>
    private static string Clean(string name)
    {
        foreach (var flag in (string[])["XD", "XR", "DR"])
        {
            if (name.StartsWith(flag, StringComparison.Ordinal) && name.Length > flag.Length)
            {
                return name[flag.Length..].Trim();
            }
        }

        return name.Trim();
    }

    private static readonly Encoding Gbk = GetGbk();

    private static Encoding GetGbk()
    {
        Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
        return Encoding.GetEncoding(936);
    }
}
