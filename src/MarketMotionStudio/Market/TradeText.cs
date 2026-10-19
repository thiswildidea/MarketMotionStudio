using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace MarketMotionStudio.Market;

/// <summary>One word the OCR engine read, with the box it sat in.</summary>
/// <param name="Text">The word as read.</param>
/// <param name="X">Left edge, in image pixels.</param>
/// <param name="Y">Top edge, in image pixels.</param>
/// <param name="Height">Its height, which is what tells two visual lines apart.</param>
public readonly record struct OcrWord(string Text, double X, double Y, double Height);

/// <summary>A trade read out of a broker's order list.</summary>
/// <param name="Side">Buy or sell.</param>
/// <param name="Code">The instrument, in the quote endpoint's spelling.</param>
/// <param name="Name">The name as the list spelled it, which may be Chinese.</param>
/// <param name="Price">The price ordered at — see the class note on why it is not the current price.</param>
/// <param name="Shares">How many shares filled.</param>
/// <param name="Time">`HH:mm:ss` from the list.</param>
public sealed record ParsedTrade(TradeSide Side, string Code, string Name, double Price, double Shares, string Time);

/// <summary>What a list parsed into, and what it could not read.</summary>
/// <param name="Trades">The trades, in the order they were listed.</param>
/// <param name="Skipped">One line per row that was not a trade, saying what it was.</param>
public sealed record TradeParse(IReadOnlyList<ParsedTrade> Trades, IReadOnlyList<string> Skipped)
{
    /// <summary>
    /// Rows the list itself says did not happen — 已撤, 废单, 未成交.
    ///
    /// Kept apart from <see cref="Skipped"/> because the two mean opposite things to a reader: a
    /// skipped row is one the parser could not read and must be fixed before anything is applied,
    /// while a cancelled row is one the broker has already told us about and which therefore must
    /// simply be left out. A cancelled order still carries a code, a price, a size and a clock —
    /// every part a trade has — so without this distinction it would be imported as a trade that
    /// never happened.
    /// </summary>
    public IReadOnlyList<string> Cancelled { get; init; } = [];
}

/// <summary>
/// Reads a broker's completed-order list, from a screenshot or from typed text.
///
/// **The two number columns are 委托价 and 现价, not 委托价 and 成交价.** That looks like a detail
/// and it is not: the sample day's 超图软件 buy reads "9.80 10.05 3000 3000", and 10.05 was the
/// day's close. Taking the second number as the fill would put the purchase at the closing price,
/// which is both wrong and flattering — the position would show no profit on a trade that made
/// 250 元. The first number is what was ordered, and the broker's own day P&L only reconciles
/// against that one.
///
/// <para>
/// The reader is deliberately tolerant about layout and strict about content. It never trusts a
/// column position — a screenshot cropped differently, at another scale, on another phone would
/// put every column somewhere else — and instead finds each row by its own parts: a side, a code,
/// a price, a size and a clock. Rows are delimited by the clock, because every filled order has
/// exactly one and nothing else on the screen does. What it cannot read it reports rather than
/// guessing, and the dialog shows both lists before anything is applied.
/// </para>
/// </summary>
public static class TradeText
{
    /// <summary>
    /// Fixes what OCR does to a table of numbers and Chinese names.
    ///
    /// The engine reads the decimal point as a middle dot («48 · 10») and puts a space between
    /// every pair of Chinese characters («中 望 软 件»); it reads the colon of a clock as a
    /// full-width one. None of that is wrong for OCR — it is wrong for a parser — so it is
    /// normalised once, in one place, before anything else looks at the text.
    /// </summary>
    public static string Normalize(string raw)
    {
        // **Every kind of line break becomes LF before anything else looks at the text.** Read from
        // a `TextBox`, a broker list pasted as LF arrives as CR — WinUI's own `TextBox.Text` keeps
        // a bare "\r" — and splitting that on "\n" finds one line where the reader meant three:
        // three filled orders collapse into one row, the parser reads the first one and reports
        // "识别到 1 笔，跳过 0 行". Measured on the machine, with two rows pasted. A paste from a
        // Windows app happens to carry "\r\n" and survives by luck, which is why it went unnoticed.
        var text = raw.Replace("\r\n", "\n").Replace('\r', '\n');

        text = text
            .Replace('：', ':').Replace('，', ',').Replace('％', '%')
            .Replace('．', '.').Replace('－', '-').Replace('　', ' ')
            .Replace('·', '.').Replace('•', '.').Replace('・', '.');

        // The spaces the engine puts around a punctuation mark it recognised separately.
        text = Regex.Replace(text, @"\s*([.:%])\s*", "$1");

        // A space between two Chinese characters is an artefact, never a word break.
        text = CjkGap.Replace(text, string.Empty);

        // Runs of spaces between columns become one, so a line reads the same however the
        // engine sliced it.
        text = Regex.Replace(text, @"[ \t]+", " ");

        return text;
    }

    private static readonly Regex CjkGap =
        new(@"(?<=[\u3400-\u9FFF])\s+(?=[\u3400-\u9FFF])", RegexOptions.Compiled);

    /// <summary>
    /// Turns OCR words into text lines, one per visual row, left to right.
    ///
    /// Rows are found by height rather than by a fixed tolerance: a phone screenshot at 2× has
    /// characters three times the height of the same screenshot at 1×, and a pixel threshold
    /// tuned on one would merge every row of the other. A word joins the current row when its top
    /// is within most of a character of where that row started.
    /// </summary>
    public static IReadOnlyList<string> Rows(IEnumerable<OcrWord> words)
    {
        var ordered = words
            .Where(w => w.Text.Trim().Length > 0)
            .OrderBy(w => w.Y)
            .ThenBy(w => w.X)
            .ToList();

        var rows = new List<List<OcrWord>>();
        var rowTop = double.NaN;
        var rowHeight = 0.0;

        foreach (var word in ordered)
        {
            var tolerance = Math.Max(6, rowHeight * 0.85);

            if (rows.Count == 0 || word.Y - rowTop > tolerance)
            {
                rows.Add([word]);
                rowTop = word.Y;
                rowHeight = word.Height;
                continue;
            }

            rows[^1].Add(word);
            rowHeight = Math.Max(rowHeight, word.Height);
        }

        // Rebuilt from the words rather than taken from the engine's own lines: those split a
        // table cell away from its neighbours, and a row is what the parser needs.
        return [.. rows.Select(r => string.Join(" ", r.OrderBy(w => w.X).Select(w => w.Text)))];
    }

    /// <summary>
    /// Reads a whole list. The text may be typed, pasted or produced by <see cref="Rows"/>; the
    /// parser does not care which.
    /// </summary>
    public static TradeParse Parse(string raw)
    {
        var lines = Normalize(raw)
            .Split('\n')
            .Select(l => l.Trim())
            .Where(l => l.Length > 0)
            .ToList();

        var blocks = Blocks(lines);
        var trades = new List<ParsedTrade>();
        var skipped = new List<string>();
        var cancelled = new List<string>();

        foreach (var block in blocks)
        {
            // **Only what the list says actually happened.** A broker's order table carries a
            // status column — 已成 / 全部成交 / 已撤 / 废单 — and a cancelled row carries every
            // other field a filled one does: the code, the price, the size and the clock. Read
            // without the status, a day of cancelled orders becomes a day of trades, and the book
            // then disagrees with the broker in a way nothing on the page can explain. Rows that
            // say nothing about a status are taken: the tab these screenshots come from is the
            // filled-order tab, and a hand-typed list has no room for a column it does not need.
            if (IsCancelled(block))
            {
                cancelled.Add(block);
                continue;
            }

            if (Read(block) is { } trade)
            {
                trades.Add(trade);
            }
            else if (block.Length > 0)
            {
                skipped.Add(block);
            }
        }

        return new TradeParse(trades, skipped) { Cancelled = cancelled };
    }

    /// <summary>How a broker's order table spells "this did not happen", in its several ways.</summary>
    private static bool IsCancelled(string block) =>
        CancelledWords.Any(word => block.Contains(word, StringComparison.Ordinal));

    private static readonly string[] CancelledWords =
    [
        "已撤", "部撤", "撤单", "废单",
        "未成交", "待成交", "已报", "待报", "申报中",
    ];

    /// <summary>
    /// Splits lines into rows, using the clock as the delimiter.
    ///
    /// A filled order carries exactly one timestamp and the table has no other column that looks
    /// like one, so "the lines up to and including the next clock" is a row however the engine
    /// chose to break the cells apart.
    /// </summary>
    private static List<string> Blocks(IReadOnlyList<string> lines)
    {
        var joined = string.Join(" ", lines);
        var clocks = Clock.Matches(joined);

        if (clocks.Count == 0)
        {
            // Nothing to delimit by: every line is its own row. This is the shape a hand-typed
            // list has, and one line per trade is how such a list is written.
            return [.. lines];
        }

        // **Cut at every clock wherever it falls, rather than at every line ending.** A visual row
        // is not a trade: OCR can read two filled orders as one row of pixels, and a pasted list
        // can arrive with its line breaks gone (see `Normalize`). The clock is the one thing
        // neither of those can take away from a row, so a block is "whatever sat between the last
        // clock and this one" instead of "whatever sat between the last newline and this one".
        var blocks = new List<string>();
        var start = 0;

        foreach (Match clock in clocks)
        {
            var end = clock.Index + clock.Length;
            var block = joined[start..end].Trim();

            if (block.Length > 0)
            {
                blocks.Add(block);
            }

            start = end;
        }

        // Anything after the last clock is a footer (the broker's own advertising line, the tab
        // bar). Kept as a block so it is reported as skipped rather than silently dropped.
        var tail = joined[start..].Trim();

        if (tail.Length > 0)
        {
            blocks.Add(tail);
        }

        return blocks;
    }

    private static readonly Regex Clock = new(@"\b\d{1,2}:\d{2}:\d{2}\b", RegexOptions.Compiled);

    /// <summary>Reads one row, or null when it is not a trade.</summary>
    private static ParsedTrade? Read(string block)
    {
        var side = Side(block);

        if (side is null)
        {
            return null;
        }

        var match = Code(block);

        if (match is null)
        {
            return null;
        }

        var clock = Clock.Match(block);

        if (!clock.Success)
        {
            return null;
        }

        // Everything that is not a number belonging to the trade is removed before the numbers
        // are read: the code's own digits would otherwise be the first number on the row, and
        // 688083 is not a price.
        var rest = block
            .Remove(match.Index, match.Length)
            .Replace(clock.Value, " ")
            .Replace("全部成交", " ");

        var values = Figures.Matches(rest).Select(m => m.Value).ToList();

        if (values.Count < 2)
        {
            return null;
        }

        var price = Number(values[0]);

        if (price <= 0)
        {
            return null;
        }

        // The size is a whole number after the price. **It appears twice** — 委托量 and 成交量 —
        // and that repetition is what tells it apart from an integer-valued price on a row that
        // also carries one ("9 9 3000 3000"): the size is the value that comes back.
        var rest2 = values.Skip(1).ToList();
        var shares = 0.0;

        for (var i = 0; i < rest2.Count; i++)
        {
            if (rest2[i].Contains('.') || Number(rest2[i]) < 1)
            {
                continue;
            }

            if (rest2.Skip(i + 1).Any(v => string.Equals(v, rest2[i], StringComparison.Ordinal)))
            {
                shares = Number(rest2[i]);
                break;
            }
        }

        if (shares <= 0)
        {
            shares = rest2.LastOrDefault(v => !v.Contains('.') && Number(v) >= 1) is { } last
                ? Number(last)
                : 0;
        }

        if (shares <= 0)
        {
            return null;
        }

        return new ParsedTrade(side.Value, match.Code, Name(block, match), price, shares, clock.Value);
    }

    private static readonly Regex Figures = new(@"\d+(?:\.\d+)?", RegexOptions.Compiled);

    /// <summary>A number, or zero rather than an exception: unreadable text is a row the reader
    /// is shown, not a crash halfway down someone's trade list.</summary>
    private static double Number(string value) =>
        double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var d) ? d : 0;

    /// <summary>Which way the row went, or null when it says nothing about a direction.</summary>
    private static TradeSide? Side(string block)
    {
        if (block.Contains("买入", StringComparison.Ordinal) || block.Contains("买 入", StringComparison.Ordinal))
        {
            return TradeSide.Buy;
        }

        if (block.Contains("卖出", StringComparison.Ordinal) || block.Contains("卖 出", StringComparison.Ordinal))
        {
            return TradeSide.Sell;
        }

        return null;
    }

    /// <summary>
    /// The code on the row, with the venue it was quoted on.
    ///
    /// **A bare six-digit number is not enough on its own.** 204001 — the one-day repo that sits
    /// at the top of a broker's filled-order list — is six digits and quotes on Shanghai, and
    /// treating it as a share would put a 366,000-share position in the book at 0.97. It is
    /// refused by the boards' own prefixes: Shanghai is 6xx, Shenzhen 0xx/3xx, Beijing 4xx/8xx,
    /// and 2xx is the repo's.
    /// </summary>
    private static CodeMatch? Code(string block)
    {
        var suffixed = Suffixed.Match(block);

        if (suffixed.Success)
        {
            var venue = suffixed.Groups["venue"].Value.ToUpperInvariant().ToLowerInvariant();
            var digits = suffixed.Groups["digits"].Value;

            return venue switch
            {
                "sh" or "sz" or "bj" when digits.Length == 6 => new CodeMatch(venue + digits, suffixed.Index, suffixed.Length),
                "hk" => new CodeMatch("hk" + digits.PadLeft(5, '0'), suffixed.Index, suffixed.Length),
                _ => null,
            };
        }

        var prefixed = Prefixed.Match(block);

        if (prefixed.Success)
        {
            var venue = prefixed.Groups["venue"].Value.ToLowerInvariant();
            var digits = prefixed.Groups["digits"].Value;

            return venue switch
            {
                "sh" or "sz" or "bj" when digits.Length == 6 => new CodeMatch(venue + digits, prefixed.Index, prefixed.Length),
                "hk" => new CodeMatch("hk" + digits.PadLeft(5, '0'), prefixed.Index, prefixed.Length),
                _ => null,
            };
        }

        var bare = Bare.Match(block);

        if (!bare.Success)
        {
            return null;
        }

        var value = bare.Groups["digits"].Value;

        if (value.Length == 6)
        {
            return value[0] switch
            {
                '6' => new CodeMatch("sh" + value, bare.Index, bare.Length),
                '0' or '3' => new CodeMatch("sz" + value, bare.Index, bare.Length),
                '4' or '8' => new CodeMatch("bj" + value, bare.Index, bare.Length),
                _ => null,
            };
        }

        // Five digits with nothing else to go on: a Hong Kong listing. The venue is inferred
        // rather than assumed silently — the dialog shows the code it read before anything is
        // applied, and a wrong one is visible there.
        return value.Length == 5 ? new CodeMatch("hk" + value, bare.Index, bare.Length) : null;
    }

    private sealed record CodeMatch(string Code, int Index, int Length);

    private static readonly Regex Suffixed = new(
        @"(?<digits>\d{6})\s*[.\-]?\s*(?<venue>SH|SZ|BJ|HK)\b|(?<digits>\d{4,5})\s*[.\-]?\s*(?<venue>HK)\b",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    private static readonly Regex Prefixed = new(
        @"\b(?<venue>SH|SZ|BJ|HK)\s*(?<digits>\d{5,6})\b",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    private static readonly Regex Bare = new(@"\b(?<digits>\d{5,6})\b", RegexOptions.Compiled);

    /// <summary>
    /// The name on the row: the Chinese run before the code, with the direction word taken off.
    ///
    /// Kept as the source spells it and displayed through <see cref="InstrumentNames"/>, so a
    /// reader whose interface is not Chinese still sees the name they know.
    /// </summary>
    private static string Name(string block, CodeMatch code)
    {
        var head = block[..Math.Min(block.Length, code.Index)];

        head = head.Replace("买入", " ").Replace("卖出", " ").Replace("全部成交", " ");

        var match = NameRun.Match(head);

        return match.Success ? match.Value : string.Empty;
    }

    private static readonly Regex NameRun = new(
        @"[\u3400-\u9FFF][\u3400-\u9FFFA-Za-z0-9\-]*", RegexOptions.Compiled);
}
