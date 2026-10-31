using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Pages;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.UI;

namespace MarketMotionStudio.Views;

/// <summary>
/// The title row every page carries: a badge that shows the merged headline, one gear that opens
/// a dialog per subject (main title, subtitle), and the hide-title switch under them. It is the
/// real-time-holdings page's title controls, lifted out into a control every page drops in.
///
/// The two-layer rule lives in <see cref="TitleStyle.Merge"/>; this panel only reads and writes
/// the page's own (partial) records and shows the merged result. A field the page never set is
/// null in its record, so the merge with the settings page's global defaults answers it — which
/// is how one global choice reaches every page and a page's own choice still wins.
/// </summary>
public sealed partial class TitlePanel : UserControl
{
    private TitleStyle _mainStyle = new();
    private TitleStyle _subStyle = new();
    private string _subtitleText = string.Empty;
    private bool _showSubtitle = true;

    /// <summary>Raised when any local choice changes — the page rebuilds its renderer and saves.</summary>
    public event EventHandler? Changed;

    public TitlePanel()
    {
        InitializeComponent();

        var gearTip = Strings.Get("PortfolioPnlTitleEdit.Text");

        ToolTipService.SetToolTip(Gear, gearTip);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(Gear, gearTip);

        // 全局样式改了，本地没配置的项要跟着变：徽章照合并结果重画。
        TitleSettings.Changed += (_, _) => RefreshBadge();
    }

    /// <summary>The page's own main-title choices. The renderer passes this to
    /// <c>new TitleBlock(size, MainStyle, () =&gt; TitleSettings.MainStyle)</c>.</summary>
    public TitleStyle MainStyle => _mainStyle;

    /// <summary>The page's own subtitle choices, on the same terms.</summary>
    public TitleStyle SubtitleStyle => _subStyle;

    /// <summary>What the subtitle says. Empty draws nothing.</summary>
    public string SubtitleText => _subtitleText;

    /// <summary>Whether the subtitle is drawn at all.</summary>
    public bool ShowSubtitle => _showSubtitle;

    /// <summary>Whether the headline is hidden on the canvas (the switch under the badge).</summary>
    public bool HideTitle => HideToggle.IsOn;

    private string _titleText = string.Empty;

    /// <summary>The headline text the badge previews with — the page sets this to its own
    /// resolved title (the typed text, or the page's default).</summary>
    public string TitleText
    {
        get => _titleText;
        set
        {
            _titleText = value ?? string.Empty;
            RefreshBadge();
        }
    }

    /// <summary>Reads the page's stored choices. Call before the page reads any of them.</summary>
    public void Restore(StudioPreferences prefs)
    {
        var styleJson = prefs.GetString("TitleStyle", string.Empty);

        if (styleJson.Length > 0)
        {
            _mainStyle = TitleStyle.FromJson(styleJson);
        }
        else
        {
            // 旧键迁移：旧的样式序号与颜色是本地选择，不是「未配置」。
            _mainStyle = new TitleStyle
            {
                Skin = prefs.GetInt("TitleSkin", 0),
                Colour = NullIfEmpty(prefs.GetString("TitleColour", string.Empty)),
            };
        }

        _subStyle = TitleStyle.FromJson(prefs.GetString("SubtitleStyle", string.Empty));
        _showSubtitle = prefs.GetBool("ShowSubtitle", true);
        _subtitleText = prefs.GetString("SubtitleText", string.Empty);
        HideToggle.IsOn = prefs.GetBool("PnlHideTitle", prefs.GetBool("HideTitle", false));

        RefreshBadge();
    }

    /// <summary>Writes the page's choices. Call from the page's own save path.</summary>
    public void Save(StudioPreferences prefs)
    {
        prefs.Save("TitleStyle", _mainStyle.ToJson());
        prefs.Save("SubtitleStyle", _subStyle.ToJson());
        prefs.Save("SubtitleText", _subtitleText);
        prefs.Save("ShowSubtitle", _showSubtitle);
        prefs.Save("PnlHideTitle", HideToggle.IsOn);
    }

    private static string? NullIfEmpty(string value) => value.Length == 0 ? null : value;

    private async void OnEditMainTitle(object sender, RoutedEventArgs e)
    {
        if (XamlRoot is null)
        {
            return;
        }

        var dialog = new TitleStyleDialog(
            subtitle: false,
            _mainStyle,
            titleText: TitleText)
        { XamlRoot = XamlRoot };

        if (await Dialogs.ShowAsync(dialog) != ContentDialogResult.Primary)
        {
            return;
        }

        _mainStyle = dialog.Chosen;
        TitleText = dialog.TitleTextValue;

        RefreshBadge();
        Changed?.Invoke(this, EventArgs.Empty);
    }

    private async void OnEditSubtitle(object sender, RoutedEventArgs e)
    {
        if (XamlRoot is null)
        {
            return;
        }

        var dialog = new TitleStyleDialog(
            subtitle: true,
            _subStyle,
            _subtitleText,
            _showSubtitle)
        { XamlRoot = XamlRoot };

        if (await Dialogs.ShowAsync(dialog) != ContentDialogResult.Primary)
        {
            return;
        }

        _subStyle = dialog.Chosen;
        _subtitleText = dialog.SubtitleText;
        _showSubtitle = dialog.ShowSubtitle;

        RefreshBadge();
        Changed?.Invoke(this, EventArgs.Empty);
    }

    private void OnHideToggled(object sender, RoutedEventArgs e)
    {
        RefreshBadge();
        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>Redraws the badge from the merged result — the page's own choices over the
    /// settings page's defaults — because that is what the canvas draws.</summary>
    private void RefreshBadge()
    {
        var merged = TitleStyle.Merge(_mainStyle, TitleSettings.MainStyle);

        BadgeText.Text = TitleText;

        if (merged.Font is { } font)
        {
            BadgeText.FontFamily = new FontFamily(font);
        }

        // 徽章在浅色页面，Plain 的默认色（画布白）看不见：读者的颜色优先，渐变样式用其主色，
        // Plain 留主题墨色。
        var ink = merged.ParsedColour()
            ?? (merged.Skin is { } skin && (TitleSkin)skin is not TitleSkin.Plain
                ? TitleSkins.Default((TitleSkin)skin)
                : null);

        BadgeText.Foreground = ink is { } colour ? new SolidColorBrush(colour) : null;

        var spin = merged.Rotation ?? 0;

        BadgeText.RenderTransform = spin == 0
            ? null
            : new RotateTransform { Angle = spin };

        var sub = _showSubtitle ? _subtitleText : string.Empty;

        BadgeSub.Text = sub.ReplaceLineEndings(" ");
        BadgeSub.Visibility = sub.Length > 0 ? Visibility.Visible : Visibility.Collapsed;
    }
}
