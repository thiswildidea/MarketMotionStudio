using MarketMotionStudio.Diagnostics;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Documents;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Imaging;

namespace MarketMotionStudio.Pages;

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
/// <item><description><c>![caption](media/picture.png)</c> on a line of its own</description></item>
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
    /// The language whose pictures to show, taken from the document's own file
    /// name — <c>help-ja.md</c> means <c>ja</c>.
    ///
    /// The manual is written once per language and the screenshots are captured
    /// once per language, so the two have to be chosen by the same decision.
    /// Reading it off the document rather than asking the settings again is what
    /// keeps them from disagreeing: a Japanese page showing English screenshots
    /// would be the same class of mistake as a Japanese window showing Chinese
    /// labels.
    /// </summary>
    private static string _language = string.Empty;

    /// <summary>
    /// Pictures are drawn at the manual's column width or at their own size,
    /// whichever is smaller — never stretched up. The number matches the width
    /// the help page gives its text (820 less the 24-wide padding on each side);
    /// a picture wider than the words around it looks like a mistake.
    /// </summary>
    private const double PictureWidth = 772;
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

        if (!File.Exists(path))
        {
            return null;
        }

        // Only once the document is known to be there: a language with a picture
        // folder but no manual would otherwise send the renderer looking for
        // screenshots to illustrate nothing.
        _language = Language(safe);

        return await File.ReadAllTextAsync(path);
    }

    /// <summary>
    /// <c>help-pt-BR.md</c> reads as <c>pt-BR</c>. A name that does not carry a
    /// language leaves it empty, which lands every picture on the shared folder.
    /// </summary>
    private static string Language(string file)
    {
        var name = Path.GetFileNameWithoutExtension(file);

        return name.StartsWith("help-", StringComparison.OrdinalIgnoreCase)
            ? name["help-".Length..]
            : string.Empty;
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

            // A picture sits on a line of its own. One written in the middle of a
            // sentence is left as the characters that were typed, which is what
            // this renderer does with everything it cannot lay out.
            if (Picture(line) is { } picture)
            {
                Flush();
                into.Children.Add(picture);
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
    {        var (level, style) = line switch
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

    /// <summary>
    /// Reads <c>![caption](media/sector-race.png)</c>, or nothing when the line is
    /// not that shape — the caller then treats it as ordinary text.
    /// </summary>
    private static UIElement? Picture(string line)
    {
        if (!line.StartsWith("![", StringComparison.Ordinal) || !line.EndsWith(')'))
        {
            return null;
        }

        var split = line.IndexOf("](", 2, StringComparison.Ordinal);

        if (split < 0)
        {
            return null;
        }

        var caption = line[2..split];
        var source = line[(split + 2)..^1].Trim();

        if (source.Length == 0)
        {
            return null;
        }

        var column = new StackPanel { Margin = new Thickness(0, 8, 0, 14) };

        if (PictureFile(source) is { } file)
        {
            column.Children.Add(new Border
            {
                // Left-aligned so a picture narrower than the column keeps its own
                // width instead of sitting in a frame stretched across the page.
                HorizontalAlignment = HorizontalAlignment.Left,
                Padding = new Thickness(4),
                CornerRadius = new CornerRadius(8),
                BorderThickness = new Thickness(1),
                Background = (Brush)Application.Current.Resources["CardBackgroundFillColorDefaultBrush"],
                BorderBrush = (Brush)Application.Current.Resources["CardStrokeColorDefaultBrush"],
                Child = new Image
                {
                    Source = new BitmapImage(file),
                    Stretch = Stretch.Uniform,
                    MaxWidth = PictureWidth,
                },
            });
        }
        else
        {
            // Not shown to the reader. A picture that failed to copy is the
            // developer's problem, not something to put in front of somebody who
            // opened the manual because something was already going wrong; the log
            // is where it gets noticed.
            CrashLog.Note($"Help picture missing: {source} ({_language})");
        }

        if (caption.Length > 0)
        {
            column.Children.Add(new TextBlock
            {
                Text = caption,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(2, 8, 0, 0),
                Style = (Style)Application.Current.Resources["CaptionTextBlockStyle"],
                Foreground = (Brush)Application.Current.Resources["TextFillColorSecondaryBrush"],
                IsTextSelectionEnabled = true,
            });
        }

        return column;
    }

    /// <summary>
    /// Finds the file a reference names, preferring the folder for the document's
    /// own language: <c>media/sector-race.png</c> resolves to
    /// <c>media/ja/sector-race.png</c> before <c>media/sector-race.png</c>.
    ///
    /// That way the fourteen documents point at one name per picture and the
    /// screenshots still come out in the right language — no language tag inside
    /// the prose, and nothing to keep in step by hand.
    /// </summary>
    private static Uri? PictureFile(string source)
    {
        var relative = source.Replace('\\', '/').TrimStart('/');

        // The path arrives from a file rather than from the user, but it arrives as
        // a path, and `..` in one walks out of the manual's own folder.
        if (relative.Length == 0 || relative.Split('/').Contains(".."))
        {
            return null;
        }

        var cut = relative.IndexOf('/');
        var localized = _language.Length > 0 && cut > 0
            ? string.Concat(relative.AsSpan(0, cut + 1), _language, "/", relative.AsSpan(cut + 1))
            : null;

        foreach (var candidate in new[] { localized, relative })
        {
            if (candidate is null)
            {
                continue;
            }

            var path = Path.Combine(AppContext.BaseDirectory, "Assets", "Help", candidate);

            if (File.Exists(path))
            {
                return new Uri(path);
            }
        }

        return null;
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
