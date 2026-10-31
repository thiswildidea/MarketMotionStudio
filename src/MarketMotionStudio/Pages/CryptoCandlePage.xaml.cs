using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Automation;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// A coin's candles, drawn by the stock candle page's own renderer.
///
/// Two things are this page's and not the stock page's. **The weekly and monthly
/// candles are made here** rather than asked for, because neither source serves them —
/// see <see cref="CryptoCandleLoader"/>. And **the minute periods are asked for a day
/// rather than for a span**: a coin's minutes reach back days where its history reaches
/// back years, so the panel names a day and the source answers that day's hours — where
/// the stock page's minute endpoint keeps the last few sessions and names them itself,
/// leaving the reader to pick from what happened to survive.
///
/// The four styles are the stock page's four, with one condition: a candle and a bar
/// are shapes drawn out of four prices, and the fallback source has one. Offered anyway
/// they would draw a body and two wicks out of a single close — a shape the coin never
/// made, on every frame. So the two shapes that need four prices fall back to a line
/// when that is what arrived, and the note under the control says which.
///
/// More than one coin is the other picture the stock page draws: their prices have no
/// common axis, so a frame of several draws what each did as a percentage. Same board,
/// same renderer — <see cref="CandleRaceRenderer"/>.
/// </summary>
public sealed partial class CryptoCandlePage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>Marks the two typed dates in the span list.</summary>
    private const int CustomMonths = -1;

    /// <summary>
    /// The periods, daily ones first.
    ///
    /// The three minute ones are listed on every machine and switched off where the
    /// source in force cannot serve them, for the reason the stock page gives for the
    /// same thing: a list that changes length between markets asks where the others
    /// went, and three entries that can only ever fail are worse than three that say
    /// why they are off. See <see cref="RefreshMinutePeriods"/>.
    /// </summary>
    private static readonly (CandlePeriod Period, string Key)[] Periods =
    [
        (CandlePeriod.Daily, "CandlePeriodDaily"),
        (CandlePeriod.Weekly, "CandlePeriodWeekly"),
        (CandlePeriod.Monthly, "CandlePeriodMonthly"),
        (CandlePeriod.Minute1, "CandlePeriodMinute1"),
        (CandlePeriod.Minute5, "CandlePeriodMinute5"),
        (CandlePeriod.Minute15, "CandlePeriodMinute15"),
    ];

    private readonly StudioPreferences _prefs = new("CryptoCandle.");

    private static readonly (CandleStyle Style, string Key)[] Styles =
    [
        (CandleStyle.Candles, "CandleStyleCandles"),
        (CandleStyle.Bars, "CandleStyleBars"),
        (CandleStyle.Line, "CandleStyleLine"),
        (CandleStyle.Area, "CandleStyleArea"),
    ];

    private const int DefaultWindow = 60;

    private const int MinWindow = 10;

    private const int MaxWindow = 500;

    private CandleSeries? _fetched;

    private CandleBoard? _board;

    /// <summary>The coin and its name, for a title that has to exist before a fetch.</summary>
    private string _instrumentName = CryptoAsset.All[0].Display;

    private bool _ready;

    private bool _filling;

    public CryptoCandlePage()
    {
        InitializeComponent();

        foreach (var (period, key) in Periods)
        {
            PeriodCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = period });
        }

        PeriodCombo.SelectedIndex = 0;

        // The day the minute periods draw, bounded now and re-bounded whenever the
        // period changes: each of the three reaches a different distance, and a picker
        // offering a day the source will refuse is a picker that fails.
        DayPicker.MinYear = DateTimeOffset.Now.AddDays(-(CryptoQuotes.MinuteDays - 1));
        DayPicker.MaxYear = DateTimeOffset.Now;
        DayPicker.Date = DateTimeOffset.Now;

        // Named here rather than in the markup, because `x:Uid` does not put an
        // AutomationId on a control: it names the resource the text comes from, and a
        // script that looks the control up by id has to have one put on it explicitly.
        // `x:Name` does not do it either — the picker above proves it, and a script that
        // cannot find the period list cannot tell six periods from three.
        AutomationProperties.SetAutomationId(DayPicker, "CryptoMinuteDay");
        AutomationProperties.SetAutomationId(DayNote, "CryptoMinuteNote");
        AutomationProperties.SetAutomationId(PeriodCombo, "CryptoPeriodCombo");
        AutomationProperties.SetAutomationId(RangeCombo, "CryptoRangeCombo");

        // The minute periods' reach is a fact about the source, and the source is not
        // known until it has been asked — which happens while this page is already on
        // screen. Asked again here so the list a person is looking at matches the one
        // the fetch will use; the answer is cached, so on every visit after the first
        // this returns at once.
        _ = RefreshMinutePeriodsAsync();

        foreach (var (style, key) in Styles)
        {
            StyleCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = style });
        }

        StyleCombo.SelectedIndex = 0;

        foreach (var (motion, key) in new[]
                 {
                     (CandleMotion.Grow, "CandleMotionGrow"),
                     (CandleMotion.Scroll, "CandleMotionScroll"),
                 })
        {
            MotionCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)motion });
        }

        MotionCombo.SelectedIndex = 0;

        var now = DateTimeOffset.Now;
        var oldest = now.AddDays(-CryptoQuotes.YahooMostDays);

        FromDate.MinYear = oldest;
        FromDate.MaxYear = now;
        ToDate.MinYear = oldest;
        ToDate.MaxYear = now;

        Coins.Changed += OnCoinsChanged;

        VideoSettings.AllowHideTitle = false;
        VideoSettings.AllowTitleText = false;
        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            SavePreferences();
        };

        TitlePanel.Changed += (_, _) =>
        {
            VideoSettings.SetTitleText(TitlePanel.TitleText);
            ApplyPreviewSettings();
            SavePreferences();
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        SetPlaybackState(playing: false);

        RestorePreferences();

        // After the preferences, because the period they restore is what fills the list
        // of spans — and the span they restore is one of that list's entries.
        FillRanges();
        ApplyPreviewSettings();

        _ready = true;
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("CryptoCandlePageTitle.Text");

    // ---- what is being drawn ---------------------------------------------------------

    private IReadOnlyList<RaceEntry> Chosen() => [.. Coins.Selected];

    private void OnCoinsChanged(object? sender, EventArgs e)
    {
        _fetched = null;
        _board = null;

        var names = Chosen().Select(e => InstrumentNames.Display(e.Code, e.Name)).ToArray();

        if (names.Length > 0)
        {
            _instrumentName = names[0];
        }

        SavePreferences();
        ApplyPreviewSettings();
    }

    // ---- the terms -------------------------------------------------------------------

    private CandlePeriod ChosenPeriod() =>
        PeriodCombo.SelectedItem is ComboBoxItem { Tag: CandlePeriod period } ? period : CandlePeriod.Daily;

    private int ChosenMonths() =>
        RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 12;

    private CandleMotion ChosenMotion() =>
        MotionCombo.SelectedItem is ComboBoxItem { Tag: int motion }
            ? (CandleMotion)motion
            : CandleMotion.Grow;

    /// <summary>
    /// The style asked for, read down to one the bars in hand can carry.
    ///
    /// A candle and a bar are drawn from four prices. The fallback source has one, and a
    /// body and two wicks made out of a single close is a shape the coin never made — so
    /// the two shapes that need four fall to a line rather than drawing a lie on every
    /// frame. See <see cref="CryptoQuotes.GivesCandles"/>.
    /// </summary>
    private CandleStyle ChosenStyle()
    {
        var style = StyleCombo.SelectedItem is ComboBoxItem { Tag: CandleStyle chosen }
            ? chosen
            : CandleStyle.Candles;

        if (!Services.Crypto.GivesCandles && style is CandleStyle.Candles or CandleStyle.Bars)
        {
            return CandleStyle.Line;
        }

        return style;
    }

    private bool CrossSafeRight() => CrossCheck.IsChecked is true;

    private int ChosenWindow()
    {
        var text = WindowBox.Text.Trim();

        var window = int.TryParse(text, NumberStyles.Integer, CultureInfo.CurrentUICulture, out var parsed) ? parsed
            : int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out parsed) ? parsed
            : DefaultWindow;

        return Math.Clamp(window, MinWindow, MaxWindow);
    }

    private static DateOnly Oldest =>
        DateOnly.FromDateTime(DateTime.Now).AddDays(-CryptoQuotes.YahooMostDays);

    private (DateOnly From, DateOnly To) CustomSpan() =>
        (DateOnly.FromDateTime(FromDate.Date.DateTime), DateOnly.FromDateTime(ToDate.Date.DateTime));

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = ChosenMonths();
        var today = DateOnly.FromDateTime(DateTime.Now);

        if (months == CustomMonths)
        {
            var (from, to) = CustomSpan();

            return (from, to > today ? today : to);
        }

        return months == 0 ? (Oldest, today) : (today.AddMonths(-months), today);
    }

    /// <summary>
    /// The day the minute periods draw, read off the picker.
    ///
    /// Not a field, for the reason <see cref="ChosenPeriod"/> is not one: a control
    /// showing one day while a fetch uses another is a disagreement that costs an
    /// afternoon to find, and reading it costs nothing.
    /// </summary>
    private DateOnly ChosenDay() => DateOnly.FromDateTime(DayPicker.Date.DateTime);

    private void OnDayChanged(object sender, DatePickerValueChangedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        // Another day is another chart, not a redraw of the last one: the whole series
        // is different and the old one answers nothing about it.
        _fetched = null;
        _board = null;

        SavePreferences();
        ApplyPreviewSettings();
    }

    /// <summary>
    /// Switches the three minute periods on or off to match the source in force, once the
    /// source is known.
    ///
    /// Only the fallback turns them off: it carries a day and a price, has no intraday
    /// series at all, and a minute chart folded out of days would be a shape the coin
    /// never made. Yahoo carries all three grains.
    ///
    /// Asked again here rather than only in the constructor because the source is decided
    /// by a request, and the request finishes while this page is already on the screen.
    /// The answer is cached, so every visit after the first returns at once.
    /// </summary>
    private async Task RefreshMinutePeriodsAsync()
    {
        await Services.Crypto.ReachableAsync();

        DispatcherQueue.TryEnqueue(RefreshMinutePeriods);
    }

    private void RefreshMinutePeriods()
    {
        var offered = Services.Crypto.GivesCandles;

        foreach (var item in PeriodCombo.Items)
        {
            if (item is not ComboBoxItem { Tag: CandlePeriod period } box || !CandleLoader.IsMinute(period))
            {
                continue;
            }

            box.IsEnabled = offered;

            ToolTipService.SetToolTip(box, offered ? null : Strings.Get("CryptoMinuteSourceNone"));
        }

        // A period switched off while it is the one selected is moved off rather than
        // left: the list would say one thing and the fetch another, and what the fetch
        // would answer is an exception out of a source that has no such series — not a
        // sentence anyone can act on.
        if (!offered && CandleLoader.IsMinute(ChosenPeriod()))
        {
            PeriodCombo.SelectedIndex = 0;
        }
    }

    /// <summary>
    /// How far back the day picker may go, in days, for the period in force.
    ///
    /// The finest grain reaches least: eight days of one-minute candles, sixty of
    /// five- and fifteen-minute ones — both the source's own numbers rather than ours;
    /// see <see cref="CryptoQuotes.Minute1Days"/>.
    /// </summary>
    private static int Reach(CandlePeriod period) =>
        period == CandlePeriod.Minute1 ? CryptoQuotes.Minute1Days : CryptoQuotes.MinuteDays;

    /// <summary>
    /// The spans the period in force offers — its own list, because a span is counted in
    /// months and read in candles: a decade of days is three thousand six hundred of
    /// them and a decade of months is a hundred and twenty.
    ///
    /// On a minute period there are no spans to offer and the whole control is swapped
    /// for the day picker, which is the question those periods are actually asked.
    /// </summary>
    private void FillRanges()
    {
        var minute = CandleLoader.IsMinute(ChosenPeriod());

        RangeCombo.Visibility = minute ? Visibility.Collapsed : Visibility.Visible;
        MinuteRange.Visibility = minute ? Visibility.Visible : Visibility.Collapsed;

        // The typed span belongs to the daily periods and to nothing else: on a minute
        // period the fetch reads one day, and two pickers naming a range it never looks
        // at would sit right underneath the control that replaced them.
        if (minute)
        {
            CustomRange.Visibility = Visibility.Collapsed;

            var today = DateOnly.FromDateTime(DateTime.Now);
            var oldest = today.AddDays(-(Reach(ChosenPeriod()) - 1));

            DayPicker.MinYear = new DateTimeOffset(oldest, TimeOnly.MinValue, TimeSpan.Zero);
            DayPicker.MaxYear = new DateTimeOffset(today, TimeOnly.MinValue, TimeSpan.Zero);

            // A day remembered from a wider reach than the period now chosen has is
            // clipped rather than left out of range: a picker that silently refused the
            // date it was showing is a picker that lies about where it is.
            if (ChosenDay() < oldest)
            {
                DayPicker.Date = DayPicker.MaxYear;
            }

            DayNote.Text = Strings.Format("CryptoMinuteReach", Reach(ChosenPeriod()));

            return;
        }

        _filling = true;

        // The span the preferences restored, which cannot be read off the control: the
        // list is the period's, and it is this method that fills it.
        var wanted = _months;

        RangeCombo.Items.Clear();

        foreach (var range in CandleLoader.Ranges(ChosenPeriod()))
        {
            // Zero is that list's own "as far back as the source goes", not the typed
            // span — see `ChosenRange`.
            RangeCombo.Items.Add(new ComboBoxItem
            {
                Content = Strings.Get(range.Key),
                Tag = range.Months,
            });
        }

        // The typed span, always last, and always offered: a person looking at a coin
        // asks about a day they remember.
        RangeCombo.Items.Add(new ComboBoxItem
        {
            Content = Strings.Get("StudioRangeCustom"),
            Tag = CustomMonths,
        });

        var at = 0;

        for (var i = 0; i < RangeCombo.Items.Count; i++)
        {
            if (RangeCombo.Items[i] is ComboBoxItem { Tag: int months } && months == wanted)
            {
                at = i;
                break;
            }
        }

        RangeCombo.SelectedIndex = at;

        CustomRange.Visibility = ChosenMonths() == CustomMonths
            ? Visibility.Visible
            : Visibility.Collapsed;

        _filling = false;
    }

    private void OnPeriodChanged(object sender, object e)
    {
        if (PeriodCombo is null)
        {
            return;
        }

        FillRanges();

        if (!_ready)
        {
            return;
        }

        // A new period is a new chart, not a redraw of the old one: the candles are
        // counted differently and the old ones were fetched for a different question.
        _fetched = null;
        _board = null;

        SavePreferences();
        ApplyPreviewSettings();
    }

    private void OnRangeChanged(object sender, object e)
    {
        if (_filling || !_ready)
        {
            return;
        }

        CustomRange.Visibility = ChosenMonths() == CustomMonths
            ? Visibility.Visible
            : Visibility.Collapsed;

        SavePreferences();
    }

    private void OnCustomRangeChanged(object sender, DatePickerValueChangedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        SavePreferences();
    }

    private void OnLookChanged(object sender, object e)
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
        var showTitle = !TitlePanel.HideTitle;
        var subtitle = TitlePanel.SubtitleText;
        TitlePanel.TitleText = title;
        var candles = Services.Crypto.GivesCandles;

        if (_board is { } board)
        {
            var plan = AnimationPlan.For(
                VideoSettings.Duration, board.Count,
                Math.Max(Math.Abs(board.Peak), Math.Abs(board.Trough)));

            Preview.Renderer = new CandleRaceRenderer(
                board, plan, ChosenMotion(), ChosenWindow(), CrossSafeRight(),
                TitlePanel.MainStyle, TitlePanel.SubtitleStyle)
            {
                Title = title,
                ShowTitle = showTitle,
                Subtitle = subtitle,
            };
        }
        else if (_fetched is { } fetched)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, fetched.Count, fetched.High);

            Preview.Renderer = new CandleRenderer(
                fetched, plan, ChosenStyle(), ChosenMotion(), ChosenWindow(),
                AveragesCheck.IsChecked is true, VolumeCheck.IsChecked is true && candles,
                CrossSafeRight(), TitlePanel.MainStyle, TitlePanel.SubtitleStyle)
            {
                Title = title,
                ShowTitle = showTitle,
                Subtitle = subtitle,
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = DefaultTitle();

        WindowBox.IsEnabled = ChosenMotion() is CandleMotion.Scroll;

        // A comparison draws percentages, and the four styles, the averages and the
        // volume are all ways of drawing one instrument's bars. Offered during a
        // comparison they are settings the frame silently ignores.
        StyleCombo.IsEnabled = _board is null && candles;
        AveragesCheck.IsEnabled = _board is null;
        VolumeCheck.IsEnabled = _board is null && candles;

        // Said only when it is true: the fallback answered, and two of the four shapes
        // cannot be drawn from a single close.
        StyleNote.Visibility = candles ? Visibility.Collapsed : Visibility.Visible;

        var ready = _fetched is not null || _board is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : DefaultTitle();

    private string DefaultTitle()
    {
        if (_board is { } board)
        {
            return string.Join(" / ", board.Tracks.Select(t => t.Name));
        }

        return Strings.Format(
            "CryptoCandleDefaultTitle", _instrumentName, Strings.Get(CandleLoader.NameKey(ChosenPeriod())));
    }

    // ---- fetching --------------------------------------------------------------------

    private async void Fetch()
    {
        var period = ChosenPeriod();
        var minute = CandleLoader.IsMinute(period);

        // A minute chart is one day wide by its own nature, so the span controls are not
        // read at all when one of those periods is in force — the day picker is the
        // question, and a span restored from the daily periods would be a different
        // question answered with the wrong one's dates.
        var day = ChosenDay();
        var months = ChosenMonths();
        var custom = !minute && months == CustomMonths;
        var (from, to) = minute ? (day, day) : ChosenRange();

        if (custom && from >= to)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
            return;
        }

        var chosen = Chosen();

        if (chosen.Count == 0)
        {
            // 三页同一句话：同一个选择器、同一个上限，被拒的时候说的也得是同一件事。
            // 股票那句说的是「标的」和「清单」，而这十二个是币种。
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CryptoPickOne"));
            return;
        }

        if (chosen.Count > CryptoCandleLoader.MostTracks)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format(
                "SectorTooManyStocks", CryptoCandleLoader.MostTracks));

            return;
        }

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            if (chosen.Count > 1)
            {
                var board = minute
                    ? await CryptoCandleLoader.LoadIntradayBoardAsync(
                        Services.Crypto, chosen, period, day, progress, cancellation)
                    : await CryptoCandleLoader.LoadBoardAsync(
                        Services.Crypto, chosen, period, from, to, progress, cancellation);

                if (board.Tracks.Count < 2)
                {
                    ShowStatus(InfoBarSeverity.Error, Strings.Format(
                        "PositionSkipped", board.Skipped.Count, string.Join(", ", board.Skipped)));

                    return;
                }

                _board = board;
                _fetched = null;

                ApplyPreviewSettings();
                ShowMoment(1);

                ShowFetched(minute
                    ? Strings.Format(
                        "CryptoCandleMinuteFetched",
                        board.Count,
                        Strings.Get(CandleLoader.NameKey(period)),
                        CandleLoader.Iso(day))
                    : Strings.Format(
                        "CryptoCandleBoardFetched",
                        board.Tracks.Count,
                        board.Count,
                        CandleLoader.Iso(board.Start),
                        CandleLoader.Iso(board.End)),
                    InfoBarSeverity.Success, board.Start, from,
                    Strings.Format("CryptoRangeShort", CandleLoader.Iso(board.Start)));

                return;
            }

            var fetched = minute
                ? await CryptoCandleLoader.LoadIntradayAsync(
                    Services.Crypto, chosen[0].Code, chosen[0].Name, period, day, progress, cancellation)
                : await CryptoCandleLoader.LoadAsync(
                    Services.Crypto, chosen[0].Code, chosen[0].Name, period, from, to, progress, cancellation);

            if (fetched.Count == 0)
            {
                // Named rather than thrown: a span the source holds nothing for is an
                // answer, and "no candles in it" is the honest thing to say. The two are
                // different sentences because they are different questions — one about a
                // stretch of years, one about a single day.
                ShowStatus(InfoBarSeverity.Error,
                    Strings.Get(minute ? "CryptoMinuteNone" : "CandleMinuteNone"));

                return;
            }

            _fetched = fetched;
            _board = null;
            _instrumentName = InstrumentNames.Display(fetched.Code, fetched.Name);

            ApplyPreviewSettings();
            ShowMoment(1);

            ShowFetched(minute
                ? Strings.Format(
                    "CryptoCandleMinuteFetched",
                    fetched.Count,
                    Strings.Get(CandleLoader.NameKey(period)),
                    CandleLoader.Iso(day))
                : Strings.Format(
                    "CryptoCandleFetched",
                    fetched.Count,
                    Strings.Get(CandleLoader.NameKey(period)),
                    CandleLoader.Iso(fetched.Start),
                    CandleLoader.Iso(fetched.End)),
                InfoBarSeverity.Success, fetched.Start, from,
                Strings.Format("CryptoRangeShort", CandleLoader.Iso(fetched.Start)));
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

    // ---- export ----------------------------------------------------------------------

    /// <summary>The span an export is named after, whichever of the two pictures is up.</summary>
    private (DateOnly Start, DateOnly End)? Span() =>
        _board is { } board ? (board.Start, board.End)
            : _fetched is { } fetched ? (fetched.Start, fetched.End)
            : null;

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || Span() is not { } span || App.Window is not { } window)
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
                VideoExporter.VideoName(label, span.Start, span.End, format),
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
        if (Preview.Renderer is not { } renderer || Span() is not { } span || App.Window is not { } window)
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
                FrameExporter.CoverName(ResolvedTitle(), span.Start, span.End, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences -----------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var period = _prefs.GetString("Period", CandlePeriod.Daily.ToString());
        var which = Array.FindIndex(Periods, p => p.Period.ToString() == period);
        PeriodCombo.SelectedIndex = which >= 0 ? which : 0;

        // Read before the list of spans is filled: the list is the period's, and the
        // span remembered is one of its entries.
        _months = _prefs.GetInt("Months", 12);

        var style = _prefs.GetString("Style", CandleStyle.Candles.ToString());
        var at = Array.FindIndex(Styles, s => s.Style.ToString() == style);
        StyleCombo.SelectedIndex = at >= 0 ? at : 0;

        MotionCombo.SelectedIndex = _prefs.GetInt("Motion", (int)CandleMotion.Grow) == (int)CandleMotion.Scroll ? 1 : 0;
        WindowBox.Text = Math.Clamp(_prefs.GetInt("Window", DefaultWindow), MinWindow, MaxWindow)
            .ToString(CultureInfo.InvariantCulture);

        AveragesCheck.IsChecked = _prefs.GetInt("Averages", 1) != 0;
        VolumeCheck.IsChecked = _prefs.GetInt("Volume", 1) != 0;
        CrossCheck.IsChecked = _prefs.GetInt("CrossSafeRight", 0) != 0;

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

        if (DateOnly.TryParse(_prefs.GetString("Day", string.Empty), out var day))
        {
            var stamp = new DateTimeOffset(day, TimeOnly.MinValue, TimeSpan.Zero);

            // Clipped rather than left out of range, for the reason `FillRanges` gives:
            // the reach belongs to the period in force, and a day remembered from a
            // wider one is outside it.
            DayPicker.Date = stamp < DayPicker.MinYear ? DayPicker.MinYear
                : stamp > DayPicker.MaxYear ? DayPicker.MaxYear
                : stamp;
        }

        Coins.Select(_prefs.GetString("Coins", "BTC").Split(';', StringSplitOptions.RemoveEmptyEntries));

        var names = Chosen().Select(e => InstrumentNames.Display(e.Code, e.Name)).ToArray();

        if (names.Length > 0)
        {
            _instrumentName = names[0];
        }

        VideoSettings.Restore(_prefs);
        TitlePanel.Restore(_prefs);

        _prefs.Restoring = false;
    }

    /// <summary>The span to select once the list is filled; see <see cref="FillRanges"/>.</summary>
    private int _months = 12;

    private void SavePreferences()
    {
        _prefs.Save("Period", ChosenPeriod().ToString());
        _prefs.Save("Months", ChosenMonths());
        _prefs.Save("Style", ChosenStyle().ToString());
        _prefs.Save("Motion", (int)ChosenMotion());
        _prefs.Save("Window", ChosenWindow());
        _prefs.Save("Averages", AveragesCheck.IsChecked is true ? 1 : 0);
        _prefs.Save("Volume", VolumeCheck.IsChecked is true ? 1 : 0);
        _prefs.Save("CrossSafeRight", CrossSafeRight() ? 1 : 0);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("Day", ChosenDay().ToString("yyyy-MM-dd", CultureInfo.InvariantCulture));
        _prefs.Save("Coins", string.Join(";", Chosen().Select(c => c.Code)));

        VideoSettings.Save(_prefs);
        TitlePanel.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
