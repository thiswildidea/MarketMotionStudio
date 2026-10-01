using System.Globalization;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;

namespace MarketMotionStudio.Market;

/// <summary>The stock a smartbox suggestion or a snapshot resolved to.</summary>
/// <param name="Code">The full code, venue prefix included — `sh600000`, `hk00700`, `usAAPL`.</param>
/// <param name="Name">The instrument's name.</param>
public sealed record StockRef(string Code, string Name);

/// <summary>
/// Everything about a stock that is not its bars: turning what a person types into a code,
/// suggesting names while they type, and the real-time snapshot the turnover rate is derived from.
///
/// The two endpoints here are the awkward ones in the whole data layer. Both are served as GBK
/// while their headers claim UTF-8 — the browser tool had to load them through `script` tags with
/// `charset="GBK"` because of it — and neither is JSON. Going through <see cref="HttpClient"/>
/// instead of script injection means the same job is one explicit
/// <see cref="Encoding.RegisterProvider"/> call and a bytes-to-string decode.
/// </summary>
public sealed class StockDirectory(HttpClient http)
{
    private const string SearchEndpoint = "https://smartbox.gtimg.cn/s3/";

    private const string SnapshotEndpoint = "https://qt.gtimg.cn/q=";

    /// <summary>The prefix sets that decide a six-digit code's venue, in the order they are tested.</summary>
    private static readonly string[] Shanghai = ["600", "601", "603", "605", "688", "689", "900"];

    private static readonly string[] Shenzhen = ["000", "001", "002", "003", "300", "301", "200"];

    /// <summary>
    /// Turns what a person typed into a code the quote endpoints accept.
    ///
    /// A code alone is ambiguous — `600519` carries its venue nowhere a reader can see it — so the
    /// prefix decides, and the two fallback single digits catch a code the prefix lists do not
    /// cover. Five digits are Hong Kong, letters are a US ticker, and anything already carrying a
    /// venue is put back into the shape the quote endpoints read.
    /// </summary>
    /// <returns>The normalised code, or null if the input is no code at all — which is how a name or
    /// a pinyin string ends up here, and the caller's cue to search instead.</returns>
    public static string? Normalize(string raw)
    {
        var s = raw.Trim().ToLowerInvariant().Replace(" ", string.Empty);

        // A US code is the only one that runs past eight characters: it carries an
        // exchange suffix — `usAAPL.OQ` is nine — and the other venues have nothing
        // to put there. Left at eight, a suffixed code fell through to the ticker
        // branch below and came back wearing a second `us`.
        var longest = s.StartsWith("us") ? 12 : 8;

        if (s.Length >= 4 && s.Length <= longest &&
            (s.StartsWith("sh") || s.StartsWith("sz") || s.StartsWith("bj") ||
             s.StartsWith("hk") || s.StartsWith("us")))
        {
            // Put through Canonize rather than returned as it stands, because `s` has
            // been lowered and that is only right for three of the four venues. A US
            // ticker is read in upper case — `usAAPL.OQ` — and the chart endpoint
            // answers `usaapl` with no bars rather than with an error, so a code that
            // came out of the search box and went back in through 取数 read as an
            // instrument with no history at all. The other three prefixes lowercase
            // to themselves, so this changes nothing for them.
            return Markets.Canonize(s);
        }

        if (s.Length == 6 && s.All(char.IsAsciiDigit))
        {
            var prefix = s[..3];

            if (Shanghai.Contains(prefix))
            {
                return "sh" + s;
            }

            if (Shenzhen.Contains(prefix))
            {
                return "sz" + s;
            }

            return s[0] switch
            {
                '6' => "sh" + s,
                '0' or '3' => "sz" + s,
                _ => "bj" + s,   // 4/8/9 lead the Beijing exchange
            };
        }

        if (s.Length == 5 && s.All(char.IsAsciiDigit))
        {
            return "hk" + s;
        }

        // A US ticker with its exchange suffix, `aapl.oq`, is longer than a bare
        // one, so the bound leaves room for the four characters a suffix adds.
        if (s.Length is >= 1 and <= 10 && s.All(c => char.IsAsciiLetterLower(c) || c == '.'))
        {
            return Markets.Canonize("us" + s);
        }

        return null;
    }

    /// <summary>
    /// Suggestions while a person types: a code, a Chinese name or pinyin all resolve to the same
    /// instrument list.
    /// </summary>
    /// <param name="market">The market to keep. The endpoint answers every venue at once, so
    /// without it a Hong Kong search lists Shanghai listings and the page lets a person pick an
    /// instrument the market in force cannot draw.</param>
    /// <remarks>
    /// The response is GBK text shaped like `v_hint="sh~600000~浦发银行~pufa~GP-A^…"`, so it is
    /// decoded by hand rather than parsed as anything structured. The query itself must be sent
    /// UTF-8-escaped — a GBK-escaped Chinese query returns nothing, which is the one combination
    /// that fails silently.
    /// </remarks>
    public async Task<IReadOnlyList<StockRef>> SearchAsync(
        string query, MarketProfile market, CancellationToken cancellation)
    {
        var uri = $"{SearchEndpoint}?v=2&t=all&q={Uri.EscapeDataString(query)}";

        using var response = await http.GetAsync(uri, cancellation);
        response.EnsureSuccessStatusCode();

        var raw = await DecodeGbk(response, cancellation);

        // Strip the assignment down to the value between the quotes.
        var open = raw.IndexOf('"');
        var close = raw.LastIndexOf('"');

        if (open < 0 || close <= open)
        {
            return [];
        }

        var body = Unescape(raw[(open + 1)..close]);

        if (body.Length == 0 || body == "N")
        {
            return [];
        }

        var found = new List<StockRef>();

        foreach (var item in body.Split('^'))
        {
            var fields = item.Split('~');

            if (fields.Length < 5 || fields[1].Length == 0 || fields[2].Length == 0)
            {
                continue;
            }

            // The search answers in lower case — `usaapl.oq` — and the chart endpoint
            // will only read `usAAPL.OQ`, so the code is put into that shape here,
            // where it is first known. See Markets.Canonize.
            var code = Markets.Canonize(fields[0] + fields[1]);

            if (!market.Accepts(code))
            {
                continue;
            }

            found.Add(new StockRef(code, fields[2]));
        }

        return found;
    }

    /// <summary>
    /// The one number the minute-data endpoint does not carry: free-float market value, from which
    /// the share count — and so a turnover rate — is derived.
    /// </summary>
    public async Task<StockSnapshot> SnapshotAsync(string code, CancellationToken cancellation)
    {
        using var response = await http.GetAsync(SnapshotEndpoint + code, cancellation);
        response.EnsureSuccessStatusCode();

        var raw = await DecodeGbk(response, cancellation);

        var open = raw.IndexOf('"');
        var close = raw.LastIndexOf('"');

        if (open < 0 || close <= open)
        {
            throw new InvalidOperationException($"{code}: the snapshot carried no data.");
        }

        var fields = raw[(open + 1)..close].Split('~');

        if (fields.Length < 46)
        {
            throw new InvalidOperationException($"{code}: the snapshot was too short to read.");
        }

        var iso = CultureInfo.InvariantCulture;

        double Parse(string s) =>
            double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? v : 0;

        return new StockSnapshot(
            fields[1],
            Parse(fields[3]),
            Parse(fields[38]),
            Parse(fields[44]));
    }

    /// <summary>
    /// Reads a body as GBK. Both endpoints here claim `charset=utf-8` in their headers while
    /// shipping GBK bytes, so the header is ignored on purpose and the real encoding is applied.
    /// </summary>
    private static async Task<string> DecodeGbk(HttpResponseMessage response, CancellationToken cancellation)
    {
        var bytes = await response.Content.ReadAsByteArrayAsync(cancellation);

        return Gbk.GetString(bytes);
    }

    private static readonly Encoding Gbk = GetGbk();

    private static Encoding GetGbk()
    {
        Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
        return Encoding.GetEncoding(936);
    }

    /// <summary>
    /// Turns `\uXXXX` sequences back into characters.
    ///
    /// The suggestion endpoint does not ship GBK bytes at all — it ships an ASCII body in which
    /// every non-ASCII character is a JavaScript escape, so 超图软件 arrives as the twelve literal
    /// characters `\u8d85\u56fe\u8f6f\u4ef6` and a GBK decode passes them through untouched. The
    /// browser tool never saw this because the `script` tag handed the string to the JS engine,
    /// which unescapes it as a side effect of parsing. Applied after the decode, where it is
    /// harmless on a body that carries none.
    /// </summary>
    internal static string Unescape(string body) =>
        UnicodeEscape.Replace(body, static m => ((char)Convert.ToInt32(m.Groups[1].Value, 16)).ToString());

    private static readonly Regex UnicodeEscape =
        new(@"\\u([0-9a-fA-F]{4})", RegexOptions.Compiled);
}

/// <summary>The parts of the real-time snapshot this app reads.</summary>
/// <param name="Name">The instrument's name.</param>
/// <param name="Price">The last price, whatever the session state.</param>
/// <param name="TurnoverToday">Today's turnover rate so far, in per cent.</param>
/// <param name="FloatCapYi">Free-float market value in 亿元.</param>
public sealed record StockSnapshot(string Name, double Price, double TurnoverToday, double FloatCapYi);
