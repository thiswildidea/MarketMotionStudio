using System.Globalization;
using System.Text;

namespace MarketMotionStudio.Market;

/// <summary>What makes one line of a holdings sheet unusable.</summary>
public enum SheetProblem
{
    /// <summary>Not three or four fields — the row cannot even be read as a holding.</summary>
    Columns,

    /// <summary>The first field is not a code any venue answers to.</summary>
    Code,

    /// <summary>The share count is missing, zero, negative, or not a number.</summary>
    Shares,

    /// <summary>The cost is not a number. Negative is fine — a diluted cost goes negative.</summary>
    Cost,

    /// <summary>Another line above already carries this code.</summary>
    Duplicate,
}

/// <summary>One line that cannot be booked, and why. <paramref name="Line"/> counts the way a
/// reader counts — the first line of the file is 1, header included.</summary>
public sealed record SheetRow(int Line, SheetProblem Problem);

/// <summary>
/// The holdings list as a file: `code,name,shares,cost`, one position per line.
///
/// <para>
/// **The format is the one this page already speaks.** A holding is a code, a name, a share count
/// and a diluted cost; a CSV is the only shape a broker's export, Excel and this dialog all agree
/// on, and it opens in every one of them without an add-in. The header is fixed English —
/// `code,name,shares,cost` — rather than the interface's language: a file written on a machine
/// running Japanese has to be readable on one running German, and a header that changed with the
/// UI would make the same file mean different things in different places.
/// </para>
///
/// <para>
/// **What it will not do is guess.** A line with an unreadable code, a zero share count or text
/// where the cost should be is reported with its line number and nothing is applied — a book
/// half replaced by a file is a position nobody holds, and that is worse than a refused import.
/// </para>
/// </summary>
public static class HoldingsSheet
{
    /// <summary>The first line of every file this writes.</summary>
    public const string Header = "code,name,shares,cost";

    /// <summary>First fields that mean "this line is the header", across the languages a broker's
    /// export might be written in.</summary>
    private static readonly string[] Headers = ["code", "代码", "代碼", "コード", "코드"];

    /// <summary>The whole list as text: header, then one line per holding, CRLF between.</summary>
    public static string Write(IEnumerable<Holding> rows)
    {
        var text = new StringBuilder(Header);

        foreach (var holding in rows)
        {
            text.Append("\r\n")
                .Append(Field(holding.Code)).Append(',')
                .Append(Field(holding.Name)).Append(',')
                .Append(holding.Shares.ToString("0.####", CultureInfo.InvariantCulture)).Append(',')
                .Append(holding.Cost.ToString("0.####", CultureInfo.InvariantCulture));
        }

        return text.ToString();
    }

    /// <summary>
    /// Turns the bytes of a picked file into text, or says it cannot.
    ///
    /// **UTF-8 only, and strictly.** Excel in a Chinese locale writes "CSV (comma delimited)" in
    /// the system code page (GBK), which is not valid UTF-8; decoding that with replacement turns
    /// every name into U+FFFD — the mojibake this whole feature exists to avoid. Reading it
    /// strictly means the file is either read correctly or refused with an instruction to save it
    /// as "CSV UTF-8", which is the one behaviour a reader can act on.
    /// </summary>
    public static bool TryDecode(byte[] bytes, out string text)
    {
        text = string.Empty;

        if (bytes.Length >= 3 && bytes[0] == 0xEF && bytes[1] == 0xBB && bytes[2] == 0xBF)
        {
            text = Encoding.UTF8.GetString(bytes, 3, bytes.Length - 3);
            return true;
        }

        if (bytes.Length >= 2 && bytes[0] == 0xFF && bytes[1] == 0xFE)
        {
            text = Encoding.Unicode.GetString(bytes, 2, bytes.Length - 2).TrimStart('\uFEFF');
            return true;
        }

        if (bytes.Length >= 2 && bytes[0] == 0xFE && bytes[1] == 0xFF)
        {
            text = Encoding.BigEndianUnicode.GetString(bytes, 2, bytes.Length - 2).TrimStart('\uFEFF');
            return true;
        }

        try
        {
            text = new UTF8Encoding(false, throwOnInvalidBytes: true).GetString(bytes).TrimStart('\uFEFF');
            return true;
        }
        catch (DecoderFallbackException)
        {
            return false;
        }
    }

    /// <summary>
    /// Reads what <see cref="Write"/> wrote — and a hand-kept spreadsheet in the same shape.
    ///
    /// Three columns (`code,shares,cost`) are accepted as well as four, because a reader typing a
    /// list by hand has no name to put in and would otherwise have to invent one. A missing name
    /// is filled from the book by the caller.
    /// </summary>
    /// <param name="normalise">The dialog's own code rule, so a code typed here and the same code
    /// imported as a trade resolve to one listing rather than two.</param>
    public static (List<Holding> Rows, List<SheetRow> Problems) Parse(
        string text, Func<string, string?> normalise)
    {
        var rows = new List<Holding>();
        var problems = new List<SheetRow>();
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        var lines = text.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n');

        for (var i = 0; i < lines.Length; i++)
        {
            var line = lines[i];

            if (line.Trim().Length == 0)
            {
                continue;
            }

            // 1-based, as the reader's editor numbers it.
            var number = i + 1;
            var fields = Fields(line);

            if (Headers.Contains(fields[0].Trim().ToLowerInvariant()))
            {
                continue;
            }

            if (fields.Count is not (3 or 4))
            {
                problems.Add(new SheetRow(number, SheetProblem.Columns));
                continue;
            }

            var raw = fields[0];
            var code = normalise(raw);

            if (code is null)
            {
                problems.Add(new SheetRow(number, SheetProblem.Code));
                continue;
            }

            var name = fields.Count == 4 ? fields[1] : string.Empty;
            var sharesField = fields.Count == 4 ? fields[2] : fields[1];
            var costField = fields.Count == 4 ? fields[3] : fields[2];

            if (!double.TryParse(sharesField, NumberStyles.Float, CultureInfo.InvariantCulture, out var shares)
                || shares <= 0 || !double.IsFinite(shares))
            {
                problems.Add(new SheetRow(number, SheetProblem.Shares));
                continue;
            }

            if (!double.TryParse(costField, NumberStyles.Float, CultureInfo.InvariantCulture, out var cost)
                || !double.IsFinite(cost))
            {
                problems.Add(new SheetRow(number, SheetProblem.Cost));
                continue;
            }

            if (!seen.Add(code))
            {
                problems.Add(new SheetRow(number, SheetProblem.Duplicate));
                continue;
            }

            rows.Add(new Holding(code, name, Math.Round(shares, 4), Math.Round(cost, 4)));
        }

        return (rows, problems);
    }

    /// <summary>One field as RFC 4180 has it: quoted when it holds a comma, a quote or a break.</summary>
    private static string Field(string value) =>
        value.IndexOfAny([',', '"', '\r', '\n']) < 0
            ? value
            : "\"" + value.Replace("\"", "\"\"") + "\"";

    /// <summary>Splits a line on commas, honouring quotes — a name is allowed to contain one.</summary>
    private static List<string> Fields(string line)
    {
        var fields = new List<string>();
        var field = new StringBuilder();
        var quoted = false;

        for (var i = 0; i < line.Length; i++)
        {
            var c = line[i];

            if (quoted)
            {
                if (c != '"')
                {
                    field.Append(c);
                }
                else if (i + 1 < line.Length && line[i + 1] == '"')
                {
                    field.Append('"');
                    i++;
                }
                else
                {
                    quoted = false;
                }

                continue;
            }

            switch (c)
            {
                case '"':
                    quoted = true;
                    break;

                case ',':
                    fields.Add(field.ToString());
                    field.Clear();
                    break;

                default:
                    field.Append(c);
                    break;
            }
        }

        fields.Add(field.ToString());

        return fields;
    }
}
