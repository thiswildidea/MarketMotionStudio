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

        /// <summary>
        /// Rows the engine read every part of except the direction — a code, a price, a size and a
        /// clock were all there, only 买入 / 卖出 was dropped.
        ///
        /// **This is the common OCR failure, and it is not the parser's to guess.** On a broker's
        /// dark order list the direction word is the only white text at the left edge of the row,
        /// and Windows' recogniser drops it far more often than it keeps it — measured on the day's
        /// own list, one of seven came back with it. The row is a trade in every other respect, so
        /// rather than dropping it as unreadable (which would block the whole import) it is handed
        /// back here for the reader to choose 买入 or 卖出 in the dialog. A trade with no direction
        /// is worse than a missing one: it would be applied as whichever way the guess fell.
        /// </summary>
        public IReadOnlyList<string> Incomplete { get; init; } = [];
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
            .Replace('：', ':').Replace('，', ',').Replace('、', ',').Replace('％', '%')
            .Replace('．', '.').Replace('－', '-').Replace('　', ' ')
            .Replace('·', '.').Replace('•', '.').Replace('・', '.');

        // **The clock's colon is what OCR loses most often, and it loses it in every direction**:
        // as a full-width colon, as a semicolon, as a full-width semicolon. That matters more
        // than it looks, because a block is delimited *by* its clock (see `Blocks`) — one
        // unreadable clock merges two rows into one, and what comes out is a single trade with
        // the first row's price and the second row's code and timestamp. Between two digits a
        // semicolon is never anything else, so it becomes a colon here.
        text = ClockColon.Replace(text, ":");

        // **A clock that lost its second colon entirely** — 14:5002 for 14:50:02. Four digits
        // behind a colon is not a time any other way, and an unreadable clock is worse than a
        // missing one: `Blocks` delimits rows by the clock, so one bad stamp merges two orders
        // into a single row and the parser reads the first one's price with the second one's
        // size. Repaired here, where every other clock artefact is repaired.
        text = ClockRun.Replace(text, "$1:$2:$3");

        // **A comma inside a number is one of two things, and the digit count says which.** The
        // broker prints at most two decimals and never groups a size with two digits after the
        // comma, so `31,80` is a price and `5,900` is a size. Left alone, `31,80` reads as two
        // numbers — 31 and 80 — and the trade is imported at 31.00, which is the kind of import
        // nobody notices until the day's profit disagrees with the broker by a thousand yuan.
        text = CommaSpace.Replace(text, "$1");
        text = Thousands.Replace(text, "$1");
        text = Decimals.Replace(text, ".$1");

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

    private static readonly Regex ClockColon =
        new(@"(?<=\d)\s*[;；∶]\s*(?=\d)", RegexOptions.Compiled);

    /// <summary>`14:5002` — a clock that lost its second colon. Four digits behind one colon is
    /// never a time any other way, and an unreadable clock is worse than a missing one:
    /// <see cref="Blocks"/> delimits rows by the clock, so one bad stamp merges two orders into a
    /// single row and the parser reads the first one's price with the second one's size. Repaired
    /// here, beside the other clock artefacts.</summary>
    private static readonly Regex ClockRun =
        new(@"\b(\d{1,2}):(\d{2})(\d{2})\b", RegexOptions.Compiled);

    private static readonly Regex CommaSpace = new(@"\s*(,)\s*", RegexOptions.Compiled);

    /// <summary>`5,900` — three digits after the comma is a thousands group, so the comma goes.</summary>
    private static readonly Regex Thousands = new(@"(?<=\d),(\d{3})(?!\d)", RegexOptions.Compiled);

    /// <summary>`31,80` — one or two digits after it is the decimal point the engine misread.</summary>
    private static readonly Regex Decimals = new(@"(?<=\d),(\d{1,2})(?!\d)", RegexOptions.Compiled);

    /// <summary>A text line, with the band it occupied in the picture.</summary>
    /// <param name="Text">The words, left to right.</param>
    /// <param name="Top">Top edge, in the same pixels as the words.</param>
    /// <param name="Height">Tallest word on the line.</param>
    public readonly record struct TextRow(string Text, double Top, double Height);

    /// <summary>
    /// Turns OCR words into text lines, one per visual row, left to right.
    ///
    /// Rows are found by height rather than by a fixed tolerance: a phone screenshot at 2× has
    /// characters three times the height of the same screenshot at 1×, and a pixel threshold
    /// tuned on one would merge every row of the other. A word joins the current row when its top
    /// is within most of a character of where that row started.
    /// </summary>
    public static IReadOnlyList<TextRow> RowBoxes(IEnumerable<OcrWord> words)
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
        return
        [
            .. rows.Select(r => new TextRow(
                string.Join(" ", r.OrderBy(w => w.X).Select(w => w.Text)),
                r.Min(w => w.Y),
                r.Max(w => w.Height))),
        ];
    }

    /// <summary>The same rows, as text.</summary>
    public static IReadOnlyList<string> Rows(IEnumerable<OcrWord> words) =>
        [.. RowBoxes(words).Select(r => r.Text)];

    /// <summary>
    /// Puts the direction word back on rows that were read without one.
    ///
    /// **The direction is the one field the parser will not guess, and it is the one the engine
    /// loses most often** — on the day's own list it read 买入 on one row out of seven and 卖出 on
    /// the last. The reason is not size: those two words are the only *coloured* text on a broker's
    /// dark order list, and the recogniser drops coloured text on a dark background far more
    /// readily than white. Reading the same picture again with everything but the colour thrown
    /// away (see <c>ScreenshotText</c>) gets all seven; this puts them back where they belong, by
    /// the band each one sat in. A row that already says its direction is left alone, so the
    /// second reading can only add, never overwrite.
    /// </summary>
    public static IReadOnlyList<string> Attach(IReadOnlyList<TextRow> rows, IReadOnlyList<TextRow> sides)
    {
        var text = rows.Select(r => r.Text).ToList();

        foreach (var side in sides)
        {
            var word = side.Text.Contains("卖出", StringComparison.Ordinal) ? "卖出"
                : side.Text.Contains("买入", StringComparison.Ordinal) ? "买入"
                : null;

            if (word is null)
            {
                continue;
            }

            var centre = side.Top + (side.Height / 2);
            var index = -1;
            var best = double.MaxValue;

            for (var i = 0; i < rows.Count; i++)
            {
                if (Side(text[i]) is not null)
                {
                    continue;
                }

                var middle = rows[i].Top + (rows[i].Height / 2);
                var distance = Math.Abs(middle - centre);
                var reach = Math.Max(rows[i].Height, side.Height);

                if (distance <= reach && distance < best)
                {
                    best = distance;
                    index = i;
                }
            }

            if (index >= 0)
            {
                text[index] = $"{word} {text[index]}";
            }
        }

        return text;
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
        var incomplete = new List<string>();

        foreach (var block in blocks)
        {
            // **Only what the list says actually happened.** A broker's order table carries a
            // status column — 已成 / 全部成交 / 已撤 / 废单 — and a cancelled row carries every
            // other field a filled one does: the code, the price, the size and the clock. Read
            // without the status, a day of cancelled orders becomes a day of trades, and the book
            // then disagrees with the broker in a way nothing on the page can explain. Rows that
            // say nothing about a status are taken: the tab these screenshots come from is the
            // filled-order tab, and a hand-typed list has no room for a column it does not need.
            if (IsCancelled(block) || Unfilled(block))
            {
                cancelled.Add(block);
                continue;
            }

            if (Read(block) is { } trade)
            {
                trades.Add(trade);
            }
            else if (LooksLikeTrade(block))
            {
                // Everything but the direction: the reader chooses 买入 / 卖出 in the dialog
                // rather than this row blocking the import of the trades that did read cleanly.
                incomplete.Add(block);
            }
            else if (block.Length > 0)
            {
                skipped.Add(block);
            }
        }

        return new TradeParse(trades, skipped)
        {
            Cancelled = cancelled,
            Incomplete = incomplete,
        };
    }

    /// <summary>
    /// Whether the list has a row that looks like a trade but says nothing about its direction.
    ///
    /// The direction is the field the reader will not guess — `买入` and `卖出` are the
    /// difference between a position added and a position closed — and it is the one the engine
    /// loses most often, because on these lists it is the leftmost and thinnest text on the row.
    /// A row carrying a code or a clock but no direction is importable in every other respect and
    /// unusable as it stands, which is what the second reading in
    /// <see cref="ScreenshotText.ReadAsync"/> is for.
    /// </summary>
    public static bool Incomplete(IReadOnlyList<string> rows) =>
        rows.Any(row => Side(row) is null && (Code(row) is not null || Clock.IsMatch(row)));

    /// <summary>
    /// Row by row, the reading that says more about the row.
    ///
    /// A row the smaller reading took without its direction is replaced by the same row from the
    /// bigger one. **The whole row comes from one reading** — never a part of each — so no row
    /// can end up with one reading's price and the other's size. Rows that do not line up are not
    /// merged at all: two readings of different row counts are readings of different pictures, or
    /// of the same picture cut up differently, and the smaller is the one the numbers were
    /// checked against.
    /// </summary>
    public static IReadOnlyList<string> Merge(IReadOnlyList<string> first, IReadOnlyList<string> second)
    {
        if (first.Count != second.Count)
        {
            return first;
        }

        return [.. first.Select((row, i) => Side(row) is null && Side(second[i]) is not null ? second[i] : row)];
    }

    /// <summary>How a broker's order table spells "this did not happen", in its several ways.</summary>
    private static bool IsCancelled(string block) =>
        CancelledWords.Any(word => block.Contains(word, StringComparison.Ordinal));

    /// <summary>
    /// A row whose 成交量 column reads zero: the order was cancelled, or never traded at all.
    ///
    /// **The status word is not the only way a cancellation shows up.** One broker's list prints
    /// the sizes as two lines — 委托量 on top, 成交量 under it — so a cancelled row reads
    /// "37.66 200" on the first line and a bare "0" on the second, with 全部撤单 to the right of
    /// neither. When the engine loses that status cell (it is the thinnest text on the row) what
    /// is left looks exactly like a fill of 200 shares. Reading the last size instead of the
    /// first is what tells them apart: nothing filled means nothing to import.
    /// </summary>
    private static bool Unfilled(string block)
    {
        var clock = Clock.Match(block);
        var rest = clock.Success ? block.Replace(clock.Value, " ") : block;

        var whole = Figures.Matches(WithoutCodes(rest))
            .Select(m => m.Value)
            .Where(v => !v.Contains('.'))
            .Select(Number)
            .ToList();

        return whole.Count >= 2 && whole[^1] <= 0;
    }

    /// <summary>A copy of the row with every code on it taken out, so a code's digits are never
    /// read as a price or a size.</summary>
    private static string WithoutCodes(string block)
    {
        var text = block;

        for (var i = 0; i < 6; i++)
        {
            if (Code(text) is not { } code)
            {
                break;
            }

            text = text.Remove(code.Index, code.Length);
        }

        return text;
    }

    private static readonly string[] CancelledWords =
    [
        "已撤", "部撤", "撤单", "撤销", "废单",
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
        var parts = new List<(int Start, int End)>();
        var start = 0;

        foreach (Match clock in clocks)
        {
            var end = clock.Index + clock.Length;

            if (joined[start..end].Trim().Length > 0)
            {
                parts.Add((start, end));
            }

            start = end;
        }

        // Anything after the last clock is a footer (the broker's own advertising line, the tab
        // bar) — and, on the two-line layout, the last row's own code. Kept as a part so the row
        // above can take its code from it, and reported as skipped if anything is left over.
        if (joined[start..].Trim().Length > 0)
        {
            parts.Add((start, joined.Length));
        }

        var starts = parts.Select(p => p.Start).ToArray();
        var blocks = new List<string>();

        for (var i = 0; i < parts.Count; i++)
        {
            var end = parts[i].End;

            if (starts[i] >= end)
            {
                continue;
            }

            var text = joined[starts[i]..end].Trim();

            if (Code(text) is null)
            {
                // **The code can sit on the row's second line, after the clock.** A broker that
                // prints the name above the code — 公牛集团 over 603195.SH — puts the code past
                // the only delimiter the row has, so the block above it carries a direction, a
                // price and a size but no code, and the code then opens the *next* block and
                // lends its numbers to the wrong row. Reading forward from this clock to the next
                // row's direction word is what reunites them: everything in between is this row's
                // second line, and it belongs to this row.
                var remainder = joined[end..];
                var nextClock = Clock.Match(remainder);
                var bound = nextClock.Success ? nextClock.Index : remainder.Length;
                var after = remainder[..bound];
                var side = FirstSide(after);
                var segment = side >= 0 ? after[..side] : after;

                if (segment.Trim().Length > 0 && Code(segment) is not null)
                {
                    text = $"{text} {segment.Trim()}".Trim();

                    if (i + 1 < parts.Count)
                    {
                        starts[i + 1] = end + segment.Length;
                    }
                }
            }

            if (text.Length > 0)
            {
                blocks.Add(text);
            }
        }

        return [.. blocks.SelectMany(Single)];
    }

    /// <summary>The first direction word in a stretch of text, or -1 when it has none.</summary>
    private static int FirstSide(string text)
    {
        var buy = text.IndexOf("买入", StringComparison.Ordinal);
        var sell = text.IndexOf("卖出", StringComparison.Ordinal);

        if (buy < 0)
        {
            return sell;
        }

        return sell < 0 ? buy : Math.Min(buy, sell);
    }

    /// <summary>
    /// One trade per block: a block carrying two codes is two rows.
    ///
    /// The boundary is the clock, and an unreadable clock is the one thing that takes it away.
    /// Two rows then arrive as one block, and <see cref="Read"/> would report a trade made of the
    /// first row's price and the second row's code and timestamp — a *wrong* trade, which is far
    /// worse than a missing one: it is applied to somebody's book without anything on screen
    /// saying it was guessed. Cutting at the second code costs the first row (reported, so the
    /// reader can fix it) and leaves the second row whole.
    /// </summary>
    private static IEnumerable<string> Single(string block)
    {
        var first = Code(block);
        var rest = first is null ? null : Code(block[(first.Index + first.Length)..]);

        if (first is null || rest is null)
        {
            yield return block;
            yield break;
        }

        var cut = first.Index + first.Length + rest.Index;

        yield return block[..cut].Trim();

        foreach (var part in Single(block[cut..]))
        {
            yield return part;
        }
    }

    private static readonly Regex Clock = new(@"\b\d{1,2}:\d{2}:\d{2}\b", RegexOptions.Compiled);

    /// <summary>
    /// Whether a block is a trade that only lost its direction: a code, a clock and at least a
    /// price and a size, but no 买入 / 卖出. Anything that is not even that is a row the parser
    /// could not read at all, and belongs in <see cref="TradeParse.Skipped"/> instead.
    /// </summary>
    private static bool LooksLikeTrade(string block) =>
        Side(block) is null
        && Code(block) is not null
        && Clock.IsMatch(block)
        && Figures.Matches(block).Count >= 2;

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
            var venue = Venue(suffixed.Groups["venue"].Value);
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
            var venue = Venue(prefixed.Groups["venue"].Value);
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

    /// <summary>
    /// The venue as the engine spelled it: `SZ`, and also `5Z` — at a small text height an `S` is
    /// read as a `5` often enough that a whole row was being dropped for it ("3000365z" on the
    /// day's own list). The two-letter suffix is what carries the venue, so recovering the first
    /// letter from its neighbour is not a guess about the number: the digits came through on
    /// their own.
    /// </summary>
    private static string Venue(string raw) => raw.ToLowerInvariant().Replace('5', 's');

    /// <summary>
    /// A six-digit code followed by its venue. The first letter of the venue may come back as a
    /// `5`, and one stray character may stand between the digits and the suffix — both are what
    /// the engine does to `.SZ` at a small size.
    /// </summary>
    private static readonly Regex Suffixed = new(
        @"(?<digits>\d{6})\s*[.\-]?\s*(?<venue>[Ss5][Hh]|[Ss5][Zz]|[Bb][Jj]|[Hh][Kk])\b"
        + @"|(?<digits>\d{4,5})\s*[.\-]?\s*(?<venue>[Hh][Kk])\b",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    private static readonly Regex Prefixed = new(
        @"\b(?<venue>[Ss5][Hh]|[Ss5][Zz]|[Bb][Jj]|[Hh][Kk])\s*(?<digits>\d{5,6})\b",
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
