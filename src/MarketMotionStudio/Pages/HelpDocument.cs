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
    /// Where the manual is published, besides being shipped inside the package.
    ///
    /// The package carries every document and every picture, so the application
    /// answers with the manual whether or not there is a network. This is the
    /// copy that can be corrected without a Store submission: re-wording a
    /// sentence, adding a chapter or replacing a screenshot is a commit to the
    /// support site, not a new build. Help is read by somebody who is already
    /// stuck, and a wrong sentence in it should not have to wait weeks.
    ///
    /// One place to write a sentence, not two: <c>tools/publish-help-to-support.py</c>
    /// copies the packaged folder to the site, so the two are the same files by
    /// construction rather than by care.
    /// </summary>
    private const string Remote = "https://thiswildidea.github.io/MarketMotionStudio-Support/help/";

    /// <summary>
    /// How long the published copy gets before the packaged one is shown.
    ///
    /// Short on purpose. This page is opened by somebody who is already stuck,
    /// and a blank page for half a minute is worse than a page one revision
    /// behind; the packaged copy is a complete manual, not a stub.
    /// </summary>
    private static readonly TimeSpan RemoteWait = TimeSpan.FromSeconds(6);

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
    /// Whether the document on screen came from the site or from the package,
    /// which is what the pictures are read from too.
    ///
    /// Kept beside <see cref="_language"/> rather than inside
    /// <see cref="LoadAsync"/> because the two are always asked together and
    /// always about the same document: prose from the site and pictures from the
    /// package would be two documents shown as one.
    /// </summary>
    private static bool _published;

    /// <summary>
    /// Pictures are drawn at the manual's column width or at their own size,
    /// whichever is smaller — never stretched up. The number matches the width
    /// the help page gives its text (820 less the 24-wide padding on each side);
    /// a picture wider than the words around it looks like a mistake.
    /// </summary>
    private const double PictureWidth = 772;
    /// <summary>
    /// Reads the document for the language the interface is actually in: the
    /// published copy first, the packaged one when that cannot be had.
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

        // Set before either copy is tried, because both name the same document:
        // the pictures are chosen by what the reader asked for, not by which
        // answer arrived. Nothing looks a picture up until a document is in hand,
        // so a language whose manual turns up nowhere still shows nothing.
        _language = Language(safe);

        if (await PublishedAsync(safe) is { } published)
        {
            _published = true;
            return published;
        }

        _published = false;

        var path = Path.Combine(AppContext.BaseDirectory, "Assets", "Help", safe);

        return File.Exists(path) ? await File.ReadAllTextAsync(path) : null;
    }

    /// <summary>
    /// The published copy, or <c>null</c> when it could not be had — no network,
    /// an answer that took too long, a 404, or a page of something that is not
    /// the document.
    ///
    /// All of those are one answer to the caller: show the packaged copy. None of
    /// them is said to the reader, because from where they are sitting nothing is
    /// wrong — they have a manual either way. The log is where the site being
    /// wrong gets noticed.
    /// </summary>
    private static async Task<string?> PublishedAsync(string file)
    {
        try
        {
            using var give = new CancellationTokenSource(RemoteWait);
            var text = await AppServices.Current.Http.GetStringAsync(new Uri(Remote + file), give.Token);

            if (Readable(text))
            {
                return text;
            }

            CrashLog.Note($"Help document at {Remote}{file} is not a document: {Head(text)}");
        }
        catch (Exception problem)
        {
            CrashLog.Note($"Help document not fetched: {file} ({problem.GetType().Name})");
        }

        return null;
    }

    /// <summary>
    /// A document, rather than whatever else a URL can answer with.
    ///
    /// Every manual opens with its own title and runs to tens of kilobytes. An
    /// error page, an empty answer, or — the one that actually happens — a host
    /// that helpfully renders the Markdown into an HTML page fails one of those
    /// three, and rendering that as the manual would put markup in front of the
    /// reader. Checked rather than assumed, because the failure is silent
    /// otherwise: the page would still draw, just wrongly.
    /// </summary>
    private static bool Readable(string text) =>
        text.Length > 2000 &&
        text.StartsWith("# ", StringComparison.Ordinal) &&
        !text.Contains("<html", StringComparison.OrdinalIgnoreCase);

    /// <summary>The first few characters, for a log line about something unexpected.</summary>
    private static string Head(string text) =>
        text[..Math.Min(60, text.Length)].ReplaceLineEndings(" ");

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
    ///
    /// The same two names are asked of the site when the document came from
    /// there, in the same order. Nothing is tested for existence on that side:
    /// the lookup would be a second request per picture to answer a question the
    /// site has already answered by publishing the folder, and a picture that is
    /// missing leaves the caption underneath it, which still says what it was.
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

        if (_published)
        {
            return new Uri(Remote + (localized ?? relative));
        }

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
