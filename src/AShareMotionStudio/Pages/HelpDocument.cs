using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Documents;

namespace AShareMotionStudio.Pages;

/// <summary>
/// Renders the small slice of Markdown the help documents are written in.
///
/// Hand-written rather than taken from a package. This app ships one third-party
/// dependency and each one is a licence and a certification question at submission
/// time; a few dozen lines of text layout do not earn another. The subset is
/// deliberately small:
///
/// <list type="bullet">
/// <item><description><c>#</c>, <c>##</c>, <c>###</c> headings</description></item>
/// <item><description><c>-</c> bullets</description></item>
/// <item><description>blank line between paragraphs</description></item>
/// <item><description><c>**bold**</c> and <c>`code`</c> within a line</description></item>
/// </list>
///
/// Anything it does not recognise is emitted as the characters that were written,
/// markers and all. A renderer that quietly drops what it cannot read hides the
/// mistake in the source; one that shows it makes the mistake the first thing
/// anybody notices.
/// </summary>
internal static class HelpDocument
{
    /// <summary>
    /// Reads the document for the language the interface is actually in.
    /// </summary>
    public static async Task<string?> LoadAsync(string fileName)
    {
        // Not user input, but it is a name from outside this method on its way to a
        // path, and the cost of saying so is one call.
        var safe = Path.GetFileName(fileName);

        if (safe.Length == 0)
        {
            return null;
        }

        var path = Path.Combine(AppContext.BaseDirectory, "Assets", "Help", safe);

        return File.Exists(path) ? await File.ReadAllTextAsync(path) : null;
    }

    public static void Render(string markdown, Panel into)
    {
        into.Children.Clear();

        var block = new List<string>();
        var bulleted = false;

        foreach (var raw in markdown.Replace("\r\n", "\n").Split('\n'))
        {
            var line = raw.TrimEnd();

            if (line.Length == 0)
            {
                Flush();
                continue;
            }

            if (Heading(line) is { } heading)
            {
                Flush();
                into.Children.Add(heading);
                continue;
            }

            if (line.StartsWith("- ", StringComparison.Ordinal))
            {
                Flush();
                bulleted = true;
                block.Add(line[2..]);
                continue;
            }

            // A continuation of whatever is open, bullet or paragraph alike. Treating
            // a bullet as one line left every wrapped one rendered as a bullet
            // followed by a stray unindented paragraph, and split any **bold** that
            // spanned the wrap so the asterisks printed.
            block.Add(line.TrimStart());
        }

        Flush();

        void Flush()
        {
            if (block.Count == 0)
            {
                return;
            }

            // Joined with spaces: a block wrapped across source lines is one block,
            // and keeping the author's line breaks would re-wrap the text at whatever
            // width the file happened to be written to.
            var text = string.Join(" ", block);

            into.Children.Add(bulleted ? Bullet(text) : Body(text));

            block.Clear();
            bulleted = false;
        }
    }

    private static TextBlock? Heading(string line)
    {
        var (level, style) = line switch
        {
            _ when line.StartsWith("### ", StringComparison.Ordinal) => (4, "BodyStrongTextBlockStyle"),
            _ when line.StartsWith("## ", StringComparison.Ordinal) => (3, "SubtitleTextBlockStyle"),
            _ when line.StartsWith("# ", StringComparison.Ordinal) => (2, "TitleTextBlockStyle"),
            _ => (0, string.Empty),
        };

        if (level == 0)
        {
            return null;
        }

        var block = new TextBlock
        {
            Style = (Style)Application.Current.Resources[style],
            TextWrapping = TextWrapping.Wrap,
            Margin = new Thickness(0, level == 2 ? 0 : 20, 0, 6),
            IsTextSelectionEnabled = true,
        };

        Fill(block, line[level..]);
        return block;
    }

    private static UIElement Bullet(string text)
    {
        var row = new Grid { Margin = new Thickness(0, 2, 0, 2) };
        row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(18) });
        row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

        var dot = new TextBlock
        {
            Text = "\u2022",
            VerticalAlignment = VerticalAlignment.Top,
            Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["TextFillColorSecondaryBrush"],
        };

        var body = Body(text);
        Grid.SetColumn(body, 1);

        row.Children.Add(dot);
        row.Children.Add(body);
        return row;
    }

    private static TextBlock Body(string text)
    {
        var block = new TextBlock
        {
            TextWrapping = TextWrapping.Wrap,
            Margin = new Thickness(0, 0, 0, 8),
            IsTextSelectionEnabled = true,
            LineHeight = 21,
        };

        Fill(block, text);
        return block;
    }

    /// <summary>
    /// Splits a line on <c>**</c> and <c>`</c> and builds the runs.
    ///
    /// A marker left unclosed is emitted as itself rather than swallowing the rest of
    /// the line, so a typo costs one visible pair of asterisks instead of a paragraph
    /// that silently disappears.
    /// </summary>
    private static void Fill(TextBlock block, string text)
    {
        var at = 0;

        while (at < text.Length)
        {
            var bold = text.IndexOf("**", at, StringComparison.Ordinal);
            var code = text.IndexOf('`', at);

            var next = (bold, code) switch
            {
                (< 0, < 0) => -1,
                (< 0, _) => code,
                (_, < 0) => bold,
                _ => Math.Min(bold, code),
            };

            if (next < 0)
            {
                Add(text[at..], FontWeights.Normal, code: false);
                return;
            }

            var isBold = next == bold;
            var marker = isBold ? "**" : "`";
            var close = text.IndexOf(marker, next + marker.Length, StringComparison.Ordinal);

            if (close < 0)
            {
                Add(text[at..], FontWeights.Normal, code: false);
                return;
            }

            if (next > at)
            {
                Add(text[at..next], FontWeights.Normal, code: false);
            }

            Add(
                text[(next + marker.Length)..close],
                isBold ? FontWeights.SemiBold : FontWeights.Normal,
                code: !isBold);

            at = close + marker.Length;
        }

        void Add(string run, Windows.UI.Text.FontWeight weight, bool code)
        {
            if (run.Length == 0)
            {
                return;
            }

            block.Inlines.Add(new Run
            {
                Text = run,
                FontWeight = weight,
                FontFamily = code
                    ? new Microsoft.UI.Xaml.Media.FontFamily("Cascadia Mono, Consolas")
                    : block.FontFamily,
            });
        }
    }
}
