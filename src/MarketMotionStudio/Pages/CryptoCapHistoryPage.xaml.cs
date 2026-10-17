using System.Linq;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// A coin's market value over the years, with its price under it — or several coins
/// compared as one line each, named at their ends.
///
/// No renderer of its own: the value-history renderer takes a <see cref="CapBoard"/>
/// and draws the panels, so this page is a loader and a set of choices. The two
/// panels are the point of the single-coin frame, and they are the stock page's reason
/// too — a value line that climbs while the price line does not is coins being minted,
/// and a price that climbs faster than the value is a supply being burned. On a coin the
/// first of those is ordinary: bitcoin mints until 2140, so the two lines come apart
/// every single day.
///
/// **And the same question asked of several coins at once.** One coin is this page as it
/// has always been. Several give the whole frame to the value and draw one line each,
/// because several coins' prices do not share an axis honestly — bitcoin at $67,000
/// beside dogecoin at $0.12 puts the second flat along the bottom, which is a claim
/// about a coin rather than about two scales. The value panel's vertical axis reads
/// either the figure itself or every line rebased to 100 at its own first day, which is
/// the readable one once two coins are orders of magnitude apart.
///
/// **The value here is measured, not recovered.** The stock page multiplies a share
/// count it worked out of the turnover rate by a price, and says so. This page is
/// handed the value: CoinMetrics publishes it daily, back to 2010 on bitcoin and to
/// 2019 on coins it carries only as an estimate. Which of the two a coin got is not
/// shown, because the difference is under a percent where they overlap and the point
/// of the page is the shape, not the sixth digit.
///
/// **A coin the catalogue does not carry is not drawn.** Most of what a search can add is
/// outside CoinMetrics' asset list, and those come back empty; they are named on the
/// status line rather than drawn flat along the bottom — the same answer the stock page
/// gives an index.
/// </summary>
public sealed partial class CryptoCapHistoryPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>The span that hands the two date pickers over instead of a month count.</summary>
    private const int CustomMonths = 0;

    /// <summary>
    /// The spans offered, none of them shorter than a year.
    ///
    /// Unlike the stock page's list this one has no month-scale entry, and that is the
    /// subject rather than the source: a coin's value moves with its supply, which is a
    /// slow variable, and thirty days of it is a price chart with a different label.
    /// Thirty years is the longest, which is past every coin — the span is clipped to
    /// what the source carries and the page says where the picture really starts.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (12, "StudioRange12M"),
        (24, "StudioRange24M"),
        (60, "StudioRange60M"),
        (120, "StudioRange120M"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("CryptoCapHistory.");

    /// <summary>The fetched board, or null before anything has been fetched.</summary>
    private CapBoard? _board;

    /// <summary>Whether the page is finished being built; see the handlers that read it.</summary>
    private bool _ready;

    public CryptoCapHistoryPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 2;

        // Two readings of one value axis, the same two the share pages' value history
        // offers and for the same reason. Absolute is first and default: "how big did this
        // coin get" is a question about the figure itself.
        foreach (var (axis, key) in new[]
                 {
                     (CapAxis.Absolute, "CapHistoryAxisAbsolute"),
                     (CapAxis.Normalized, "CapHistoryAxisNormalized"),
                 })
        {
            AxisCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)axis });
        }

        AxisCombo.SelectedIndex = 0;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-10);
        ToDate.Date = today;

        // The row's ceiling is this board's ceiling, set here rather than left to the
        // picker's own default so that the two are one number. The loader refuses nothing —
        // it draws whatever it is given — so a frame drawn from a list somebody meant to
        // trim is the one failure this line prevents.
        Coins.Limit = CapLoader.MostTracks;

        // A pick added or removed retires the board that was drawn from the old list: a
        // frame still showing three coins under a row that no longer lists one of them is
        // a frame about a list nobody chose.
        Coins.Changed += OnCoinsChanged;

        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(RangeCombo, "CryptoCapRange");

        VideoSettings.AllowHideTitle = true;
        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            SavePreferences();
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        SetPlaybackState(playing: false);

        RestorePreferences();
        ApplyPreviewSettings();

        _ready = true;
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("CryptoCapHistoryPageTitle.Text");

    /// <summary>
    /// The coins on the frame, in the order the row holds them.
    ///
    /// Read off the picker rather than kept here. What is on the frame is a state that
    /// control holds, and a page that kept its own copy would be a second place the same
    /// choice is kept — and the one that goes stale.
    /// </summary>
    private IReadOnlyList<CryptoAsset> Chosen() =>
        [.. Coins.Selected.Select(entry => CryptoAsset.Of(entry.Code)).OfType<CryptoAsset>()];

    private CapAxis ChosenAxis() =>
        AxisCombo.SelectedItem is ComboBoxItem { Tag: int axis } ? (CapAxis)axis : CapAxis.Absolute;

    private void OnLookChanged(object sender, RoutedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        ApplyPreviewSettings();
        SavePreferences();
    }

    /// <summary>
    /// The value axis changed. It is not a term of the fetch — it reads figures already on
    /// the page — so this redraws and stops there.
    /// </summary>
    private void OnAxisChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        ApplyPreviewSettings();
        SavePreferences();
    }

    private bool CrossSafeRight() => CrossCheck.IsChecked is true;

    private bool DynamicAxisOn() => DynamicAxisCheck.IsChecked is true;

    // ---- preview -------------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;
        var axis = ChosenAxis();

        if (_board is { } board)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, board.Count, board.CapPeak);

            Preview.Renderer = new CapHistoryRenderer(board, plan, axis, CrossSafeRight(), DynamicAxisOn())
            {
                Title = title,
                ShowTitle = showTitle,

                // Named only while one coin is on the frame; several codes in this line
                // would push the dates and the count off it, and every coin is already
                // written beside its own line's end.
                Code = board.Comparing ? string.Empty : board.Tracks[0].Code,

                // Every word the frame says about the figures comes from here, because a
                // renderer that named its own data would go on naming it on whichever
                // page came to share it.
                CapWord = Strings.Get("CryptoCapWord"),
                CapUnitWord = axis is CapAxis.Normalized
                    ? Strings.Get("CapHistoryRebasedUnit")
                    : Strings.Format("CapHistoryCapUnit", Strings.Get("DcaCurrencyUsd")),
                PriceWord = Strings.Get("CryptoPriceWord"),
                PriceUnitWord = Strings.Get("DcaCurrencyUsd"),
                SpanWord = Strings.Get("CryptoDaysUnit"),
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = ResolvedTitle();

        var ready = _board is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>The title the frame will draw: the typed one, or the default naming what
    /// is on it. The renderer is rebuilt on every change, so the placeholder follows the
    /// selection even before a fetch has confirmed the coins' proper names.</summary>
    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : DefaultTitle();

    /// <summary>
    /// “比特币市值历程”, or the coins named against each other when there is more than one.
    ///
    /// Read off the fetched board when there is one, because a fetch is what turns a code
    /// into the name the app spells for it; off the selection before that, so the
    /// placeholder says something about what is about to be drawn.
    /// </summary>
    private string DefaultTitle()
    {
        if (_board is { } board)
        {
            return board.Comparing
                ? Compared([.. board.Tracks.Select(t => t.Name)])
                : Strings.Format("CryptoCapDefaultTitle", board.Tracks[0].Name);
        }

        var names = Chosen().Select(asset => asset.Display).ToArray();

        return names.Length switch
        {
            0 => Strings.Format("CryptoCapDefaultTitle", CryptoAsset.All[0].Display),
            1 => Strings.Format("CryptoCapDefaultTitle", names[0]),
            _ => Compared(names),
        };
    }

    private static string Compared(string[] names) => names.Length == 2
        ? Strings.Format("CapHistoryVsTitle", names[0], names[1])
        : Strings.Format("CapHistoryCompareMany", names[0], names.Length);

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 60;

        if (months == CustomMonths)
        {
            return (DateOnly.FromDateTime(FromDate.Date.DateTime),
                    DateOnly.FromDateTime(ToDate.Date.DateTime));
        }

        var today = DateOnly.FromDateTime(DateTime.Now);
        return (today.AddMonths(-months), today);
    }

    // ---- fetch ---------------------------------------------------------------------------

    private void OnCoinsChanged(object? sender, EventArgs e)
    {
        _board = null;
        SavePreferences();

        if (_ready)
        {
            ApplyPreviewSettings();
        }
    }

    private async void Fetch()
    {
        var chosen = Chosen();

        if (chosen.Count == 0)
        {
            // The picker keeps at least one on by itself, so this is the arm that lands
            // here if that ever stops being true — and it is the honest thing to say
            // rather than fetching nothing and drawing an empty axis.
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CryptoPickOne"));
            return;
        }

        var (start, end) = ChosenRange();

        // Six minutes rather than three: one coin is a pair of requests, and the page now
        // walks up to six of them, one after the other.
        await RunAsync(FetchButton, async cancellation =>
        {
            // Reported straight through rather than through Progress<T>, which posts its
            // callback to the dispatcher — posted, the walk's last report lands behind this
            // block's own success line and the status bar finishes on the walk.
            var progress = new Immediate<string>(
                message => ShowStatus(InfoBarSeverity.Informational, message));

            var board = await CryptoCapLoader.LoadAsync(
                Services.CryptoCaps, chosen, start, end, progress, cancellation);

            if (board is null)
            {
                // Not one of them had a history in the span, which on this page has two
                // likely causes and the same answer: the span is shorter than the source's
                // history, or every coin chosen is one the catalogue does not carry.
                ShowStatus(InfoBarSeverity.Error, Strings.Get("CryptoCapTooFewDays"));
                return;
            }

            _board = board;

            ApplyPreviewSettings();

            // Parked on the last frame: the closing figures are what someone wants to look
            // at before deciding whether to export.
            ShowMoment(1);

            ReportFetched(board, start);
        }, TimeSpan.FromMinutes(6));
    }

    /// <summary>
    /// What the fetch came back with, said as the shape it came back in.
    ///
    /// One coin reports the closing figure, because that is the number the page exists to
    /// give and the only one its status line can carry. Several report the count and the
    /// span instead, and name whatever had to be left out — a coin that is missing from a
    /// comparison is the thing the reader has to act on, and the frame is a line short
    /// without it.
    /// </summary>
    private void ReportFetched(CapBoard board, DateOnly wanted)
    {
        var range = TurnoverRenderer.Iso(board.Start);
        var until = TurnoverRenderer.Iso(board.End);

        if (!board.Comparing)
        {
            ShowFetched(
                Strings.Format(
                    "CryptoCapFetched",
                    board.Count,
                    range,
                    until,
                    board.Tracks[0].FinalCap.ToString(
                        "N0", System.Globalization.CultureInfo.CurrentCulture)),
                InfoBarSeverity.Success,
                board.Start,
                wanted,
                Strings.Format("CryptoRangeShort", range));

            return;
        }

        var fetched = Strings.Format(
            "CryptoCapBoardFetched", board.Tracks.Count, board.Count, range, until);

        if (board.Skipped.Count == 0)
        {
            ShowFetched(
                fetched,
                InfoBarSeverity.Success,
                board.Start,
                wanted,
                Strings.Format("CryptoRangeShort", range));

            return;
        }

        // Appended to the line that reports the fetch, never shown in its place: which
        // coin the range could not hold, and how many were drawn, are one answer.
        ShowStatus(InfoBarSeverity.Warning, $"{fetched} {Strings.Format(
            "CryptoCapSkipped", board.Skipped.Count, string.Join(", ", board.Skipped))}");
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    // ---- playback -----------------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        // Raised by the selection assignment in the constructor, before CustomRange exists.
        if (CustomRange is null)
        {
            return;
        }

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: CustomMonths };
        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
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

    // ---- export -------------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _board is null || App.Window is not { } window)
        {
            return;
        }

        if (!await MarketMotionStudio.Views.SubscriptionOffer.PermitAsync(XamlRoot, window))
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;
        var label = ResolvedTitle();
        var board = _board;

        CancelButton.IsEnabled = true;

        var limit = TimeSpan.FromMinutes(5) + (duration * 4);

        Diagnostics.CrashLog.Note($"export: clicked, {format.Width}x{format.Height} dur={duration}");

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
                VideoExporter.VideoName(label, board.Start, board.End, format),
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
        if (Preview.Renderer is not { } renderer || _board is not { } board || App.Window is not { } window)
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
                FrameExporter.CoverName(ResolvedTitle(), board.Start, board.End, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences --------------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var months = _prefs.GetInt("Months", 60);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 2;

        SelectAxis(_prefs.GetInt("Axis", (int)CapAxis.Absolute));

        if (DateTime.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = from;
        }

        if (DateTime.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = to;
        }

        // The coins. The key was renamed when this page went from one coin to several, and
        // the old single code is still read as the whole list so that a coin somebody had
        // settled on survives the change. An empty answer is the picker's own business: it
        // puts the first coin on, which is what a first run needs.
        var stored = _prefs.GetString("Coins", _prefs.GetString("Code", string.Empty));

        Coins.Select(stored.Split(
            ',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));

        CrossCheck.IsChecked = _prefs.GetInt("Cross", 0) == 1;

        DynamicAxisCheck.IsChecked = _prefs.GetInt("DynamicAxis", 0) == 1;

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 60);
        _prefs.Save("Axis", (int)ChosenAxis());
        _prefs.Save("From", FromDate.Date.ToString("O"));
        _prefs.Save("To", ToDate.Date.ToString("O"));
        _prefs.Save("Coins", string.Join(",", Chosen().Select(asset => asset.Code)));
        _prefs.Save("Cross", CrossSafeRight() ? 1 : 0);
        _prefs.Save("DynamicAxis", DynamicAxisOn() ? 1 : 0);

        VideoSettings.Save(_prefs);
    }

    private void SelectAxis(int axis)
    {
        foreach (var item in AxisCombo.Items.OfType<ComboBoxItem>())
        {
            if (item.Tag is int value && value == axis)
            {
                AxisCombo.SelectedItem = item;
                return;
            }
        }

        AxisCombo.SelectedIndex = 0;
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

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
