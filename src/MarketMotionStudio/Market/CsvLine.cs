namespace MarketMotionStudio.Market;

/// <summary>
/// One comma-separated line, split the way this app writes them.
///
/// <para>
/// **The grammar is two rules, and it is this app's own.** A field may be wrapped in double
/// quotes — because a stock's name can carry a comma — and a quote inside one is doubled. That is
/// the whole of what <see cref="PortfolioLedger"/> writes, and a general CSV reader would accept
/// far more than these files can mean: a stray semicolon, a locale's decimal comma, a second
/// header row. Accepting those is how a holdings list imports with its cost column reading zero.
/// </para>
///
/// <para>
/// **One reader for both directions.** The snapshot importer and the trade importer read the same
/// three files this app exports, so they must agree about where a field ends — two splitters is
/// two answers to that, and the file would import in one dialog and not the other.
/// </para>
/// </summary>
public static class CsvLine
{
    /// <summary>The fields of one line, quotes honoured and removed.</summary>
    public static List<string> Split(string line)
    {
        var fields = new List<string>();
        var field = new System.Text.StringBuilder();
        var quoted = false;

        for (var i = 0; i < line.Length; i++)
        {
            var c = line[i];

            if (quoted)
            {
                if (c == '"' && i + 1 < line.Length && line[i + 1] == '"')
                {
                    field.Append('"');
                    i++;
                }
                else if (c == '"')
                {
                    quoted = false;
                }
                else
                {
                    field.Append(c);
                }

                continue;
            }

            if (c == '"')
            {
                quoted = true;
            }
            else if (c == ',')
            {
                fields.Add(field.ToString());
                field.Clear();
            }
            else
            {
                field.Append(c);
            }
        }

        fields.Add(field.ToString());

        return fields;
    }
}
