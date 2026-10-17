using System.Linq;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// One coin's monthly returns as a year × month grid — the coin-market reading of the
/// share market's monthly matrix, drawing the same <see cref="MatrixSpec"/> through the
/// same <see cref="MatrixRenderer"/>.
///
/// Nothing about the grid is new: the renderer, the spec builder and the compound
/// arithmetic are the share page's own, and this page is a loader plus a set of choices.
/// What is the coin market's own is the loader — no monthly endpoint answers about a coin,
/// so the months are folded out of the daily bars the chart pages already draw (see
/// <see cref="CryptoMonthly"/>) — and the year list, which stops at ten because ten years
/// of days is the ceiling of the daily source itself, not a number somebody liked.
///
/// **One coin, not several.** The share page's other reading puts several instruments'
/// recent months side by side, and a coin version of it would be the same page with a
/// different roster. It is not built yet: the single-coin grid is the reading people
/// asked for, and a grid of fourteen coins' twelve recent months is a different frame
/// with different decisions in it — better to build it when someone wants it than to
/// ship it half-thought-of here.
///
/// **The years are a reading, not a fetch.** The whole span the source holds is walked
/// once; the year count filters months when the spec is built, so changing it redraws
/// without a second decade of requests.
/// </summary>
public sealed partial class CryptoMonthlyMatrixPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("CryptoMatrix.");

    /// <summary>The years the grid can cover: ten is the daily source's own ceiling, so
    /// there is no "all" entry — the longest honest answer is already the last one.</summary>
    private static readonly int[] YearChoices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

    /// <summary>The fetched months, oldest first, across the whole span the source holds.</summary>
    private IReadOnlyList<MonthlyPoint>? _series;

    /// <summary>The coin the series was fetched for, so a coin switch can retire it.</summary>
    private CryptoAsset? _fetchedFor;

    /// <summary>The grid drawn from the series under the current year count.</summary>
    private MatrixSpec? _spec;

    /// <summary>Whether the page is finished being built; see the handlers that read it.</summary>
    private bool _ready;

    public CryptoMonthlyMatrixPage()
    {
        InitializeComponent();

        foreach (var years in YearChoices)
        {
            YearsCombo.Items.Add(new ComboBoxItem
            {
                Content = years.ToString(System.Globalization.CultureInfo.InvariantCulture),
                Tag = years,
            });
        }

        YearsCombo.SelectedIndex = YearChoices.Length - 1;

        // One coin at a time. A second press on the row is refused rather than trimming
        // something else — see the picker's own note on why a limit is a refusal.
        Coins.Limit = 1;

        // A pick added or removed retires the months that were fetched for the old coin:
        // a grid still showing one coin's months under a row that names another is a grid
        // about a choice nobody made.
        Coins.Changed += OnCoinsChanged;

        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(YearsCombo, "CryptoMatrixYears");

        VideoSettings.AllowHideTitle = true;
        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            VideoSettings.Save(_prefs);
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        // Named before it has ever been pressed: the button is an icon, so the tooltip
        // and the name a screen reader announces are the only words it has.
        SetPlaybackState(playing: false);

        RestorePreferences();
        ApplyPreviewSettings();

        _ready = true;
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("CryptoMatrixPageTitle.Text");

    /// <summary>
    /// The coin on the frame, read off the picker rather than kept here — a page that
    /// kept its own copy would be a second place the same choice is kept.
    /// </summary>
    private CryptoAsset? Chosen() =>
        Coins.Selected.Select(entry => CryptoAsset.Of(entry.Code)).OfType<CryptoAsset>().FirstOrDefault();

    private int ChosenYears() =>
        YearsCombo.SelectedItem is ComboBoxItem { Tag: int years } ? years : YearChoices[^1];

    // ---- preview -----------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_spec is { } spec)
        {
            Preview.Renderer = new MatrixRenderer(spec, VideoSettings.Duration)
            {
                Title = VideoSettings.TitleText,
                ShowTitle = VideoSettings.ShowTitle,
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("MatrixStageTitle");
            _stage.ShowTitle = VideoSettings.ShowTitle;
            Preview.Renderer = _stage;
        }

        // The typed title wins wherever a title is read; the placeholder says what the
        // grid is about, so an untouched box names the frame it sits beside.
        VideoSettings.TitlePlaceholder = _spec?.Title ?? Strings.Get("MatrixStageTitle");

        var ready = _spec is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>Rebuilds the grid from the months already fetched, under the year count
    /// now chosen. Null only when nothing has been fetched yet.</summary>
    private void RebuildSpec()
    {
        if (_series is null || _fetchedFor is null)
        {
            _spec = null;
            return;
        }

        try
        {
            _spec = MatrixSpecs.Year(_fetchedFor.Display, _fetchedFor.Code, _series, ChosenYears());
        }
        catch (InvalidOperationException)
        {
            // Fewer settled months than the year count wants — only reachable on the
            // shortest histories, where the years were already said to be bounded by
            // the coin itself. An empty frame and the earlier sentence stand.
            _spec = null;
        }
    }

    // ---- fetch -------------------------------------------------------------------------

    private void OnCoinsChanged(object? sender, EventArgs e)
    {
        _series = null;
        _fetchedFor = null;
        _spec = null;
        SavePreferences();

        if (_ready)
        {
            ApplyPreviewSettings();
        }
    }

    private async void Fetch()
    {
        var chosen = Chosen();

        if (chosen is null)
        {
            // The picker keeps at least one on by itself, so this is the arm that lands
            // here if that ever stops being true — and it is the honest thing to say
            // rather than fetching nothing and drawing an empty grid.
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CryptoPickOne"));
            return;
        }

        await RunAsync(FetchButton, async cancellation =>
        {
            // Reported straight through rather than through Progress<T>, which posts its
            // callback to the dispatcher — posted, the walk's last report lands behind
            // this block's own success line.
            var progress = new Immediate<string>(
                message => ShowStatus(InfoBarSeverity.Informational, message));

            progress.Report(Strings.Format("CryptoMatrixFetching", chosen.Display));

            var (name, series) = await CryptoMonthly.FetchAsync(
                Services.Crypto, chosen, progress, cancellation);

            if (series.Count < 6)
            {
                // Not enough settled months for a grid that means something. The source
                // may answer a young coin with three years, or nothing at all; both are
                // the same sentence here, because both leave the grid unreadable.
                ShowStatus(InfoBarSeverity.Error, Strings.Get("MatrixTooFewMonths"));
                return;
            }

            _series = series;
            _fetchedFor = chosen;
            RebuildSpec();

            ApplyPreviewSettings();

            // Parked on the last frame: the whole grid lit is what someone wants to read
            // before deciding whether to export.
            ShowMoment(1);

            var spec = _spec!;

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "MatrixFetched",
                spec.Title,
                spec.Span,
                spec.Cells.Count,
                spec.Stats[0].Label,
                spec.Stats[0].Value,
                spec.Stats[1].Label,
                spec.Stats[1].Value));
        }, TimeSpan.FromMinutes(6));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    private void OnYearsChanged(object sender, SelectionChangedEventArgs e)
    {
        // Raised by the selection assignment in the constructor, before _ready exists.
        if (!_ready)
        {
            return;
        }

        // A reading of months already in hand, not a term of the fetch.
        RebuildSpec();
        ApplyPreviewSettings();
        SavePreferences();
    }

    // ---- playback ----------------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e) => _playback?.Seek(Scrub.Value);

    private void RefreshScrubText()
    {
        var total = VideoSettings.Duration;
        var at = TimeSpan.FromSeconds(total.TotalSeconds * Math.Clamp(Preview.Progress, 0, 1));

        ScrubText.Text = Strings.Format("StudioScrubPosition", Clock(at), Clock(total));
    }

    private void OnPlay(object sender, RoutedEventArgs e)
    {
        // At the end there is nothing left to run, and a play button that does nothing
        // reads as a broken one. Starting again is what the press meant.
        if (!_playback.IsPlaying && Preview.Progress >= 0.999)
        {
            _playback.Seek(0);
        }

        _playback.Toggle();
    }

    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) => SetPlaybackState(playing);

    private void SetPlaybackState(bool playing)
    {
        var label = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

        PlayIcon.Glyph = playing ? "\uE769" : "\uE768";

        ToolTipService.SetToolTip(PlayButton, label);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export ------------------------------------------------------------------------

    private string MatrixFileName(VideoFormat format, string extension)
    {
        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : _spec!.Title;

        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        if (safe.Length > 40)
        {
            safe = safe[..40];
        }

        return $"收益矩阵_{safe}_{format.NameSuffix}.{extension}";
    }

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _spec is null || App.Window is not { } window)
        {
            return;
        }

        // One gate, asked by every page. Writing the file — as opposed to drawing it —
        // is what the subscription buys, and the one place allowed to answer that is
        // asked before anything is read for the encode.
        if (!await MarketMotionStudio.Views.SubscriptionOffer.PermitAsync(XamlRoot, window))
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;

        CancelButton.IsEnabled = true;

        var limit = TimeSpan.FromMinutes(5) + (duration * 4);

        await RunAsync(ExportButton, async cancellation =>
        {
            var folder = await OutputFolder.TryGetAsync() ?? await OutputFolder.ChooseAsync(window);

            if (folder is null)
            {
                ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioExportCancelled"));
                return;
            }

            var clock = System.Diagnostics.Stopwatch.StartNew();

            var report = new Progress<double>(fraction =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("StudioExporting", (int)(fraction * 100))));

            var file = await VideoExporter.EncodeAsync(
                renderer, format, margins, duration, folder,
                MatrixFileName(format, "mp4"),
                report, cancellation);

            clock.Stop();

            var properties = await file.GetBasicPropertiesAsync();

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioExported",
                file.Name,
                (properties.Size / 1048576.0).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture),
                clock.Elapsed.TotalSeconds.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture),
                ((int)duration.TotalSeconds).ToString(System.Globalization.CultureInfo.InvariantCulture),
                folder.Path));
        }, limit);

        CancelButton.IsEnabled = false;
    }

    private async void OnSaveCover(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _spec is null || App.Window is not { } window)
        {
            return;
        }

        await RunAsync(CoverButton, async cancellation =>
        {
            var folder = await OutputFolder.TryGetAsync() ?? await OutputFolder.ChooseAsync(window);

            if (folder is null)
            {
                ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioCoverCancelled"));
                return;
            }

            var format = VideoSettings.Format;

            var file = await FrameExporter.SavePngAsync(
                renderer, format, VideoSettings.Margins, Preview.Progress, folder,
                MatrixFileName(format, "png"),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    // ---- preferences -------------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var years = _prefs.GetInt("Years", YearChoices[^1]);
        var index = Array.IndexOf(YearChoices, years);
        YearsCombo.SelectedIndex = index >= 0 ? index : YearChoices.Length - 1;

        // An empty answer is the picker's own business: it puts the first coin on,
        // which is what a first run needs.
        Coins.Select(_prefs.GetString("Coins", string.Empty).Split(
            ',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Years", ChosenYears());
        _prefs.Save("Coins", Chosen()?.Code ?? string.Empty);

        VideoSettings.Save(_prefs);
    }

    /// <summary>
    /// An <see cref="IProgress{T}"/> that calls back where it was reported from.
    ///
    /// <see cref="Progress{T}"/> captures the context it was built on and posts, which puts
    /// the walk's last report behind this page's own success line. The walk already runs on
    /// the UI thread, so there is nothing to marshal.
    /// </summary>
    private sealed class Immediate<T>(Action<T> report) : IProgress<T>
    {
        public void Report(T value) => report(value);
    }
}
