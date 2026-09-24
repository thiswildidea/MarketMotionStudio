using AShareMotionStudio.Localization;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace AShareMotionStudio.Pages;

/// <summary>
/// The manual, in whichever of the fourteen languages the interface is showing.
///
/// Not a <see cref="StudioPage"/>: it fetches nothing, renders nothing and exports
/// nothing, and giving it the machinery for reporting long work would be describing
/// the base class rather than this page.
/// </summary>
public sealed partial class HelpPage : Page
{
    public HelpPage()
    {
        InitializeComponent();
        Loaded += OnPageLoaded;
    }

    /// <summary>
    /// Loaded once. The language cannot change without a restart — <c>x:Uid</c> is
    /// resolved when XAML loads and never re-read — so re-reading the file on a
    /// later visit would re-read the same file.
    /// </summary>
    private bool _shown;

    private async void OnPageLoaded(object sender, RoutedEventArgs e)
    {
        if (_shown)
        {
            return;
        }

        _shown = true;

        // The resources name the file, so it is chosen by the same resolution that
        // chose every other string on this screen — including all of its fallback
        // rules. Working the language out separately would be a second answer to a
        // question already answered, free to disagree with the first, which is how a
        // Japanese window ends up with an English manual.
        var text = await HelpDocument.LoadAsync(Strings.Get("HelpDocument"));

        if (text is null)
        {
            // Said plainly rather than left blank. A help page that renders nothing
            // looks like a page that failed to load, which it is — but only saying
            // so turns it into something reportable.
            Document.Children.Add(new TextBlock
            {
                Text = Strings.Get("HelpMissing"),
                TextWrapping = TextWrapping.Wrap,
                Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["SystemFillColorCautionBrush"],
            });

            return;
        }

        HelpDocument.Render(text, Document);
    }
}
