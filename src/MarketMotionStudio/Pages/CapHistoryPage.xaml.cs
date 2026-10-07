using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// A company's circulating market value over the years, with the price it was taken at
/// beneath it.
///
/// **And the same question asked of several companies at once**, which is how it is
/// usually asked — whether one company passed another, and when. Comparison takes the
/// whole frame for the value and draws one line per company, named at its own leading
/// end. The price panel goes, because several companies' prices do not share a price
/// axis honestly: 贵州茅台 at 1,258 元 beside 京东方A at 4.2 元 puts the second flat
/// along the bottom, which is a claim about a company rather than about two scales.
/// The value panel's vertical axis has two readings — the figure itself, or every line
/// rebased to 100 at its own first day — and which one is in force is decided where the
/// renderer is built, not after. See <see cref="CapAxis"/> for why.
///
/// The figure is not one the source carries. It is recovered from the row — the turnover
/// rate gives the share count, the price gives the value — which is why this page is the
/// only one that asks for an unadjusted series: an adjusted close has been rebased and a
/// value taken at it is not a value. See <see cref="CapHistory"/> for the whole of that
/// arithmetic and for what was measured to trust it.
///
/// The companies come from the reader's own list — the one every roster board shares —
/// with a chip per pick deciding whether it is on this frame; the one-tap row beneath it
/// is the market's own list of names a long-held position is plausibly a story about.
///
/// Otherwise this is the same page the other per-instrument ones are: a span, a preview
/// that is the frame, and the same four buttons.
/// </summary>
public sealed partial class CapHistoryPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();

    private readonly Playback _playback;

    /// <summary>
    /// This page's own settings. A separate prefix from the other per-instrument
    /// pages', because the video and layout panel is one control serving all of them —
    /// sharing the store would mean tuning one chart's margins silently retuned
    /// another's.
    /// </summary>
    private readonly StudioPreferences _prefs = new("CapHistory.");

    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    private CapBoard? _board;

    /// <summary>Whether the page is finished being built; see the handlers that read it.</summary>
    private bool _ready;

    /// <summary>The span that hands the two date pickers over instead of a month count.</summary>
    private const int CustomMonths = 0;

    private static readonly (int Months, string Key)[] Ranges =
    [
        (12, "StudioRange12M"),
        (24, "StudioRange24M"),
        (60, "StudioRange60M"),
        (120, "StudioRange120M"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    public CapHistoryPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // Two readings of one value axis. Absolute is first and default: "how big did
        // this company get" is a question about the figure itself, and it is the reading
        // in which two lines can be compared as one being worth more than the other.
        // Rebasing answers the other half — whose value grew faster — and is what makes
        // a comparison readable once the two are tenfold apart.
        foreach (var (axis, key) in new[]
                 {
                     (CapAxis.Absolute, "CapHistoryAxisAbsolute"),
                     (CapAxis.Normalized, "CapHistoryAxisNormalized"),
                 })
        {
            AxisCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)axis });
        }

        AxisCombo.SelectedIndex = 0;

        Presets.ItemsSource = _market.PositionInstruments
            .Select(entry => new MatrixPreset(entry.Code, InstrumentNames.Display(entry.Code, entry.Name)))
            .ToArray();

        // The picker has no status bar of its own to write into, so what it has to say is
        // said here.
        Watch.Notice += message => ShowStatus(InfoBarSeverity.Error, message);

        // A pick added or removed here changes the list on every roster board, all of
        // them sharing one, and on this one it retires the board that was drawn from the
        // old list: a frame still showing five companies under a chip row that no longer
        // lists one of them is a frame about a list nobody chose.
        Watch.Changed += OnWatchChanged;

        // The pickers stop where one walk stops. A date someone can choose and a date
        // the walk then cannot reach is a control arguing with itself.
        var today = DateTimeOffset.Now;
        var oldest = today.AddDays(-CapHistory.MostDays);

        FromDate.MinYear = oldest;
        FromDate.MaxYear = today;
        ToDate.MinYear = oldest;
        ToDate.MaxYear = today;

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

        // Named before it has ever been pressed: the button is an icon, so the tooltip
        // and the name a screen reader announces are the only words it has.
        SetPlaybackState(playing: false);

        // After every control exists and every handler is attached, so a restored value
        // reaches the preview through the same path a typed one does.
        RestorePreferences();
        ApplyPreviewSettings();

        _ready = true;
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("CapHistoryPageTitle.Text");

    private int ChosenMonths() =>
        RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 12;

    private CapAxis ChosenAxis() =>
        AxisCombo.SelectedItem is ComboBoxItem { Tag: int axis } ? (CapAxis)axis : CapAxis.Absolute;

    /// <summary>
    /// What this frame compares: the reader's list, kept to the market in force.
    ///
    /// The list itself is deliberately cross-market — it is shared with every roster
    /// board, several of which put three venues on one axis — while a value here is the
    /// market in force's currency and its walk is the one that knows that venue's rows.
    /// So a pick from another venue is not drawn rather than drawn in the wrong money,
    /// and the fetch says so when that leaves nothing at all.
    /// </summary>
    private IReadOnlyList<RaceEntry> Chosen() =>
        [.. Watch.SelectedEntries.Where(e => _market.Accepts(e.Code))];

    private (DateOnly From, DateOnly To) CustomSpan() => (
        DateOnly.FromDateTime(FromDate.Date.DateTime),
        DateOnly.FromDateTime(ToDate.Date.DateTime));

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        CustomRange.Visibility = ChosenMonths() == CustomMonths ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    /// <summary>
    /// The value axis changed. It is not a term of the fetch — it reads figures already
    /// on the page — so this redraws and stops there.
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

    // ---- preview ---------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_board is { } board)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, board.Count, board.CapPeak);

            Preview.Renderer = new CapHistoryRenderer(board, plan, ChosenAxis())
            {
                Title = title,
                ShowTitle = showTitle,

                // Named only while one company is on the frame; see DrawHeader.
                Code = board.Comparing ? string.Empty : board.Tracks[0].Code,

                // Every word the frame says about the figures comes from here. The
                // renderer holds none of them, because a renderer that named its own
                // data would go on naming it on whichever page came to share it — the
                // market-cap board once drew twelve months as "12 个交易日" out of a
                // line no caller had any say in.
                CapWord = Strings.Get("CapHistoryCapWord"),
                CapUnitWord = ChosenAxis() is CapAxis.Normalized
                    ? Strings.Get("CapHistoryRebasedUnit")
                    : Strings.Format("CapHistoryCapUnit", Strings.Get(_market.CurrencyKey)),
                PriceWord = Strings.Get(board.PriceIsAverage
                    ? "CapHistoryAveragePriceWord"
                    : "CapHistoryPriceWord"),
                PriceUnitWord = Strings.Get(_market.CurrencyKey),
                SpanWord = Strings.Get("StockTradingDaysUnit"),
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
    /// selection even before a fetch has confirmed the companies' proper names.</summary>
    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : DefaultTitle();

    /// <summary>
    /// “贵州茅台 市值”, or the companies named against each other when there is more than
    /// one.
    ///
    /// Read off the fetched board when there is one, because a fetch is what corrects a
    /// typed code to the name the venue actually calls it; off the selection before that,
    /// so the placeholder says something about what is about to be drawn.
    /// </summary>
    private string DefaultTitle()
    {
        if (_board is { } board)
        {
            return board.Comparing
                ? Compared([.. board.Tracks.Select(t => t.Name)])
                : Strings.Format("CapHistoryDefaultTitle", board.Tracks[0].Name);
        }

        var names = Chosen().Select(e => InstrumentNames.Display(e.Code, e.Name)).ToArray();

        return names.Length switch
        {
            0 => Strings.Format("CapHistoryDefaultTitle", _market.PositionInstruments[0].Name),
            1 => Strings.Format("CapHistoryDefaultTitle", names[0]),
            _ => Compared(names),
        };
    }

    private static string Compared(string[] names) => names.Length == 2
        ? Strings.Format("CapHistoryVsTitle", names[0], names[1])
        : Strings.Format("CapHistoryCompareMany", names[0], names.Length);

    // ---- picking ---------------------------------------------------------------------

    private void OnWatchChanged(object? sender, EventArgs e)
    {
        _board = null;
        SavePreferences();
        ApplyPreviewSettings();
    }

    private void OnPresetClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is not string code)
        {
            return;
        }

        var name = Presets.Items.OfType<MatrixPreset>().FirstOrDefault(p => p.Code == code)?.Name ?? code;

        if (!Watchlist.Has(code) && !Watchlist.Add(code, name))
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("SectorTooManyStocks", Watchlist.Most));
            return;
        }

        // On the list *and* switched on for this frame in one press. The row is one-tap by
        // design: a pick that arrived on the list but switched off would draw nothing at
        // all, which reads as a broken button rather than as a setting.
        Watch.Include(code);

        Fetch();
    }

    private async void Fetch()
    {
        // Refused before a request is made, where a market's rows cannot carry a value
        // at all — see CapHistory.Serves for which and why. All three markets it serves
        // today do carry one, so this is the arm a future venue lands in, and the words
        // it answers with are deliberately about the market rather than about any one
        // of them.
        if (!CapHistory.Serves(_market.Id))
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CapHistoryMarketNone"));
            return;
        }

        var chosen = Chosen();

        if (chosen.Count == 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("CapHistoryNoMarketPicks", _market.Name));
            return;
        }

        // Refused rather than trimmed: a frame drawn from six of the nine companies
        // somebody ticked answers about a list nobody chose, and it looks entirely
        // plausible while it does — the same reason no roster board quietly drops a row.
        if (chosen.Count > CapLoader.MostTracks)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format(
                "CapHistoryTooMany", CapLoader.MostTracks, chosen.Count));

            return;
        }

        var months = ChosenMonths();
        var custom = months == CustomMonths;
        var today = DateOnly.FromDateTime(DateTime.Now);
        var (from, to) = custom ? CustomSpan() : (today.AddMonths(-months), today);

        if (custom)
        {
            if (from >= to)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
                return;
            }

            // Past this the walk runs out of requests before it runs out of range, and
            // the series starts later than the date that was asked for — which is the
            // one answer a typed span must not give.
            if ((to.DayNumber - from.DayNumber) > CapHistory.MostDays)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Format(
                    "CapHistoryRangeTooLong", CapHistory.MostDays / 365));

                return;
            }
        }

        // Six minutes, not three: one company reaching back ten years is twenty requests
        // answered one after another, and this page now draws up to six of them, walked
        // in turn.
        await RunAsync(FetchButton, async cancellation =>
        {
            // Reported straight through rather than through Progress<T>, which posts its
            // callback to the dispatcher. Posted, the callback the walk makes in its last
            // pass lands after the success line this block ends with — and the status bar
            // finishes on "0:120 …" for a fetch that worked.
            var progress = new Immediate<string>(
                message => ShowStatus(InfoBarSeverity.Informational, message));

            var board = await CapLoader.LoadAsync(
                Services.Quotes, chosen, from, to, _market, progress, cancellation);

            if (board is null)
            {
                // Nothing usable came back, which on this page has a particular and
                // likely cause worth naming: an index has no turnover rate at all, and
                // neither does anything the source quotes without one. "No value" would
                // send someone looking at the range instead.
                ShowStatus(InfoBarSeverity.Error, Strings.Get("CapHistoryNoTurnover"));
                return;
            }

            _board = board;

            // A typed pick is renamed to what the endpoint calls it, which is also the
            // name the roster boards will read off the shared list.
            foreach (var track in board.Tracks)
            {
                Watchlist.Rename(track.Code, InstrumentNames.Display(track.Code, track.Name));
            }

            ApplyPreviewSettings();

            // Parked on the last frame: the closing figures are what someone wants to
            // look at before deciding whether to export.
            ShowMoment(1);

            var iso = CultureInfo.InvariantCulture;
            var range = board.Start.ToString("yyyy-MM-dd", iso);
            var until = board.End.ToString("yyyy-MM-dd", iso);

            // No currency in either line: 亿 has no English, and a figure that arrives
            // with the wrong unit attached is worse than one that arrives with none —
            // the frame above it is labelled in the venue's own unit already.
            var fetched = board.Comparing
                ? Strings.Format("CapHistoryBoardFetched", board.Tracks.Count, board.Count, range, until)
                : Strings.Format(
                    "CapHistoryFetched", board.Count, range, until,
                    board.Tracks[0].FinalCap.ToString("N0", iso));

            if (board.Skipped.Count == 0)
            {
                ShowStatus(InfoBarSeverity.Success, fetched);
            }
            else
            {
                // Named rather than counted: which company the range could not hold is
                // the thing the reader has to act on, and the frame is a line short
                // without it.
                ShowStatus(InfoBarSeverity.Warning, $"{fetched} {Strings.Format(
                    "CapHistorySkipped", board.Skipped.Count, string.Join(", ", board.Skipped))}");
            }
        }, TimeSpan.FromMinutes(6));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    // ---- playback --------------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e)
    {
        // Moving the slider is an instruction to look at one moment, which means stopping
        // the playback wherever it had got to — and moving the position a press
        // afterwards will start from.
        _playback.Seek(Scrub.Value);
    }

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

    /// <summary>Points the button at what it will do next: ▶ to run the animation, ⏸ to hold it.</summary>
    private void SetPlaybackState(bool playing)
    {
        var label = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

        PlayIcon.Glyph = playing ? "\uE769" : "\uE768";

        ToolTipService.SetToolTip(PlayButton, label);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export ---------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _board is not { } board || App.Window is not { } window)
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

        // Read before the work starts, so touching a slider mid-export cannot change the
        // format halfway through the file.
        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;
        var label = ResolvedTitle();

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
                ShowStatus(InfoBarSeverity.Informational,
                    Strings.Format("StudioExporting", (int)(fraction * 100))));

            var file = await VideoExporter.EncodeAsync(
                renderer, format, margins, duration, folder,
                VideoExporter.VideoName(label, board.Start, board.End, format),
                report, cancellation);

            clock.Stop();

            var properties = await file.GetBasicPropertiesAsync();

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioExported",
                file.Name,
                (properties.Size / 1048576.0).ToString("0.0", CultureInfo.InvariantCulture),
                clock.Elapsed.TotalSeconds.ToString("0.0", CultureInfo.InvariantCulture),
                ((int)duration.TotalSeconds).ToString(CultureInfo.InvariantCulture),
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

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    // ---- preferences -----------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var today = DateTimeOffset.Now;

        FromDate.Date = today.AddYears(-1);
        ToDate.Date = today;

        if (DateOnly.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = new DateTimeOffset(from, TimeOnly.MinValue, TimeSpan.Zero);
        }

        if (DateOnly.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = new DateTimeOffset(to, TimeOnly.MinValue, TimeSpan.Zero);
        }

        Select(RangeCombo, _prefs.GetInt("Months", 24));
        Select(AxisCombo, _prefs.GetInt("Axis", (int)CapAxis.Absolute));

        CustomRange.Visibility = ChosenMonths() == CustomMonths ? Visibility.Visible : Visibility.Collapsed;

        VideoSettings.Restore(_prefs);

        // The companies are the shared list, which the picker loads on its own — there is
        // nothing instrument-shaped left to remember here. What is remembered is the list
        // itself, and it is remembered for every board that shares it.
        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Months", ChosenMonths());
        _prefs.Save("Axis", (int)ChosenAxis());
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));

        VideoSettings.Save(_prefs);
    }

    private static void Select(ComboBox combo, int tag)
    {
        foreach (var item in combo.Items.OfType<ComboBoxItem>())
        {
            if (item.Tag is int value && value == tag)
            {
                combo.SelectedItem = item;
                return;
            }
        }

        if (combo.Items.Count > 0)
        {
            combo.SelectedIndex = 0;
        }
    }

    /// <summary>
    /// An <see cref="IProgress{T}"/> that calls back where it was reported from.
    ///
    /// <see cref="Progress{T}"/> captures the context it was built on and posts, which
    /// puts the walk's last report behind this method's own success line. The walk
    /// already runs on the UI thread, so there is nothing to marshal.
    /// </summary>
    private sealed class Immediate<T>(Action<T> report) : IProgress<T>
    {
        public void Report(T value) => report(value);
    }
}
