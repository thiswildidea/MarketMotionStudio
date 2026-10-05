using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// Whole-market daily turnover: the Shanghai and Shenzhen composite amounts added
/// together, animated as a bar per trading day.
/// </summary>
public sealed partial class MarketTurnoverPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>
    /// The ranges offered, as a number of months. Zero means the custom range,
    /// which is the only one that consults the date pickers.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (1, "StudioRange1M"),
        (3, "StudioRange3M"),
        (6, "StudioRange6M"),
        (12, "StudioRange12M"),
        (0, "StudioRangeCustom"),
    ];

    /// <summary>
    /// The two forms the same series can be drawn as. Bars first, because it is the one that
    /// answers the ordinary question — how turnover moved — where the calendar answers when.
    ///
    /// The gain/loss calendar that once lived here as a third form is its own page now, on any
    /// A-share stock or index rather than this page's fixed composite — the same renderer, a
    /// wider choice behind it. Two places producing the same video is a choice nobody needs.
    /// </summary>
    /// <remarks>
    /// <c>Intraday</c> is the one form that is not a different picture of the same numbers: the
    /// daily forms both read the series already fetched, where this one has to go and get a
    /// session of its own. That is why switching to it drops what is here rather than redrawing
    /// it — see <see cref="OnViewChanged"/>.
    /// </remarks>
    private enum View
    {
        Bars,
        Calendar,
        Intraday,
    }

    private static readonly (View View, string Key)[] Views =
    [
        (View.Bars, "TurnoverViewBars"),
        (View.Calendar, "TurnoverViewCalendar"),
        (View.Intraday, "TurnoverViewIntraday"),
    ];

    /// <summary>
    /// The boards a series can cover, in the loader's enum order. A separate list because the
    /// combo wants display names while the loader wants the enum, and a Tag bridges them the same
    /// way the range and view combos above do.
    /// </summary>
    private static readonly (MarketScope Scope, string Key)[] Scopes =
    [
        (MarketScope.Whole, "TurnoverScopeWhole"),
        (MarketScope.Shanghai, "TurnoverScopeShanghai"),
        (MarketScope.ShanghaiMain, "TurnoverScopeShanghaiMain"),
        (MarketScope.Star, "TurnoverScopeStar"),
        (MarketScope.Shenzhen, "TurnoverScopeShenzhen"),
        (MarketScope.ShenzhenMain, "TurnoverScopeShenzhenMain"),
        (MarketScope.ChiNext, "TurnoverScopeChiNext"),
        (MarketScope.WithBeijing, "TurnoverScopeWithBeijing"),

        // Last, and the only one that is not a board: what is raced here is whatever the reader
        // put on the list. It is one entry in the same menu because the frame does not care
        // whether the codes it sums describe a board or a person's holdings — every one of these
        // options is the same addition over a different set of codes.
        (MarketScope.Watchlist, "TurnoverScopeWatchlist"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("Turnover.");

    public MarketTurnoverPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 1;

        foreach (var (view, key) in Views)
        {
            ViewCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = view });
        }

        ViewCombo.SelectedIndex = 0;

        foreach (var (scope, key) in Scopes)
        {
            ScopeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = scope });
        }

        ScopeCombo.SelectedIndex = 0;

        // The picker has no panel of its own to write into, so what it has to say is said here.
        Watch.Notice += message => ShowStatus(InfoBarSeverity.Error, message);

        // Idempotent, and needed: the shared list is read once for the whole process, and this
        // page can be the first one to ask for it.
        Watchlist.EnsureLoaded();

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddMonths(-3);
        ToDate.Date = today;

        // The hide-title switch is offered here as well. The original reason not to was that this
        // title names a market, not an instrument, so there was nothing to keep out of frame — but
        // a clean frame with just the number is a legitimate look, and the switch is free: the
        // panel, the persistence and the stage renderer all already implement it.
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

        // Named before it has ever been pressed: the button is an icon, so the tooltip and
        // the name a screen reader announces are the only words it has, and neither can
        // wait for the first toggle to appear.
        SetPlaybackState(playing: false);

        // After every control exists and every handler is attached, so a restored value reaches the
        // preview through the same path a typed one does.
        RestorePreferences();
        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>
    /// Reuses the page title. It already names this work in every language, so a
    /// separate job label would be fourteen near-duplicate strings.
    /// </summary>
    protected override string JobName => Strings.Get("MarketTurnoverPageTitle.Text");

    /// <summary>
    /// Pushes the panel's values into the preview and redraws once.
    ///
    /// One call for all of them rather than a handler per control: everything on
    /// that panel changes the picture and nothing else, so splitting it would only
    /// create the chance of handling three and forgetting the fourth.
    /// </summary>
    /// <summary>
    /// The fetched series, or null before anything has been fetched. Held rather than
    /// re-fetched: the duration slider changes the *pacing* of the same data, and going
    /// back to the network for that would be a round trip to arrive at the same numbers.
    /// </summary>
    private TurnoverSeries? _series;

    /// <summary>
    /// The session behind the intraday form, or null before one has been fetched. Separate from
    /// <see cref="_series"/> because it is a different thing: one day minute by minute, fetched
    /// from a different endpoint, and no amount of redrawing will turn one into the other.
    /// </summary>
    private IntradayTurnover? _session;

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        // Empty is passed through as empty and the *metric* supplies the default, because what
        // "nothing typed" means now depends on which form is showing: the turnover forms default to
        // naming the market, the return calendar to naming the index.
        var title = VideoSettings.TitleText;
        var showTitle = VideoSettings.ShowTitle;
        var intraday = Chosen == View.Intraday;

        if (intraday && _session is { } session)
        {
            // Rebuilt rather than mutated, because the plan is derived from the duration and the
            // bar count together. A renderer holding a stale plan would animate at the old pacing
            // while the read-out said the new length — the kind of disagreement that is invisible
            // until someone times an export.
            var plan = AnimationPlan.For(VideoSettings.Duration, session.Count, session.TotalYi);

            Preview.Renderer = new IntradayRenderer(session, plan) { Title = title, ShowTitle = showTitle };
        }
        else if (!intraday && _series is { } series)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, series.Count, series.Peak);

            Preview.Renderer = Chosen switch
            {
                View.Calendar => new CalendarHeatmapRenderer(series, plan, Metric.Turnover)
                    { Title = title, ShowTitle = showTitle },
                _ => new BarRaceRenderer(series, plan) { Title = title, ShowTitle = showTitle },
            };
        }
        else
        {
            _stage.Title = title.Length > 0
                ? title
                : intraday ? Strings.Get("TurnoverIntradayStageTitle") : Metric.Turnover.DefaultTitle();
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        // The placeholder follows the form, so an empty box always shows the title that would
        // actually be used rather than one of the two.
        VideoSettings.TitlePlaceholder =
            intraday ? Strings.Get("TurnoverIntradayStageTitle") : Metric.Turnover.DefaultTitle();

        // Everything that needs a series is enabled and disabled together, in the one place that
        // knows whether there is one. Three buttons each deciding for themselves is three chances
        // for one of them to be live over an empty frame.
        var ready = intraday ? _session is not null : _series is not null;

        CoverButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        PlayButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    private View Chosen => ViewCombo.SelectedItem is ComboBoxItem { Tag: View v } ? v : View.Bars;

    /// <summary>
    /// The range the user asked for, as two dates.
    ///
    /// The custom option is the only one that consults the pickers; the rest count back from
    /// today. Working it out here rather than in the loader keeps the data layer free of any
    /// notion of what a combo box said.
    /// </summary>
    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 3;

        if (months == 0)
        {
            return (DateOnly.FromDateTime(FromDate.Date.DateTime), DateOnly.FromDateTime(ToDate.Date.DateTime));
        }

        var today = DateOnly.FromDateTime(DateTime.Now);
        return (today.AddMonths(-months), today);
    }

    /// <summary>
    /// Remembered, but the series already fetched is left alone: including Beijing changes what the
    /// next fetch asks for, not what the last one returned. Redrawing with a subtitle that named a
    /// market the numbers do not include would be worse than leaving it until the next fetch.
    /// </summary>
    private void OnScopeChanged(object sender, SelectionChangedEventArgs e)
    {
        // Shown only for the one entry it feeds. Done even while a restore is running, so a
        // remembered choice of one's own list comes back with the list under it rather than as a
        // bare combo box.
        var mine = ChosenScope == MarketScope.Watchlist;

        Watch.Visibility = mine ? Visibility.Visible : Visibility.Collapsed;
        PickNote.Visibility = mine ? Visibility.Visible : Visibility.Collapsed;

        // A different board is a different answer, so whatever was fetched no longer describes
        // the panel. Dropped rather than left standing: a frame still drawn from the whole market
        // under a caption reading one's own list is a plausible picture of the wrong thing, and
        // the numbers on it give no hint that it is.
        if (!_prefs.Restoring)
        {
            _series = null;
            _session = null;
        }

        SavePreferences();
    }

    private MarketScope ChosenScope =>
        ScopeCombo.SelectedItem is ComboBoxItem { Tag: MarketScope scope } ? scope : MarketScope.Whole;

    private async void OnFetch(object sender, RoutedEventArgs e)
    {
        // The intraday form is a fetch of its own: it reads a different endpoint, it has no range
        // to apply, and what comes back is not the series the other two draw.
        if (Chosen == View.Intraday)
        {
            await FetchSessionAsync();
            return;
        }

        var (start, end) = ChosenRange();
        var scope = ChosenScope;

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            if (scope == MarketScope.Watchlist)
            {
                var basket = ChosenBasket();

                // Nothing switched on is not the same as nothing on the list, and the two want
                // different sentences: one is a list to fill in, the other a switch to turn back on.
                if (basket.Count == 0)
                {
                    ShowStatus(InfoBarSeverity.Error, Strings.Get(
                        Watchlist.Picks.Count == 0 ? "TurnoverBasketEmpty" : "TurnoverPickNone"));

                    return;
                }

                // Named from the whole list rather than from the basket: a chip reads its code
                // until a fetch names it, and this board's chips now include the picks that are
                // switched off — they are on the screen too, and would otherwise keep reading
                // `SH688981` for as long as nobody switches them on. One snapshot names them all,
                // and the list is shared, so the four roster boards get the names as well.
                await NameBasketAsync([.. Watch.Entries.Select(entry => entry.Code)], cancellation);

                _series = await BasketTurnover.LoadAsync(
                    Services.Quotes, basket, start, end, progress, cancellation);
            }
            else
            {
                _series = await MarketTurnover.LoadAsync(
                    Services.Quotes, scope, start, end, progress, cancellation);
            }

            var series = _series;

            ApplyPreviewSettings();

            // Parked on the last frame, the way the source tool does: the closing statistics
            // are the part someone wants to look at before deciding whether to export, and
            // starting at frame zero shows an empty chart instead.
            ShowMoment(1);

            // Formatted the same way the frame formats them — ISO dates and grouped
            // thousands. The status line and the video are describing one series, and a
            // reader comparing them should not have to work out that 23807 and 23,807 are
            // the same number.
            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "TurnoverFetched",
                series.Count,
                TurnoverRenderer.Iso(series.Dates[0]),
                TurnoverRenderer.Iso(series.Dates[^1]),
                TurnoverRenderer.Round(series.Average),
                TurnoverRenderer.Round(series.Peak),
                TurnoverRenderer.Round(series.Low)));
        }, TimeSpan.FromMinutes(2));
    }

    /// <summary>
    /// The picks this board draws: the ones switched on, as the basket loader wants them.
    ///
    /// Read from the picker rather than from <see cref="Watchlist.Picks"/> directly, because the
    /// picker is both what is bound to that collection and what holds the switching — a chip
    /// removed a moment ago is gone from it, and a second list held here would be a second thing
    /// to keep in step.
    /// </summary>
    private IReadOnlyList<(string Code, string Name)> ChosenBasket() =>
        [.. MainlandPicks().Select(entry => (entry.Code, entry.Name))];

    /// <summary>
    /// The picks this page can actually add up: the switched-on ones quoted on a mainland exchange.
    ///
    /// The shared list is cross-market, and turnover is the one measure here that cannot be —
    /// each venue reports it in its own currency, so a Hong Kong name in this basket would be
    /// added to a total the frame labels 亿元. Dropped rather than converted, because the rate
    /// that would make the sum honest is a different rate on every day in the range.
    ///
    /// **Said out loud when anything is dropped.** A silently smaller basket is the failure this
    /// whole page is built to avoid: the frame stays plausible and only the total is wrong.
    /// </summary>
    private IReadOnlyList<RaceEntry> MainlandPicks()
    {
        var all = Watch.SelectedEntries;
        var mainland = all.Where(entry => Markets.IsMainland(entry.Code)).ToArray();

        if (mainland.Length < all.Count)
        {
            ShowStatus(
                InfoBarSeverity.Informational,
                Strings.Format("TurnoverBasketSkipped", all.Count - mainland.Length));
        }

        return mainland;
    }

    /// <summary>
    /// Which codes one session is the sum of, and what to call it.
    ///
    /// The boards' recipes are borrowed from the daily loader rather than restated — the Shanghai
    /// main board is the exchange less its STAR board on *every* axis this page draws, and a
    /// minute-by-minute chart with its own idea of that would show the whole exchange under a
    /// title saying the main board.
    /// </summary>
    private (string[] Adds, string[] Subtracts, string Label) SessionRecipe()
    {
        if (ChosenScope != MarketScope.Watchlist)
        {
            var (adds, subtracts) = MarketTurnover.Codes(ChosenScope);

            return (adds, subtracts, Strings.Get(Scopes.First(s => s.Scope == ChosenScope).Key));
        }

        // The same filter the daily basket uses, for the same reason: a session's running total
        // is money, and the Hong Kong and New York minute series count it in their own currency.
        var picks = MainlandPicks();

        return (
            [.. picks.Select(entry => entry.Code)],
            [],
            Strings.Format("TurnoverBasketLabel", picks.Count));
    }

    /// <summary>
    /// Puts the picks' real names on the shared list.
    ///
    /// A code typed into the picker without choosing a suggestion has no name yet, so its chip
    /// reads `SH688981` — and the list is shared with the four roster boards, so they read it too.
    /// One snapshot per fetch names all of them at once, which is what those boards do after their
    /// own fetch and why a name corrected here shows up there.
    ///
    /// Wrapped, and swallowed: a name is worth one request and not worth failing a fetch over.
    /// </summary>
    private async Task NameBasketAsync(IEnumerable<string> codes, CancellationToken cancellation)
    {
        try
        {
            var shots = await Services.Stocks.SnapshotsAsync([.. codes], cancellation);

            foreach (var (code, shot) in shots)
            {
                Watchlist.Rename(code, InstrumentNames.Display(code, shot.Name));
            }
        }
        catch (Exception)
        {
            // Ignored on purpose — see the note above.
        }
    }

    /// <summary>
    /// Fetches one session and puts it on the stage.
    ///
    /// No range is applied, and that is not an oversight: the minute endpoint keeps the last five
    /// sessions and no more, so the only choice on offer is which of those five — and the frame
    /// names the one it drew rather than leaving it to be inferred.
    /// </summary>
    private async Task FetchSessionAsync()
    {
        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var (adds, subtracts, label) = SessionRecipe();

            // Same distinction as the daily basket: an empty list and an empty selection are
            // different states with different fixes.
            if (adds.Length == 0)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get(
                    Watchlist.Picks.Count == 0 ? "TurnoverBasketEmpty" : "TurnoverPickNone"));

                return;
            }

            if (ChosenScope == MarketScope.Watchlist)
            {
                await NameBasketAsync(adds, cancellation);
            }

            IntradayTurnover session;

            try
            {
                session = await TurnoverIntraday.LoadBasketAsync(
                    Services.Http, adds, subtracts, label, progress, cancellation);
            }
            catch (IntradayUnavailableException gone)
            {
                // Said here rather than left to the runner's own reporting, which would put the
                // code and an English enum name on a status line otherwise in the reader's
                // language — and would not say whether the instrument will ever work.
                ShowStatus(InfoBarSeverity.Error, Strings.Format(DenialKey(gone.Denial), gone.Code.ToUpperInvariant()));
                return;
            }

            _session = session;
            ApplyPreviewSettings();

            ShowMoment(1);

            // The unit is passed rather than written into the string, because it is the same word
            // the frame prints under the figure and the same word the daily status line uses —
            // three translations of "亿元" is three chances for one of them to be a different
            // unit.
            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "TurnoverIntradayFetched",
                session.Name,
                session.Day,
                session.Count,
                TurnoverRenderer.Round(session.TotalYi),
                Strings.Get("TurnoverUnit")));
        }, TimeSpan.FromMinutes(2));
    }

    /// <summary>Which string says why an instrument could not be drawn minute by minute.</summary>
    private static string DenialKey(IntradayDenial denial) => denial switch
    {
        IntradayDenial.NoAmount => "TurnoverIntradayNoAmount",
        IntradayDenial.TooFew => "TurnoverIntradayTooFew",
        _ => "TurnoverIntradayNone",
    };

    /// <summary>
    /// Hides the range controls on the intraday form, where they would be a promise the page
    /// cannot keep: the source holds five sessions and a picker offering dates beyond them
    /// answers with a day that has already been dropped.
    /// </summary>
    private void SyncRangeVisibility()
    {
        var intraday = Chosen == View.Intraday;

        RangeCombo.Visibility = intraday ? Visibility.Collapsed : Visibility.Visible;

        CustomRange.Visibility = !intraday && RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 }
            ? Visibility.Visible
            : Visibility.Collapsed;
    }

    /// <summary>
    /// The list changed, so whatever is on the stage no longer describes it.
    ///
    /// Dropped rather than left standing: a board drawn from five codes under a caption saying
    /// four is a plausible picture of the wrong basket, and nothing on the frame would say so.
    /// </summary>
    private void OnWatchChanged(object sender, EventArgs e)
    {
        _series = null;
        _session = null;

        ApplyPreviewSettings();
    }

    /// <summary>
    /// Moves the preview and the scrub bar together, without the slider's own handler
    /// stopping the playback that might be driving it.
    /// </summary>
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
        // Built in the constructor before CustomRange has been reached by the
        // loader on the very first pass, so the null check is not defensive
        // decoration — the selection assignment above raises this.
        if (CustomRange is null)
        {
            return;
        }

        SyncRangeVisibility();

        SavePreferences();
    }

    /// <summary>
    /// Switching the form redraws from the series already in hand. Deliberately not a re-fetch:
    /// the two forms are two pictures of the same numbers, and going back to the network would
    /// spend a round trip to arrive at what is already here.
    /// </summary>
    private void OnViewChanged(object sender, SelectionChangedEventArgs e)
    {
        // Raised by the selection assignment in the constructor, before the rest of the page's
        // controls have been built.
        if (VideoSettings is null || Preview is null)
        {
            return;
        }

        // Bars and calendar are two pictures of one series, so switching between them redraws
        // from what is already here. The intraday form is not: it reads a different endpoint, so
        // moving onto or off it drops what is in hand instead of drawing the wrong axis over it.
        if (!_prefs.Restoring)
        {
            if (Chosen == View.Intraday)
            {
                _series = null;
            }
            else
            {
                _session = null;
            }
        }

        SyncRangeVisibility();

        ApplyPreviewSettings();
        SavePreferences();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e)
    {
        // Moving the slider is an instruction to look at a moment, which means
        // stopping wherever the playback had got to. Letting both drive the
        // position would make the thumb fight the person holding it.
        //
        // Seeking rather than only stopping, because the press that follows starts from
        // the frame on screen. Stopping left the slider's position in the preview and the
        // playback's own position on the stopwatch, so playing after a drag jumped the
        // picture away from the moment someone had just chosen.
        _playback?.Seek(Scrub.Value);
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
        // reads as a broken one. Starting again is what the press meant: these clips run
        // for a minute or two, so watching one twice is an ordinary thing to do.
        //
        // Through the seek rather than by setting the preview's progress directly, so that
        // the position playback counts from is the position the picture is showing. Two
        // places to put the position are two places to disagree about it.
        if (!_playback.IsPlaying && Preview.Progress >= 0.999)
        {
            _playback.Seek(0);
        }

        _playback.Toggle();
    }

    /// <summary>
    /// Called by <see cref="Playback"/> as it advances, and once when it stops. Explicit, so
    /// driving the preview stays between this page and its playback rather than becoming part
    /// of the page's public surface.
    /// </summary>
    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) => SetPlaybackState(playing);

    /// <summary>
    /// Points the button at what it will do next: ▶ to run the animation, ⏸ to hold it.
    ///
    /// An icon carries no text of its own, so the same word that picks the glyph is put on
    /// the tooltip and on the name a screen reader announces. Without that the button is
    /// unnamed, and "unnamed button" is what a reader has to say about a control whose
    /// whole meaning is a shape.
    /// </summary>
    private void SetPlaybackState(bool playing)
    {
        var label = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

        PlayIcon.Glyph = playing ? "\uE769" : "\uE768";

        ToolTipService.SetToolTip(PlayButton, label);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    /// <summary>
    /// Renders and encodes the whole animation to an MP4.
    /// </summary>
    /// <summary>
    /// The first and last day of whatever is on the stage, whichever form is showing.
    ///
    /// One method because three places need it and each of them would otherwise have to know
    /// that the intraday form keeps its day as text while the daily forms keep theirs as dates —
    /// and a file name built from the wrong one is a file that sorts into the wrong year.
    /// </summary>
    private (DateOnly From, DateOnly To)? SeriesRange()
    {
        if (Chosen == View.Intraday)
        {
            return _session is { } session && DateOnly.TryParse(session.Day, out var day)
                ? (day, day)
                : null;
        }

        return _series is { } series ? (series.Dates[0], series.Dates[^1]) : null;
    }

    /// <summary>What the frame is called when no title has been typed, on whichever form.</summary>
    private string DefaultLabel() =>
        Chosen == View.Intraday
            ? Strings.Get("TurnoverIntradayStageTitle")
            : Metric.Turnover.DefaultTitle();

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || SeriesRange() is not { } range || App.Window is not { } window)
        {
            return;
        }

        // One gate, asked by every page. Writing the file — as opposed to
        // drawing it — is what the subscription buys, and the one place allowed
        // to answer that is asked before anything is read for the encode.
        if (!await MarketMotionStudio.Views.SubscriptionOffer.PermitAsync(XamlRoot, window))
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;

        // Read before the work starts. Everything the encoder needs is captured up front so that
        // touching a slider mid-export cannot change the format halfway through the file.
        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : DefaultLabel();

        CancelButton.IsEnabled = true;

        // Generous, and proportional to what is being asked for: a 1440p sixty-second video is a real
        // amount of encoding. The timeout is a backstop against a wedged pipeline, not a schedule.
        var limit = TimeSpan.FromMinutes(5) + (duration * 4);

        Diagnostics.CrashLog.Note($"export: clicked, {format.Width}x{format.Height} dur={duration}");

        await RunAsync(ExportButton, async cancellation =>
        {
            Diagnostics.CrashLog.Note("export: inside RunAsync, resolving folder");

            var folder = await OutputFolder.TryGetAsync() ?? await OutputFolder.ChooseAsync(window);

            Diagnostics.CrashLog.Note($"export: folder = {folder?.Path ?? "(null)"}");

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
                VideoExporter.VideoName(label, range.From, range.To, format),
                report, cancellation);

            clock.Stop();

            var properties = await file.GetBasicPropertiesAsync();

            // The elapsed time is reported next to the video's own length, because the ratio between
            // them is the claim this whole design was built to make. If it is not under 1.0, something
            // is pacing on a clock.
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

    /// <summary>
    /// Saves the frame currently on screen as a full-resolution PNG.
    /// </summary>
    private async void OnSaveCover(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || SeriesRange() is not { } range || App.Window is not { } window)
        {
            return;
        }

        await RunAsync(CoverButton, async cancellation =>
        {
            // Asks the first time and remembers, so a run of covers costs one dialog. A packaged app
            // cannot write wherever it likes, which is why this is a picker rather than a path.
            var folder = await OutputFolder.TryGetAsync() ?? await OutputFolder.ChooseAsync(window);

            if (folder is null)
            {
                ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioCoverCancelled"));
                return;
            }

            var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : DefaultLabel();

            var format = VideoSettings.Format;

            var file = await FrameExporter.SavePngAsync(
                renderer, format, VideoSettings.Margins, Preview.Progress, folder,
                FrameExporter.CoverName(label, range.From, range.To, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    /// <summary>
    /// Puts back what was chosen last time, and starts saving changes afterwards.
    ///
    /// The restore flag covers the whole of this, including the assignments made to the page's own
    /// controls — each of those raises its handler, and a handler that writes while the restore is
    /// still running saves a half-restored state over the one being read.
    /// </summary>
    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var months = _prefs.GetInt("Months", 3);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 1;

        var view = _prefs.GetInt("View", (int)View.Bars);
        ViewCombo.SelectedIndex = view >= 0 && view < Views.Length ? view : 0;

        // By tag rather than by value: the combo's order groups the boards by exchange for
        // reading, which is not the enum's order, and an index saved as one would be read as
        // the other.
        var scope = _prefs.GetInt("Scope", (int)MarketScope.Whole);
        var scopeAt = Enum.IsDefined(typeof(MarketScope), scope)
            ? Array.FindIndex(Scopes, s => (int)s.Scope == scope)
            : -1;
        ScopeCombo.SelectedIndex = scopeAt >= 0 ? scopeAt : 0;

        if (DateTime.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = from;
        }

        if (DateTime.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = to;
        }

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 3);
        _prefs.Save("View", (int)Chosen);
        _prefs.Save("Scope", (int)ChosenScope);
        _prefs.Save("From", FromDate.Date.ToString("O"));
        _prefs.Save("To", ToDate.Date.ToString("O"));

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
