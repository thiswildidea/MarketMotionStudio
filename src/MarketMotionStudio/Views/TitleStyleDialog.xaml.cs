using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Xaml.Media;
using Windows.UI;

namespace MarketMotionStudio.Views;

/// <summary>
/// The main title's or the subtitle's own style, asked for in a dialog instead of lived in
/// on the page.
///
/// <para>
/// The page keeps a badge and a gear; this is where the gear goes. One class for both
/// subjects because their fields are the same list with one exception each way — the main
/// title spins and the subtitle does not, the subtitle says something and the main title
/// does not (the headline text lives in the video panel, shared with every page) — and two
/// dialogs that differed by a row would be two copies of one form to keep in step.
/// </para>
///
/// <para>
/// **A field left on 「跟随全局」 is a field the record does not name.** That is the whole
/// of the two-layer mechanism: the dialog reads the page's own record in, hands back a new
/// one whose unset fields are null, and the merge with the settings page's defaults happens
/// at draw time inside <see cref="TitleBlock"/>. The dialog never needs to know what the
/// global answer is — except for the badge at the top, which shows the *merged* result,
/// because that is what will actually be drawn.
/// </para>
/// </summary>
public sealed partial class TitleStyleDialog : ContentDialog
{
    /// <summary>True while the dialog is setting the picker's own colour, so the change it
    /// raises on itself is not read back as a choice.</summary>
    private bool _painting;

    /// <summary>The colour the reader picked, as <c>#RRGGBB</c>; empty means "whichever the
    /// treatment comes with".</summary>
    private string _colour = string.Empty;

    /// <summary>Which subject the dialog is editing: the subtitle gains the text and the
    /// show switch, and loses the rotation row.</summary>
    private readonly bool _subtitle;

    /// <summary>The style as handed in, kept so closing with the close button is a real
    /// refusal: the page keeps what it had. Called <c>Chosen</c> rather than <c>Style</c> —
    /// the latter is <see cref="FrameworkElement"/>'s own property, and shadowing it is a
    /// warning, not a feature.</summary>
    public TitleStyle Chosen { get; private set; } = new();

    /// <summary>The headline's own text, canonicalised the way the panel canonicalises it.
    /// Only read under the main-title subject.</summary>
    public string TitleTextValue { get; private set; } = string.Empty;

    /// <summary>What the subtitle says. Only read under the subtitle subject.</summary>
    public string SubtitleText { get; private set; } = string.Empty;

    /// <summary>Whether the subtitle is drawn. Only read under the subtitle subject.</summary>
    public bool ShowSubtitle { get; private set; } = true;

    /// <summary>
    /// Opens the dialog on one subject.
    /// </summary>
    /// <param name="subtitle">False for the main title, true for the subtitle.</param>
    /// <param name="style">The page's own record as it stands — its unset fields are the
    /// ones the dialog shows as 「跟随全局」.</param>
    /// <param name="subtitleText">What the subtitle says, under the subtitle subject.</param>
    /// <param name="showSubtitle">Whether the subtitle is drawn, under the same subject.</param>
    /// <param name="titleText">What the headline says, under the main-title subject — the
    /// dialog is the headline's editor now, so it opens on the text as it stands.</param>
    /// <param name="titlePlaceholder">What the headline's box offers when empty — the page's
    /// own default, the same words the video panel shows.</param>
    public TitleStyleDialog(
        bool subtitle,
        TitleStyle style,
        string subtitleText = "",
        bool showSubtitle = true,
        string titleText = "",
        string? titlePlaceholder = null)
    {
        InitializeComponent();

        _subtitle = subtitle;
        Chosen = style;

        Title = Strings.Get(subtitle ? "PortfolioPnlSubtitleDialog" : "PortfolioPnlTitleDialog");
        CloseButtonText = Strings.Get("PortfolioDialogClose");
        PrimaryButtonText = Strings.Get("PortfolioPnlStyleOk");

        SkinCombo.Header = Strings.Get("PortfolioPnlTitleSkin.Header");
        FontCombo.Header = Strings.Get(
            subtitle ? "PortfolioPnlSubtitleFont.Header" : "PortfolioPnlTitleFont.Header");
        SizeLabel.Text = Strings.Get(
            subtitle ? "PortfolioPnlSubtitleSize.Header" : "PortfolioPnlTitleSize.Header");
        SizeFollow.Content = Strings.Get("PortfolioPnlFollowGlobal.Content");
        LinesCombo.Header = Strings.Get(
            subtitle ? "PortfolioPnlSubtitleLines.Header" : "PortfolioPnlTitleLines.Header");

        RotationLabel.Text = Strings.Get("PortfolioPnlTitleRotation.Header");
        RotationFollow.Content = Strings.Get("PortfolioPnlFollowGlobal.Content");

        ColourLabel.Text = Strings.Get(
            subtitle ? "PortfolioPnlSubtitleColour.Text" : "PortfolioPnlTitleColour.Text");
        ColourDefault.Content = Strings.Get("PortfolioPnlTitleColourDefault.Content");

        ShowCheck.Content = Strings.Get("PortfolioPnlShowSubtitle.Content");
        SubTextBox.PlaceholderText = Strings.Get("PortfolioPnlSubtitleText.PlaceholderText");

        FillSkinCombo(SkinCombo);
        FillFontCombo(FontCombo);
        FillLinesCombo(LinesCombo);

        SkinCombo.SelectedIndex = style.Skin is { } skin
            ? Math.Max(0, IndexOfTag(SkinCombo, skin))
            : 0;
        FontCombo.SelectedIndex = style.Font is { } font
            ? Math.Max(0, IndexOfTag(FontCombo, font))
            : 0;
        SizeFollow.IsChecked = style.Size is null;
        SizeSlider.Value = style.Size ?? 62;
        SizeSlider.IsEnabled = SizeFollow.IsChecked is not true;
        LinesCombo.SelectedIndex = style.MaxLines is { } lines
            ? Math.Max(0, IndexOfTag(LinesCombo, lines))
            : 0;
        _colour = style.Colour ?? string.Empty;

        RotationGroup.Visibility = subtitle ? Visibility.Collapsed : Visibility.Visible;
        RotationFollow.IsChecked = style.Rotation is null;
        RotationSlider.Value = style.Rotation ?? 0;

        SubtitleGroup.Visibility = subtitle ? Visibility.Visible : Visibility.Collapsed;
        TitleTextBox.Visibility = subtitle ? Visibility.Collapsed : Visibility.Visible;

        if (subtitle)
        {
            ShowCheck.IsChecked = showSubtitle;
            SubTextBox.Text = subtitleText;
        }
        else
        {
            TitleTextBox.Header = Strings.Get("StudioTitleText.Header");

            if (titlePlaceholder is { } placeholder)
            {
                TitleTextBox.PlaceholderText = placeholder;
            }

            TitleTextBox.Text = titleText;
        }

        PaintPicker();
        PaintPreview();
    }

    /// <summary>The style as the dialog reads right now — nulls where 「跟随全局」 is on.</summary>
    private TitleStyle Current() => new()
    {
        Skin = TagOf(SkinCombo),
        Font = TagText(FontCombo),
        Size = SizeFollow.IsChecked is true ? null : SizeSlider.Value,
        Colour = _colour.Length == 0 ? null : _colour,
        MaxLines = TagOf(LinesCombo),
        Rotation = _subtitle
            ? null
            : RotationFollow.IsChecked is true ? null : RotationSlider.Value,
    };

    /// <summary>Redraws the badge inside the dialog: the merged result, because that is
    /// what the page will draw once the dialog closes. The preview draws through the frame's
    /// own renderer now, so it is handed the page's own (partial) style and the text — the
    /// merge with the global default happens inside the preview, exactly as it will on the
    /// page.</summary>
    private void PaintPreview()
    {
        var text = _subtitle ? SubTextBox.Text : TitleTextBox.Text;

        Preview.Subtitle = _subtitle;
        Preview.Chosen = Current();
        Preview.Text = text.Length > 0
            ? text
            : Strings.Get("PortfolioPnlTitleBadge");

        RotationValue.Text = RotationFollow.IsChecked is true
            ? "—"
            : string.Create(CultureInfo.InvariantCulture, $"{RotationSlider.Value:0}°");

        SizeValue.Text = SizeFollow.IsChecked is true
            ? "—"
            : string.Create(CultureInfo.InvariantCulture, $"{SizeSlider.Value:0}");
    }

    private void OnComboChanged(object sender, SelectionChangedEventArgs e) => PaintPreview();

    private void OnValueChanged(object sender, RoutedEventArgs e) => PaintPreview();

    private void OnSizeChanged(object sender, RangeBaseValueChangedEventArgs e) => PaintPreview();

    private void OnRotationFollowChanged(object sender, RoutedEventArgs e)
    {
        RotationSlider.IsEnabled = RotationFollow.IsChecked is not true;
        PaintPreview();
    }

    private void OnSizeFollowChanged(object sender, RoutedEventArgs e)
    {
        SizeSlider.IsEnabled = SizeFollow.IsChecked is not true;
        PaintPreview();
    }

    private void OnColourChanged(ColorPicker sender, ColorChangedEventArgs args)
    {
        if (_painting)
        {
            return;
        }

        var ink = args.NewColor;

        _colour = string.Format(
            CultureInfo.InvariantCulture, "#{0:X2}{1:X2}{2:X2}", ink.R, ink.G, ink.B);

        PaintSwatch();
        PaintPreview();
    }

    private void OnColourDefault(object sender, RoutedEventArgs e)
    {
        _colour = string.Empty;

        PaintPicker();
        PaintPreview();
    }

    private TitleSkin ChosenSkin() =>
        TagOf(SkinCombo) is { } tag ? (TitleSkin)tag : TitleSkin.Plain;

    private Color? ChosenColour()
    {
        var hex = _colour;

        if (hex.Length != 7 || hex[0] != '#')
        {
            return null;
        }

        return byte.TryParse(hex[1..3], NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var r)
            && byte.TryParse(hex[3..5], NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var g)
            && byte.TryParse(hex[5..7], NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var b)
            ? Color.FromArgb(255, r, g, b)
            : null;
    }

    /// <summary>An unpicked colour shows the treatment's own default, so "use the default"
    /// is a visible state rather than an absence.</summary>
    private void PaintSwatch() =>
        Swatch.Fill = new SolidColorBrush(ChosenColour() ?? TitleSkins.Default(ChosenSkin()));

    private void PaintPicker()
    {
        _painting = true;

        ColourPicker.Color = ChosenColour() ?? TitleSkins.Default(ChosenSkin());

        _painting = false;
        PaintSwatch();
    }

    /// <summary>The treatment menu, 「跟随全局」 first: a Tag of -1 reads as a field the
    /// record does not name, which is the whole of the fallback.</summary>
    private static void FillSkinCombo(ComboBox combo)
    {
        combo.Items.Add(new ComboBoxItem
        {
            Content = Strings.Get("PortfolioPnlFollowGlobal.Content"),
            Tag = -1,
        });

        foreach (var (skin, key) in Skins)
        {
            combo.Items.Add(new ComboBoxItem
            {
                Content = Strings.Get(key),
                Tag = (int)skin,
            });
        }
    }

    private static void FillFontCombo(ComboBox combo)
    {
        combo.Items.Add(new ComboBoxItem
        {
            Content = Strings.Get("PortfolioPnlFollowGlobal.Content"),
            Tag = "",
        });

        foreach (var (family, label) in TitleSettings.Fonts[1..])
        {
            combo.Items.Add(new ComboBoxItem
            {
                Content = $"{label}  ({family})",
                Tag = family,
            });
        }
    }

    private static void FillLinesCombo(ComboBox combo)
    {
        combo.Items.Add(new ComboBoxItem
        {
            Content = Strings.Get("PortfolioPnlFollowGlobal.Content"),
            Tag = -1,
        });

        foreach (var lines in new[] { 1, 2, 3 })
        {
            combo.Items.Add(new ComboBoxItem
            {
                Content = lines.ToString(CultureInfo.InvariantCulture),
                Tag = lines,
            });
        }
    }

    /// <summary>The headline treatments, with the keys their menu items read by.</summary>
    private static readonly (TitleSkin Skin, string Key)[] Skins =
    [
        (TitleSkin.Plain, "PortfolioPnlTitlePlain.Content"),
        (TitleSkin.Gilded, "PortfolioPnlTitleGilded.Content"),
        (TitleSkin.Engraved, "PortfolioPnlTitleEngraved.Content"),
        (TitleSkin.Fire, "PortfolioPnlTitleFire.Content"),
        (TitleSkin.Aurum, "PortfolioPnlTitleAurum.Content"),
        (TitleSkin.Ink, "PortfolioPnlTitleInk.Content"),
        (TitleSkin.Neon, "PortfolioPnlTitleNeon.Content"),
    ];

    /// <summary>A combo's whole-number tag, or null for 「跟随全局」.</summary>
    private static int? TagOf(ComboBox combo) =>
        combo.SelectedItem is ComboBoxItem { Tag: int tag } && tag >= 0 ? tag : null;

    /// <summary>A combo's string tag — a font family — or null for 「跟随全局」.</summary>
    private static string? TagText(ComboBox combo) =>
        combo.SelectedItem is ComboBoxItem { Tag: string family } && family.Length > 0 ? family : null;

    /// <summary>Which item of a combo carries this tag, or none.</summary>
    private static int IndexOfTag(ComboBox combo, object? tag) =>
        combo.Items.OfType<ComboBoxItem>().ToList().FindIndex(item => Equals(item.Tag, tag));

    private void OnPrimaryClick(ContentDialog sender, ContentDialogButtonClickEventArgs args)
    {
        Chosen = Current();

        if (_subtitle)
        {
            SubtitleText = SubTextBox.Text;
            ShowSubtitle = ShowCheck.IsChecked is true;
        }
        else
        {
            // The same canonicalisation the panel applies when reading its own box: typed
            // breaks arrive as \r, pasted ones as \r\n, and the persisted copy wants \n.
            TitleTextValue = TitleTextBox.Text.Trim().Replace("\r\n", "\n").Replace('\r', '\n');
        }
    }
}
