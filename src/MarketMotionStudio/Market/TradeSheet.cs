using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Threading.Tasks;
using System.Xml.Linq;
using Windows.Storage;

namespace MarketMotionStudio.Market;

/// <summary>
/// Reads a broker's order workbook (`.xlsx`) into the same rows <see cref="TradeText"/> parses.
///
/// <para>
/// **The workbook is read as the zip of XML it is.** An `.xlsx` is a compressed package whose
/// worksheet cells carry either a literal or an index into a shared string table; both are read
/// here with nothing beyond the base class library, because a table of one's own trades is not
/// worth a spreadsheet dependency. The columns are found by their **header words** — 方向, 代码,
/// 委托价, 成交数量, 时间, 状态 — never by position: an export that adds a column or reorders two
/// must keep working.
/// </para>
///
/// <para>
/// Rows that did not trade are left out here rather than left to the parser: a cancelled order
/// (状态 says 撤单/废单, or its 成交数量 reads zero) is a row the broker already answered, and the
/// workbook's footer statistics (委托统计, 合计) are not rows at all. What remains is emitted in
/// the same shape a filled-order screenshot reads — direction, name, code, price, filled size,
/// status, clock — so there is one parser and one preview for a paste, a screenshot or a workbook.
/// </para>
/// </summary>
public static class TradeSheet
{
    /// <summary>The workbook's filled orders, as parser-ready rows, top to bottom.</summary>
    public static async Task<IReadOnlyList<string>> ReadAsync(StorageFile file)
    {
        using var stream = await file.OpenStreamForReadAsync();

        return Read(stream);
    }

    /// <summary>Same reading, from a stream the caller opens and owns.</summary>
    public static IReadOnlyList<string> Read(Stream stream)
    {
        using var zip = new ZipArchive(stream, ZipArchiveMode.Read);

        var shared = SharedStrings(zip);
        var sheet = zip.Entries.FirstOrDefault(e =>
            e.FullName.StartsWith("xl/worksheets/", StringComparison.OrdinalIgnoreCase)
            && e.FullName.EndsWith(".xml", StringComparison.OrdinalIgnoreCase));

        if (sheet is null)
        {
            return [];
        }

        XDocument doc;

        using (var entry = sheet.Open())
        {
            doc = XDocument.Load(entry);
        }

        var ns = doc.Root?.Name.Namespace
            ?? throw new InvalidDataException("工作表缺少命名空间");

        // Cell values by (row, column). A shared-string cell carries the index; an inline one
        // carries its own text; a number or a time carries a literal.
        var cells = new Dictionary<(int Row, int Col), string>();

        foreach (var row in doc.Descendants(ns + "row"))
        {
            var index = (int?)row.Attribute("r") ?? 0;

            foreach (var cell in row.Elements(ns + "c"))
            {
                var type = (string?)cell.Attribute("t");
                string? value;

                if (type == "inlineStr")
                {
                    value = cell.Descendants(ns + "t").FirstOrDefault()?.Value;
                }
                else
                {
                    var raw = cell.Element(ns + "v")?.Value;
                    value = raw is null ? null : type == "s" ? Shared(raw, shared) : raw;
                }

                if (!string.IsNullOrWhiteSpace(value))
                {
                    cells[(index, Column((string?)cell.Attribute("r")))] = value.Trim();
                }
            }
        }

        var rows = cells.Keys.Select(k => k.Row).Distinct().OrderBy(r => r).ToList();

        // **The header row is found by its words, not assumed to be the first.** An export often
        // carries a title line above it, and assuming row 1 would map every column to nothing.
        // Excel rows are 1-based, so an unfound header leaves FirstOrDefault at 0.
        var header = rows.FirstOrDefault(r => Word(cells, r, "方向") is not null);

        if (header == 0)
        {
            return [];
        }

        var map = Columns(cells, header);

        if (map.Count == 0)
        {
            return [];
        }

        var lines = new List<string>();

        foreach (var r in rows.Where(r => r > header))
        {
            var side = Word(cells, r, "方向", map);
            var name = Word(cells, r, "股票名称", "名称", map) ?? string.Empty;
            var code = Word(cells, r, "代码", map) ?? string.Empty;
            var price = Number(Word(cells, r, "委托价", map) ?? Word(cells, r, "成交价", "现价", map));
            var filled = Number(Word(cells, r, "成交数量", "成交量", map));
            var status = Word(cells, r, "状态", map) ?? string.Empty;
            var clock = Clock(Word(cells, r, "时间", map));

            if (side is not ("买入" or "卖出") || code.Length == 0 || clock is null)
            {
                continue;
            }

            // **A row the workbook says did not trade is not imported.** The status word is the
            // broker's own answer (撤单 / 废单 / 未成交); a zero filled size says the same thing
            // when the word is missing. Both are left out here, so the parser never sees them.
            if (Cancelled(status) || filled <= 0 || price <= 0)
            {
                continue;
            }

            var statusWord = status.Length > 0 ? $" {status}" : string.Empty;

            lines.Add($"{side} {name} {code.ToLowerInvariant()} {price.ToString("0.###", CultureInfo.InvariantCulture)} {filled.ToString("0", CultureInfo.InvariantCulture)}{statusWord} {clock}");
        }

        return lines;
    }

    private static bool Cancelled(string status)
    {
        foreach (var word in new[] { "撤", "废单", "未成交", "待成交", "申报中" })
        {
            if (status.Contains(word, StringComparison.Ordinal))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>The value at `row` under the first of these header words that the sheet has.</summary>
    private static string? Word(IReadOnlyDictionary<(int Row, int Col), string> cells, int row, params object[] parts)
    {
        // Last element is the column map when the caller used the mapped overload; flatten both
        // shapes into one list of header words.
        var words = parts.OfType<string>()
            .Where(p => p is not "map")
            .ToArray();
        var map = parts.OfType<IReadOnlyDictionary<string, int>>().FirstOrDefault();

        foreach (var word in words)
        {
            if (map is not null && map.TryGetValue(word, out var mapped))
            {
                return cells.TryGetValue((row, mapped), out var value) && value.Length > 0 ? value : null;
            }

            // Unmapped word (the header search itself): scan the row for it.
            var hit = cells.Keys
                .Where(k => k.Row == row && cells[k] == word)
                .Select(k => (int?)k.Col)
                .FirstOrDefault();

            if (hit is { } column)
            {
                return cells.TryGetValue((row, column), out var value) ? value : null;
            }
        }

        return null;
    }

    /// <summary>Maps each header word to its column, for the rows below the header.</summary>
    private static IReadOnlyDictionary<string, int> Columns(
        IReadOnlyDictionary<(int Row, int Col), string> cells, int row)
    {
        var wanted = new[]
        {
            "方向", "股票名称", "名称", "代码", "委托价", "成交价", "现价",
            "委托数量", "委托量", "成交数量", "成交量", "时间", "状态",
        };

        var map = new Dictionary<string, int>();

        foreach (var (r, c) in cells.Keys.Where(k => k.Row == row))
        {
            var word = cells[(r, c)];

            if (wanted.Contains(word))
            {
                map[word] = c;
            }
        }

        return map;
    }

    /// <summary>A price or a size, tolerant of the comma a thousand-group puts in.</summary>
    private static double Number(string? value) =>
        value is null ? 0
        : double.TryParse(value.Replace(",", string.Empty), NumberStyles.Float,
            CultureInfo.InvariantCulture, out var d) ? d : 0;

    /// <summary>
    /// The clock the workbook carries. A text export keeps `14:56:29`; a cell formatted as a time
    /// keeps a fraction of a day, which is hours and minutes again once the fraction is unfolded.
    /// A date-time string gives up its date part — the picker already holds the day.
    /// </summary>
    private static string? Clock(string? value)
    {
        if (value is null)
        {
            return null;
        }

        var text = value.Trim();

        var space = text.LastIndexOf(' ');

        if (space >= 0 && text[(space + 1)..].Contains(':'))
        {
            text = text[(space + 1)..];
        }

        if (text.Contains(':'))
        {
            var parts = text.Split(':');

            return parts.Length switch
            {
                3 => $"{int.Parse(parts[0], CultureInfo.InvariantCulture):00}:{int.Parse(parts[1], CultureInfo.InvariantCulture):00}:{int.Parse(parts[2], CultureInfo.InvariantCulture):00}",
                2 => $"{int.Parse(parts[0], CultureInfo.InvariantCulture):00}:{int.Parse(parts[1], CultureInfo.InvariantCulture):00}:00",
                _ => null,
            };
        }

        // A fraction of a day: 0.6226 is 14:56:29 once the day is 86,400 seconds wide.
        if (double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out var fraction)
            && fraction is > 0 and < 1)
        {
            var seconds = (int)Math.Round(fraction * 86400);

            return $"{seconds / 3600:00}:{seconds % 3600 / 60:00}:{seconds % 60:00}";
        }

        return null;
    }

    private static int Column(string? reference)
    {
        var column = 0;

        foreach (var ch in reference ?? string.Empty)
        {
            if (ch is >= 'A' and <= 'Z')
            {
                column = column * 26 + (ch - 'A' + 1);
            }
            else if (ch is >= 'a' and <= 'z')
            {
                column = column * 26 + (ch - 'a' + 1);
            }
            else
            {
                break;
            }
        }

        return Math.Max(1, column) - 1;
    }

    private static string Shared(string index, IReadOnlyDictionary<string, string> table) =>
        table.TryGetValue(index, out var text) ? text : string.Empty;

    private static IReadOnlyDictionary<string, string> SharedStrings(ZipArchive zip)
    {
        var entry = zip.GetEntry("xl/sharedStrings.xml");

        if (entry is null)
        {
            return new Dictionary<string, string>();
        }

        using var stream = entry.Open();
        var doc = XDocument.Load(stream);
        var ns = doc.Root?.Name.Namespace ?? throw new InvalidDataException();
        var table = new Dictionary<string, string>();
        var i = 0;

        foreach (var item in doc.Descendants(ns + "si"))
        {
            table[i.ToString(CultureInfo.InvariantCulture)] = string.Concat(item.Descendants(ns + "t").Select(t => t.Value));
            i++;
        }

        return table;
    }
}
