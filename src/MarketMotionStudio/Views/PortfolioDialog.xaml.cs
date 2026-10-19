using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Automation;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;

namespace MarketMotionStudio.Views;

/// <summary>
/// Edits the book: add a holding by code, remove one, or correct the size and cost of one already
/// there.
///
/// <para>
/// **Edits are applied as they are made**, and there is one button, which closes. A dialog with
/// OK/Cancel would need a second copy of the book to hold the edits, and the only thing that buys
/// is the ability to abandon them — on a page whose whole subject is a list the reader is looking
/// at, abandoning an edit is what the delete button is for.
/// </para>
///
/// <para>
/// **The code is checked against the quote endpoint before it is stored.** A holding entered with
/// a typo would fail one fetch at a time for as long as it sat in the book, and the page would
/// look broken rather than mis-typed. The request also supplies the source's own name, so the
/// row can be recognised later in whatever language the interface is running in.
/// </para>
/// </summary>
public sealed partial class PortfolioDialog : ContentDialog
{
    public PortfolioDialog()
    {
        InitializeComponent();

        Title = Strings.Get("PortfolioDialogTitle");
        CloseButtonText = Strings.Get("PortfolioDialogClose");

        Portfolio.EnsureLoaded();

        Rebuild();
    }

    /// <summary>Draws the book, one row per holding.</summary>
    private void Rebuild()
    {
        Rows.Children.Clear();

        if (Portfolio.Holdings.Count == 0)
        {
            Rows.Children.Add(new TextBlock
            {
                Text = Strings.Get("PortfolioPnlEmpty"),
                TextWrapping = TextWrapping.Wrap,
                Style = (Style)Application.Current.Resources["CaptionTextBlockStyle"],
            });

            return;
        }

        foreach (var holding in Portfolio.Holdings.ToList())
        {
            Rows.Children.Add(Row(holding));
        }
    }

    /// <summary>
    /// One holding: the name over its code, the two numbers, and a delete button.
    ///
    /// The numbers are editable in place — a cost corrected after a split, or a share count that
    /// was entered wrong, is the ordinary reason to open this dialog, and making that a
    /// delete-and-re-add is how a book ends up with the wrong history.
    /// </summary>
    private UIElement Row(Holding holding)
    {
        var grid = new Grid
        {
            ColumnSpacing = 8,
            Padding = new Thickness(0, 4, 0, 4),
        };

        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var label = new StackPanel { Spacing = 1 };

        label.Children.Add(new TextBlock
        {
            Text = InstrumentNames.Display(holding.Code, holding.Name),
            TextTrimming = TextTrimming.CharacterEllipsis,
            Style = (Style)Application.Current.Resources["CaptionTextBlockStyle"],
        });

        label.Children.Add(new TextBlock
        {
            Text = holding.Code.ToUpperInvariant(),
            Style = (Style)Application.Current.Resources["CaptionTextBlockStyle"],
            Foreground = (Brush)Application.Current.Resources["TextFillColorSecondaryBrush"],
        });

        grid.Children.Add(label);

        var shares = new TextBox
        {
            Text = holding.Shares.ToString("0.##", CultureInfo.InvariantCulture),
            Width = 90,
            VerticalAlignment = VerticalAlignment.Center,
        };

        AutomationProperties.SetName(shares, Strings.Get("PortfolioDialogShares.PlaceholderText"));
        Grid.SetColumn(shares, 1);
        grid.Children.Add(shares);

        var cost = new TextBox
        {
            Text = holding.Cost.ToString("0.####", CultureInfo.InvariantCulture),
            Width = 90,
            VerticalAlignment = VerticalAlignment.Center,
        };

        AutomationProperties.SetName(cost, Strings.Get("PortfolioDialogCost.PlaceholderText"));
        Grid.SetColumn(cost, 2);
        grid.Children.Add(cost);

        // Written back on losing focus rather than on every keystroke: a text box being typed
        // into holds "1" of "1000" for a moment, and storing that would remove a holding.
        void Commit(object _, RoutedEventArgs __)
        {
            var size = Number(shares.Text);
            var price = Number(cost.Text);

            if (size <= 0 || price < 0)
            {
                return;
            }

            Portfolio.Put(new Holding(holding.Code, holding.Name, Math.Round(size, 4), Math.Round(price, 4)));
        }

        shares.LostFocus += Commit;
        cost.LostFocus += Commit;

        var remove = new Button
        {
            Content = new FontIcon { Glyph = "\uE74D", FontSize = 12 },
            VerticalAlignment = VerticalAlignment.Center,
            Padding = new Thickness(8),
        };

        AutomationProperties.SetName(remove, Strings.Format("PortfolioDialogRemove", holding.Code.ToUpperInvariant()));

        remove.Click += (_, _) =>
        {
            Portfolio.Remove(holding.Code);
            Rebuild();
        };

        Grid.SetColumn(remove, 3);
        grid.Children.Add(remove);

        return grid;
    }

    /// <summary>Adds what was typed, if it names something the source will quote.</summary>
    private async void OnAdd(object sender, RoutedEventArgs e)
    {
        AddButton.IsEnabled = false;

        try
        {
            var code = Normalize(CodeBox.Text);
            var shares = Number(SharesBox.Text);
            var cost = Number(CostBox.Text);

            if (code is null)
            {
                Say(Strings.Get("PortfolioDialogBadCode"));
                return;
            }

            if (shares <= 0 || cost < 0)
            {
                Say(Strings.Get("PortfolioDialogBadNumbers"));
                return;
            }

            Say(Strings.Get("PortfolioDialogChecking"));

            StockSnapshot? shot;

            try
            {
                var found = await AppServices.Current.Stocks.SnapshotsAsync([code], CancellationToken.None);

                found.TryGetValue(code, out shot);
            }
            catch (Exception ex)
            {
                Say(Strings.Reason(ex));
                return;
            }

            if (shot is null || shot.Name.Length == 0)
            {
                Say(Strings.Format("PortfolioDialogUnknown", code.ToUpperInvariant()));
                return;
            }

            Portfolio.Put(new Holding(code, shot.Name, Math.Round(shares, 4), Math.Round(cost, 4)));

            CodeBox.Text = string.Empty;
            SharesBox.Text = string.Empty;
            CostBox.Text = string.Empty;
            Message.Visibility = Visibility.Collapsed;

            Rebuild();
        }
        finally
        {
            AddButton.IsEnabled = true;
        }
    }

    private void Say(string message)
    {
        Message.Text = message;
        Message.Visibility = Visibility.Visible;
    }

    private static double Number(string text) =>
        double.TryParse(text.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out var value)
            ? value
            : 0;

    /// <summary>
    /// Turns what a reader types into a code the quote endpoint answers to.
    ///
    /// The whole point is that they should not have to know which prefix a venue uses: `300036`
    /// and `sz300036` are the same listing, and a Hong Kong code is five digits with or without
    /// its `hk`. The six-digit mainland numbers are assigned to an exchange by their first digit
    /// — 6 Shanghai, 0 and 3 Shenzhen, 4 and 8 Beijing — which is the same rule
    /// <c>TradeText</c> applies to an imported row, deliberately: two rules would let a holding
    /// typed here and the same holding imported there become two positions.
    /// </summary>
    public static string? Normalize(string raw)
    {
        var text = raw.Trim().ToLowerInvariant().Replace(" ", string.Empty).Replace(".", string.Empty);

        if (text.StartsWith("hk", StringComparison.Ordinal))
        {
            var digits = text[2..];

            return digits.Length is 4 or 5 && digits.All(char.IsDigit) ? "hk" + digits.PadLeft(5, '0') : null;
        }

        if (text.StartsWith("sh", StringComparison.Ordinal) ||
            text.StartsWith("sz", StringComparison.Ordinal) ||
            text.StartsWith("bj", StringComparison.Ordinal))
        {
            return text.Length == 8 && text[2..].All(char.IsDigit) ? text : null;
        }

        if (!text.All(char.IsDigit))
        {
            return null;
        }

        return text.Length switch
        {
            6 => text[0] switch
            {
                '6' => "sh" + text,
                '0' or '3' => "sz" + text,
                '4' or '8' => "bj" + text,
                _ => null,
            },
            4 or 5 => "hk" + text.PadLeft(5, '0'),
            _ => null,
        };
    }
}
