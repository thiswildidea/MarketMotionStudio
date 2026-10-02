using System.Collections.ObjectModel;
using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The extreme-day board: one instrument, and its largest single-day moves, ranked by size.
///
/// The eleventh page and the fourth on the horizontal race — and the one that turns the race
/// inside out. Every other board gives a row a value that changes day by day; this one gives a
/// row a value that never changes, because **the row is a day**. What moves is the membership:
/// a day is worth nothing until it happens, so the board fills in as the years pass, and a day
/// larger than the fifteenth takes its place and pushes someone off the bottom.
///
/// Three things the renderer is asked for that no other page asks for, and why:
///
/// **Rank by magnitude.** A board of moves is board of *moves*: −7.7% belongs next to +8.1%.
/// Ranking the signed values would file every fall below every rise, however small the rise,
/// and the board would be a list of good days with the crashes filed underneath.
///
/// **Leave the empty rows out.** Before its day arrives a row is worth zero, and twenty-four
/// candidates of which five have happened still fill a fifteen-row frame — ten rows reading
/// 0.00% is what the first month of the video would look like without this.
///
/// **Colour by sign.** One colour per row is how a viewer follows a company up a market-cap
/// board; a day is not a thing to follow. So the bar is red for a rise and green for a fall,
/// which is also how the value label beside it already reads.
///
/// The change is the change in the **adjusted** close. For an index that is the index; for a
/// single stock it is the total return, so a stock going ex-dividend does not show a fall that
/// nobody suffered. An unadjusted series would put that fall at the top of the board.
///
/// **Any instrument the market quotes, not only the broad indices.** The board is one
/// instrument's own days, and "what were its largest days" is asked about single stocks and
/// funds at least as often as about an index — so the page carries the same suggesting box the
/// candle and calendar pages carry, the broad indices underneath it as one tap each rather than
/// as the boundary of the page, and the same watchlist for the same reason a favourite exists
/// at all: it is a fact about the instrument, not about the page it was added on. Two things a
/// reader meets only once a stock is allowed, both already true of the numbers and neither a
/// special case: a limit-rule day is the day a stock's board is mostly made of, and a listing
/// shorter than <see cref="ExtremeDayBoard.FewestDays"/> trading days has no board to draw.
/// </summary>
public sealed partial class ExtremeDaysPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("ExtremeDays.");

    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    /// <summary>
    /// The per-stock page's preference container, used for the watchlist key only. The watchlist
    /// is one list shared by every page that names one instrument — a favourite is a fact about
    /// the instrument, not about the page it was added on — so it is read and written under that
    /// page's prefix deliberately, the same way the candle and calendar pages do it.
    /// </summary>
    private readonly StudioPreferences _watchlist = new("Stock.");

    private readonly ObservableCollection<StockFavourite> _favourites = [];

    /// <summary>
    /// The instrument the series in hand was fetched for, or null before anything has been
    /// fetched. A favourite is added out of the fetch rather than out of the box, because the
    /// name only exists once the source has answered — a favourite without one is a code nobody
    /// recognises a month later.
    /// </summary>
    private RaceEntry? _fetched;

    private SectorRaceSeries? _series;

    /// <summary>
    /// The instrument the board is drawn on. The search sets it to anything the market quotes —
    /// a stock, a fund or an index — and the list below is a shortcut to the usual ones, not
    /// the limit. Held as a code and a name rather than read back off the list, because most of
    /// the things a person can choose are not on the list.
    /// </summary>
    private string _instrumentCode = string.Empty;

    private string _instrumentName = string.Empty;

    private StockSuggestion? _pendingChoice;

    private string _lastQuery = string.Empty;

    private readonly DispatcherTimer _searchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    /// <summary>
    /// -1 is the custom span and 0 is "as far back as the source goes", which is what the plan
    /// and holding pages already mean by 0.
    /// </summary>
    private const int CustomMonths = -1;

    private static readonly (int Months, string Key)[] Ranges =
    [
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (120, "DcaRange10Y"),
        (0, "ExtremeDaysRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    public ExtremeDaysPage()
    {
        InitializeComponent();

        // The market's broad indices: an index is the instrument whose single-day move is a
        // sentence about the market, so they lead. One tap each, and still a shortcut rather
        // than the limit — the search box above them takes any code the market quotes, and most
        // of what this page can be pointed at is not one of these.
        foreach (var entry in _market.BroadIndices)
        {
            Presets.Items.Add(new MatrixPreset(entry.Code, InstrumentNames.Display(entry.Code, entry.Name)));
        }

        Favourites.ItemsSource = _favourites;

        _searchDebounce.Tick += async (_, _) =>
        {
            _searchDebounce.Stop();
            await SearchSuggestionsAsync();
        };

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // Ten years: long enough to carry a crash and a rally, short enough that the board is
        // not twenty years of 1990s limit-rule days with nothing recent on it.
        RangeCombo.SelectedIndex = 2;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-5);
        ToDate.Date = today;

        // Formatted, because the string names the number of rows the frame draws. Read with
        // `Strings.Get` the card showed a literal "{0}" — the same defect the A+H page had.
        ListText.Text = Strings.Format("ExtremeDaysCount", ExtremeDayBoard.Board);

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

        // Named before it has ever been pressed: the button is an icon, so the tooltip and the
        // name a screen reader announces are the only words it has.
        SetPlaybackState(playing: false);

        _prefs.Restoring = true;
        VideoSettings.Restore(_prefs);
        RestorePreferences();
        _prefs.Restoring = false;

        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("ExtremeDaysPageTitle.Text");

    /// <summary>“极端交易日” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("ExtremeDaysPageTitle.Text");

    /// <summary>
    /// The board's one instrument, whichever way it was chosen. The name is what the frame
    /// captions itself with and what the fetch announces, so it is carried as it was chosen
    /// rather than looked up — a code typed by hand has no entry to look one up in.
    /// </summary>
    private RaceEntry ChosenInstrument() => new(_instrumentCode, _instrumentName);

    private string ChosenInstrumentName() =>
        _instrumentName.Length > 0
            ? InstrumentNames.Display(_instrumentCode, _instrumentName)
            : _instrumentCode;

    /// <summary>
    /// Sets the instrument without fetching: the button still decides when the source is asked,
    /// and choosing a stock is not a request to wait on one.
    ///
    /// Whatever was fetched goes with it. A board belongs to the instrument it was fetched for,
    /// and leaving one standing under another instrument's name is a sentence about a stock that
    /// no pixel of the frame admits is about a different one. Same rule as the candle page.
    /// </summary>
    private void ChooseInstrument(string code, string name)
    {
        _instrumentCode = code;
        _instrumentName = InstrumentNames.Display(code, name);

        _series = null;
        _fetched = null;

        SavePreferences();
        ApplyPreviewSettings();
    }

    // ---- the usual ones, and the watchlist ----------------------------------------------

    /// <summary>One of the market's broad indices, tapped.</summary>
    private void OnPresetClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is string code)
        {
            var name = Presets.Items.OfType<MatrixPreset>().FirstOrDefault(p => p.Code == code)?.Name ?? code;
            ChooseInstrument(code, name);
        }
    }

    /// <summary>Serialised as `code|name;…` under the shared watchlist key — see <see cref="_watchlist"/>.</summary>
    private const string FavouriteKey = "Favourites";

    private void LoadFavourites()
    {
        var raw = _watchlist.GetString(FavouriteKey, string.Empty);

        foreach (var item in raw.Split(';', StringSplitOptions.RemoveEmptyEntries))
        {
            var parts = item.Split('|');

            if (parts.Length == 2 && parts[0].Length > 0)
            {
                _favourites.Add(new StockFavourite(parts[0], parts[1]));
            }
        }
    }

    private void SaveFavourites()
    {
        _watchlist.Save(FavouriteKey, string.Join(";", _favourites.Select(f => $"{f.Code}|{f.Name}")));
    }

    private void OnAddFavourite(object sender, RoutedEventArgs e)
    {
        if (_fetched is not { } fetched)
        {
            // The name comes with the fetch and cannot be guessed before it: a favourite is a
            // code and a name, and a list of bare codes is a list nobody can read later.
            ShowStatus(InfoBarSeverity.Informational, Strings.Get("StockFavNeedData"));
            return;
        }

        if (_favourites.Any(f => f.Code == fetched.Code))
        {
            return;
        }

        _favourites.Add(new StockFavourite(fetched.Code, fetched.Name));
        SaveFavourites();
    }

    private void OnFavouriteClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is string code)
        {
            var name = _favourites.FirstOrDefault(f => f.Code == code)?.Name ?? code;
            ChooseInstrument(code, name);
        }
    }

    private void OnFavouriteRemove(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is not string code)
        {
            return;
        }

        var at = _favourites.ToList().FindIndex(f => f.Code == code);

        if (at >= 0)
        {
            _favourites.RemoveAt(at);
            SaveFavourites();
        }
    }

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            // The race renderer on its **return** metric: a move is a percentage, and that is
            // the metric whose labels end in %. `showTop`: twenty-four candidate days race for
            // fifteen places. The three flags are this page's own — see the note on the class.
            // `rankByMagnitude` as the constructor's argument, not as a property set below: the
            // ranking table is built inside the constructor, so an initialiser would be read too
            // late and the frame would be sorted by sign — see the note on that parameter.
            Preview.Renderer = new SectorRaceRenderer(
                series, RaceMetric.Return, VideoSettings.Duration, ExtremeDayBoard.Board,
                rankByMagnitude: true)
            {
                Title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle(),
                ShowTitle = VideoSettings.ShowTitle,
                ListLabel = ChosenInstrumentName(),
                UnitWord = Strings.Get("ExtremeDaysUnitCandidates"),

                // Daily, so the header counts trading days — the renderer's own fallback is the
                // same string, and the page says it because the page is what chose the interval.
                SpanWord = Strings.Get("StockTradingDaysUnit"),
                HideEmptyRows = true,
                ColourBySign = true,
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("ExtremeDaysStageTitle");
            _stage.ShowTitle = VideoSettings.ShowTitle;
            Preview.Renderer = _stage;
        }

        var ready = _series is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    // ---- search -------------------------------------------------------------------------

    private void OnSearchTextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        // Only a typed change asks for suggestions; choosing one assigns the text in code.
        if (args.Reason is not AutoSuggestionBoxTextChangeReason.UserInput)
        {
            return;
        }

        _lastQuery = sender.Text;
        _searchDebounce.Stop();
        _searchDebounce.Start();
    }

    /// <summary>
    /// Suggestions while a person types; a code, a Chinese name or pinyin all resolve. Filtered
    /// to the market in force, so a suggestion that would be refused on fetch never appears.
    /// </summary>
    private async Task SearchSuggestionsAsync()
    {
        var query = _lastQuery.Trim();

        if (query.Length == 0)
        {
            InstrumentSearch.ItemsSource = null;
            return;
        }

        try
        {
            var found = await Services.Stocks.SearchAsync(query, _market, CancellationToken.None);

            InstrumentSearch.ItemsSource = found
                .Where(r => _market.Accepts(r.Code))
                .Take(12)
                .Select(r => new StockSuggestion(r.Code, r.Name, r.Code[..2].ToUpperInvariant()))
                .ToArray();
        }
        catch (Exception)
        {
            // A failed suggestion list is a quiet failure: the person is still typing, and a
            // status line flashing under every keystroke is worse than no suggestions.
            InstrumentSearch.ItemsSource = null;
        }
    }

    private void OnSuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        // Held rather than read from the submit event's args — this projection of AutoSuggestBox
        // does not carry ChosenItem there, and the field survives either way.
        if (args.SelectedItem is StockSuggestion chosen)
        {
            _pendingChoice = chosen;
            sender.Text = chosen.Display;
        }
    }

    private void OnSearchSubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args)
    {
        if (_pendingChoice is { } pick)
        {
            _pendingChoice = null;
            ChooseInstrument(pick.Code, pick.Name);
            return;
        }

        var code = StockDirectory.Normalize(sender.Text);

        if (code is null)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("StockBadCode"));
            return;
        }

        // A code the normalizer can read but the market in force does not quote: the reader's
        // next step is different from the one above, so it says which market.
        if (!_market.Accepts(code))
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("WrongMarket", _market.Name));
            return;
        }

        ChooseInstrument(code, code);
    }

    // ---- range ---------------------------------------------------------------------------

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CustomRange is null)
        {
            return;
        }

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } && months == CustomMonths;

        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        if (RangeCombo.SelectedItem is ComboBoxItem { Tag: int months })
        {
            var today = DateOnly.FromDateTime(DateTime.Now);

            if (months > 0)
            {
                return (today.AddMonths(-months), today);
            }

            if (months == 0)
            {
                // "As far back as there is" — asked for generously and trimmed by the walk,
                // which is the only thing that knows where the source's history starts.
                return (today.AddYears(-30), today);
            }
        }

        return (
            DateOnly.FromDateTime(FromDate.Date.DateTime),
            DateOnly.FromDateTime(ToDate.Date.DateTime));
    }

    // ---- fetching ------------------------------------------------------------------------

    private void OnFetch(object sender, RoutedEventArgs e)
    {
        var (start, end) = ChosenRange();

        if (start >= end)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
            return;
        }

        if (end.DayNumber - start.DayNumber > HistoryWalk.MostDays)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("TurnoverRangeTooLong", HistoryWalk.MostDays));
            return;
        }

        _ = RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("SectorFetching", message)));

            var series = await ExtremeDaySeries.LoadAsync(
                Services.Quotes, _market, ChosenInstrument(), start, end, progress, cancellation);

            _series = series;

            // What a favourite needs, and the only moment both halves of it exist: the code the
            // page settled on and the name the frame is captioned with. The loader answers with
            // days rather than with an instrument, so it can supply neither.
            _fetched = new RaceEntry(_instrumentCode, ChosenInstrumentName());

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = ExtremeDaySeries.ByMagnitude(series);
            var biggest = standings[0];

            // The largest and the smallest **of the fifteen the frame draws**, not of the field:
            // the field holds days the board never shows, and "the smallest move" naming a day
            // nobody can see is a sentence about the data rather than about the picture.
            var smallest = standings[Math.Min(ExtremeDayBoard.Board, standings.Length) - 1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "ExtremeDaysFetched",
                series.Racers,
                series.Days,
                series.Entries[biggest.Index].Name,
                FormatValue(biggest.Value),
                series.Entries[smallest.Index].Name,
                FormatValue(smallest.Value)));
        }, TimeSpan.FromMinutes(6));
    }

    private static string FormatValue(double value) =>
        (value >= 0 ? "+" : "−") + Math.Abs(value).ToString("0.00", CultureInfo.InvariantCulture) + "%";

    // ---- preview transport -----------------------------------------------------------------

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
        // Moving the slider is an instruction to look at one moment, which means stopping the
        // playback wherever it had got to. See the longer note on MarketTurnoverPage.
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

    // ---- export -----------------------------------------------------------------------------

    private string CapFileName(VideoFormat format, string extension)
    {
        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle();

        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        if (safe.Length > 40)
        {
            safe = safe[..40];
        }

        return $"{safe}_{_series!.Dates[0]:yyyy-MM-dd}_{_series.Dates[^1]:yyyy-MM-dd}_{format.NameSuffix}.{extension}";
    }

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _series is null || App.Window is not { } window)
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
                CapFileName(format, "mp4"),
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
        if (Preview.Renderer is not { } renderer || _series is null || App.Window is not { } window)
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
                CapFileName(format, "png"),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    // ---- persistence ---------------------------------------------------------------------------

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Code", _instrumentCode);
        _prefs.Save("Name", _instrumentName);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        var code = _prefs.GetString("Code", _market.BroadIndices[0].Code);

        // The name as it was spelled when it was chosen. Most of the things this page can be
        // pointed at are not one of the usual ones, so the name is remembered rather than looked
        // up — a code alone would caption the frame with a code. Nothing is highlighted in the
        // row of buttons for the same reason: they are shortcuts, and most of what this page
        // draws is not on them.
        //
        // A code saved under another market is not carried over: it would fetch from a venue
        // whose suggestions this page no longer shows.
        if (_market.Accepts(code))
        {
            _instrumentCode = code;

            var name = _prefs.GetString("Name", string.Empty);

            _instrumentName = name.Length > 0 ? InstrumentNames.Display(code, name) : code;
        }
        else
        {
            _instrumentCode = _market.BroadIndices[0].Code;
            _instrumentName = InstrumentNames.Display(_market.BroadIndices[0].Code, _market.BroadIndices[0].Name);
        }

        var months = _prefs.GetInt("Months", 120);
        var match = RangeCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is int m && m == months);

        if (match is not null)
        {
            RangeCombo.SelectedItem = match;
        }

        if (DateOnly.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = new DateTimeOffset(from, TimeOnly.MinValue, TimeSpan.Zero);
        }

        if (DateOnly.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = new DateTimeOffset(to, TimeOnly.MinValue, TimeSpan.Zero);
        }

        LoadFavourites();
    }
}
