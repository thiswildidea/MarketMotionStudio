using AShareMotionStudio.Localization;
using AShareMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace AShareMotionStudio.Views;

/// <summary>
/// The video parameters both indicator pages offer, in one control.
///
/// It owns no data and produces no picture. It reports a
/// <see cref="VideoFormat"/>, a <see cref="ChartMargins"/> and a duration, and
/// raises <see cref="Changed"/> when any of them moves; the page decides what that
/// means, which is always "redraw the preview" and is not this control's business
/// to assume.
/// </summary>
public sealed partial class VideoSettingsPanel : UserControl
{
    /// <summary>
    /// Raised when any parameter changes. One event rather than one per control:
    /// every consumer so far does the same thing for all of them, and a set of
    /// narrower events would be an invitation to handle three and forget the
    /// fourth.
    /// </summary>
    public event EventHandler? Changed;

    /// <summary>
    /// Guards the population of the combo boxes.
    ///
    /// Raised before the first assignment rather than after the defaults are set.
    /// A flag only protects the assignments that come after it, and adding an item
    /// to a combo box selects it — so setting defaults first and raising the flag
    /// second lets the first selection through, which on a page that persists this
    /// would save a default over the value being restored.
    /// </summary>
    private bool _loading = true;

    public VideoSettingsPanel()
    {
        InitializeComponent();

        foreach (var (width, height) in VideoFormat.Sizes)
        {
            // Not translated: it is two numbers and a multiplication sign.
            ResolutionCombo.Items.Add(new ComboBoxItem { Content = $"{width} × {height}", Tag = (width, height) });
        }

        ResolutionCombo.SelectedIndex = 1;

        // Thirty and sixty only. The intermediate rates are not offered by the
        // platforms this targets and a rate they re-encode is a rate that cost
        // bits for nothing.
        int[] rates = [30, 60];

        foreach (var fps in rates)
        {
            FrameRateCombo.Items.Add(new ComboBoxItem { Content = $"{fps} fps", Tag = fps });
        }

        FrameRateCombo.SelectedIndex = 0;

        foreach (var (quality, key) in Qualities)
        {
            QualityCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = quality });
        }

        QualityCombo.SelectedIndex = 1;

        var margins = ChartMargins.Default;
        MarginLeftSlider.Value = margins.Left;
        MarginRightSlider.Value = margins.Right;
        MarginBottomSlider.Value = margins.Bottom;

        _loading = false;

        RefreshLabels();
    }

    /// <summary>
    /// Offers the hide-title switch. Off for the whole-market chart, which has no
    /// instrument name to keep out of frame.
    /// </summary>
    public bool AllowHideTitle
    {
        get => HideTitleGroup.Visibility == Visibility.Visible;
        set => HideTitleGroup.Visibility = value ? Visibility.Visible : Visibility.Collapsed;
    }

    /// <summary>
    /// What to show in the title box when it is empty — the default the page would
    /// use. Set by the page, because "empty" means a fixed string on one indicator
    /// and the fetched instrument's name on the other.
    /// </summary>
    public string TitlePlaceholder
    {
        get => TitleBox.PlaceholderText;
        set => TitleBox.PlaceholderText = value;
    }

    /// <summary>The typed title, or empty to mean "use the default".</summary>
    public string TitleText => TitleBox.Text.Trim();

    /// <summary>
    /// Whether the title is drawn. Always true unless the page offered the switch
    /// and it was turned on — a hidden switch must not be able to suppress a title.
    /// </summary>
    public bool ShowTitle => !(AllowHideTitle && HideTitleToggle.IsOn);

    private static readonly (VideoFormat.Quality Quality, string Key)[] Qualities =
    [
        (VideoFormat.Quality.Standard, "StudioQualityStandard"),
        (VideoFormat.Quality.High, "StudioQualityHigh"),
        (VideoFormat.Quality.Ultra, "StudioQualityUltra"),
    ];

    public TimeSpan Duration => TimeSpan.FromSeconds(DurationSlider.Value);

    public bool ShowGuides => GuidesToggle.IsOn;

    public ChartMargins Margins =>
        new(MarginLeftSlider.Value, MarginRightSlider.Value, MarginBottomSlider.Value);

    /// <summary>
    /// Puts back what this panel was last set to, for the page that owns it.
    ///
    /// The panel does not hold the preferences itself: it is one control used by two indicators, and
    /// whose settings it is reading is the page's business. Passing the store in is what keeps the
    /// two pages from sharing one set of margins.
    /// </summary>
    public void Restore(Pages.StudioPreferences prefs)
    {
        _loading = true;

        DurationSlider.Value = prefs.GetDouble("Duration", DurationSlider.Value);

        var size = prefs.GetInt("Resolution", 1);
        ResolutionCombo.SelectedIndex = size >= 0 && size < ResolutionCombo.Items.Count ? size : 1;

        var rate = prefs.GetInt("FrameRate", 0);
        FrameRateCombo.SelectedIndex = rate >= 0 && rate < FrameRateCombo.Items.Count ? rate : 0;

        var quality = prefs.GetInt("Quality", 1);
        QualityCombo.SelectedIndex = quality >= 0 && quality < QualityCombo.Items.Count ? quality : 1;

        var margins = ChartMargins.Default;
        MarginLeftSlider.Value = prefs.GetDouble("MarginLeft", margins.Left);
        MarginRightSlider.Value = prefs.GetDouble("MarginRight", margins.Right);
        MarginBottomSlider.Value = prefs.GetDouble("MarginBottom", margins.Bottom);

        TitleBox.Text = prefs.GetString("Title", string.Empty);
        GuidesToggle.IsOn = prefs.GetBool("Guides", false);
        HideTitleToggle.IsOn = prefs.GetBool("HideTitle", false);

        _loading = false;

        RefreshLabels();
    }

    /// <summary>Records the current settings. Called by the page when anything changes.</summary>
    public void Save(Pages.StudioPreferences prefs)
    {
        prefs.Save("Duration", DurationSlider.Value);
        prefs.Save("Resolution", ResolutionCombo.SelectedIndex);
        prefs.Save("FrameRate", FrameRateCombo.SelectedIndex);
        prefs.Save("Quality", QualityCombo.SelectedIndex);
        prefs.Save("MarginLeft", MarginLeftSlider.Value);
        prefs.Save("MarginRight", MarginRightSlider.Value);
        prefs.Save("MarginBottom", MarginBottomSlider.Value);
        prefs.Save("Title", TitleBox.Text);
        prefs.Save("Guides", GuidesToggle.IsOn);
        prefs.Save("HideTitle", HideTitleToggle.IsOn);
    }

    public VideoFormat Format
    {
        get
        {
            var (width, height) = ResolutionCombo.SelectedItem is ComboBoxItem { Tag: ValueTuple<int, int> size }
                ? size
                : (VideoFormat.BaselineWidth, VideoFormat.BaselineHeight);

            var fps = FrameRateCombo.SelectedItem is ComboBoxItem { Tag: int rate } ? rate : 30;

            var quality = QualityCombo.SelectedItem is ComboBoxItem { Tag: VideoFormat.Quality chosen }
                ? chosen
                : VideoFormat.Quality.High;

            return VideoFormat.Create(width, height, fps, quality);
        }
    }

    private void OnDurationChanged(object sender, RangeBaseValueChangedEventArgs e) => Announce();

    private void OnMarginChanged(object sender, RangeBaseValueChangedEventArgs e) => Announce();

    private void OnFormatChanged(object sender, SelectionChangedEventArgs e) => Announce();

    private void OnGuidesToggled(object sender, Microsoft.UI.Xaml.RoutedEventArgs e) => Announce();

    /// <summary>
    /// Every keystroke redraws. The title is the element most likely to be too long,
    /// and it is shrunk to fit — so seeing the size give way as you type is the
    /// feedback that tells you to shorten it.
    /// </summary>
    private void OnTitleChanged(object sender, TextChangedEventArgs e) => Announce();

    private void OnHideTitleToggled(object sender, Microsoft.UI.Xaml.RoutedEventArgs e) => Announce();

    private void Announce()
    {
        if (_loading)
        {
            return;
        }

        RefreshLabels();
        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>
    /// Puts the current value into each slider's own label.
    ///
    /// A slider with no read-out is a control whose value can only be guessed from
    /// the position of the thumb, and these are values people compare between
    /// sessions — "the bottom margin was 480 last time" is a thing someone
    /// remembers and cannot re-enter from a thumb.
    /// </summary>
    private void RefreshLabels()
    {
        DurationLabel.Text = Strings.Format("StudioDuration", (int)DurationSlider.Value);
        MarginLeftLabel.Text = Strings.Format("StudioMarginLeft", (int)MarginLeftSlider.Value);
        MarginRightLabel.Text = Strings.Format("StudioMarginRight", (int)MarginRightSlider.Value);
        MarginBottomLabel.Text = Strings.Format("StudioMarginBottom", (int)MarginBottomSlider.Value);

        // Rounded to one decimal. The exact figure is a product of three controls
        // and reads as spurious precision; what it is here to answer is "roughly
        // how heavy will the file be".
        BitrateText.Text = Strings.Format("StudioBitrate", (Format.BitsPerSecond / 1_000_000.0).ToString("0.0"));
    }
}
