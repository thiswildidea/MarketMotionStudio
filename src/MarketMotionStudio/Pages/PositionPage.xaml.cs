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
/// The position page: one purchase, held, and what the years did to it — the
/// question this page is asked with is a person and a date, "what if I'd held
/// a million of 中国平安 since 2015".
///
/// Two terms, both controls, for the same reason as the plan page: the point is
/// the arithmetic between them. The simulation is the plainest thing that can
/// honestly be called a holding; <see cref="PositionLoader"/> carries the
/// reasoning about what was deliberately left out — dividends above all, which
/// a long holding of a bank stock is a large fraction of, and which the frame's
/// subtitle says is not counted.
///
/// No renderer of its own pipeline: <see cref="PositionRenderer"/> draws the
/// frames, this page is a loader that turns a code and two terms into the series
/// it draws — the same split the calendar and the plan pages make.
/// </summary>
public sealed partial class PositionPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>
    /// The holding's spans, as a number of months. Zero means as far back as the
    /// source still has data, which the walk in <see cref="HistoryWalk"/> finds on
    /// its own — and it is the default, because a holding's story starts where the
    /// holder says it did, and "since 2015" is a span no fixed choice covers.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (120, "DcaRange10Y"),
        (0, "DcaRangeMax"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("Position.");

    /// <summary>The per-stock page's preferences container, used for the watchlist key only —
    /// one list shared by every page that names one instrument.</summary>
    private readonly StudioPreferences _watchlist = new("Stock.");

    private PositionSeries? _fetched;

    /// <summary>The market in force: it names the presets, it is what the search is
    /// filtered to, and its currency names the amounts.</summary>
    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    private string _instrumentCode;

    private string _instrumentName = string.Empty;

    private StockSuggestion? _pendingChoice;

    private string _lastQuery = string.Empty;

    private readonly ObservableCollection<StockFavourite> _favourites = [];

    private readonly DispatcherTimer _searchDebounce = new() { Interval = TimeSpan.FromMilliseconds(260) };

    public PositionPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // "As far back as there is": a holding is a years-long story by default, and
        // the walk stops where the listing's own history does.
        RangeCombo.SelectedIndex = 3;

        foreach (var entry in _market.PositionInstruments)
        {
            Presets.Items.Add(new MatrixPreset(entry.Code, InstrumentNames.Display(entry.Code, entry.Name)));
        }

        Favourites.ItemsSource = _favourites;

        _searchDebounce.Tick += async (_, _) =>
        {
            _searchDebounce.Stop();
            await SearchSuggestionsAsync();
        };

        // The default the frame will actually use, before anything is fetched: the
        // market's own first one-tap holding.
        _instrumentCode = _market.PositionInstruments[0].Code;
        _instrumentName = InstrumentNames.Display(_market.PositionInstruments[0].Code, _market.PositionInstruments[0].Name);

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

        // After every control exists and every handler is attached, so a restored value
        // reaches the preview through the same path a typed one does.
        RestorePreferences();
        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("PositionPageTitle.Text");

    // ---- the holding's terms ---------------------------------------------------------

    /// <summary>
    /// The capital that goes in once, or zero while the box holds nothing parsable.
    /// Zero is the fetch's refusal, not a silent substitute: a holding with no
    /// capital is not a holding. The interface's culture reads it first, the
    /// invariant one second — an amount is a number before it is a localised one,
    /// and "1000000" must mean a million everywhere.
    /// </summary>
    private double ChosenCapital
    {
        get
        {
            var text = CapitalBox.Text.Trim();

            return double.TryParse(text, NumberStyles.Float, CultureInfo.CurrentUICulture, out var capital) ? capital
                : double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out capital) ? capital
                : 0;
        }
    }

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 0;
        var today = DateOnly.FromDateTime(DateTime.Now);

        // "As far back as there is": ask for thirteen years and let the walk stop where
        // the source does. Clamped to the source's own ceiling so the first request
        // already carries the full 640-bar window.
        return months == 0 ? (today.AddYears(-13), today) : (today.AddMonths(-months), today);
    }

    // ---- preview ---------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_fetched is { } fetched)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, fetched.Points.Count, fetched.Peak);

            Preview.Renderer = new PositionRenderer(fetched, plan)
            {
                Title = title,
                ShowTitle = showTitle,
                CurrencyKey = _market.CurrencyKey,
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = Strings.Format("PositionDefaultTitle", _instrumentName);

        var ready = _fetched is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>
    /// The title the frame will draw: the typed one, or the default naming the current
    /// instrument. The renderer is rebuilt on every change, so the placeholder follows
    /// the instrument even before a fetch has confirmed its proper name.
    /// </summary>
    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0
            ? VideoSettings.TitleText
            : Strings.Format("PositionDefaultTitle", _instrumentName);

    // ---- search ----------------------------------------------------------------------

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

            var ordered = found
                .Where(r => _market.Accepts(r.Code))
                .Take(12)
                .Select(r => new StockSuggestion(r.Code, r.Name, r.Code[..2].ToUpperInvariant()))
                .ToArray();

            InstrumentSearch.ItemsSource = ordered;
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

        if (!_market.Accepts(code))
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("WrongMarket", _market.Name));
            return;
        }

        ChooseInstrument(code, code);
    }

    private void OnPresetClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is string code)
        {
            var name = Presets.Items.OfType<MatrixPreset>().FirstOrDefault(p => p.Code == code)?.Name ?? code;
            ChooseInstrument(code, name);
        }
    }

    // ---- favourites ------------------------------------------------------------------

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

    // ---- fetching --------------------------------------------------------------------

    private void ChooseInstrument(string code, string name)
    {
        _instrumentCode = code;
        _instrumentName = InstrumentNames.Display(code, name);

        Fetch();
    }

    private async void Fetch()
    {
        var capital = ChosenCapital;

        if (capital <= 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("PositionCapitalInvalid"));
            return;
        }

        var (start, end) = ChosenRange();
        var display = _instrumentName.Length > 0 ? _instrumentName : _instrumentCode;

        // Three minutes, not the calendar's two: a holding reaching back a dozen years
        // is up to twenty requests answered one after another.
        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var fetched = await PositionLoader.LoadAsync(
                Services.Quotes, _instrumentCode, display, capital, start, end, progress, cancellation);

            _fetched = fetched;
            _instrumentName = InstrumentNames.Display(fetched.Code, fetched.Name);
            ApplyPreviewSettings();

            // Parked on the last frame: the closing statistics are what someone wants to
            // look at before deciding whether to export.
            ShowMoment(1);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "PositionFetched",
                fetched.Points.Count,
                PositionRenderer.Iso(fetched.Start),
                PositionRenderer.Iso(fetched.End),
                fetched.End.DayNumber - fetched.Start.DayNumber));
        }, TimeSpan.FromMinutes(3));
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

    private void OnHoldingChanged(object sender, object e)
    {
        // Raised by the selection assignment in the constructor, before the page exists
        // well enough to save anything.
        if (RangeCombo is null)
        {
            return;
        }

        SavePreferences();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e)
    {
        _playback?.Stop();

        Preview.Progress = Scrub.Value;
        RefreshScrubText();
        Preview.Redraw();
    }

    private void RefreshScrubText()
    {
        var at = VideoSettings.Duration.TotalSeconds * Preview.Progress;
        ScrubText.Text = Strings.Format("StudioScrubPosition", at.ToString("0.0"), (int)VideoSettings.Duration.TotalSeconds);
    }

    private void OnPlay(object sender, RoutedEventArgs e) => _playback.Toggle();

    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) =>
        PlayButton.Content = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export ----------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _fetched is not { } fetched || App.Window is not { } window)
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
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("StudioExporting", (int)(fraction * 100))));

            var file = await VideoExporter.EncodeAsync(
                renderer, format, margins, duration, folder,
                VideoExporter.VideoName(label, fetched.Start, fetched.End, format),
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
        if (Preview.Renderer is not { } renderer || _fetched is not { } fetched || App.Window is not { } window)
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
                FrameExporter.CoverName(ResolvedTitle(), fetched.Start, fetched.End, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences -----------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var capital = _prefs.GetDouble("Capital", 1_000_000);
        CapitalBox.Text = capital > 0
            ? capital.ToString("0.##", CultureInfo.InvariantCulture)
            : "1000000";

        var months = _prefs.GetInt("Months", 0);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 3;

        var code = _prefs.GetString("Code", _market.PositionInstruments[0].Code);

        // A code saved under another market is not carried over: it would fetch from a
        // venue whose presets and search results this page no longer shows.
        if (_market.Accepts(code))
        {
            _instrumentCode = code;

            var name = _prefs.GetString("Name", string.Empty);

            _instrumentName = name.Length > 0
                ? InstrumentNames.Display(code, name)
                : InstrumentNames.Display(_market.PositionInstruments[0].Code, _market.PositionInstruments[0].Name);
        }

        VideoSettings.Restore(_prefs);
        LoadFavourites();

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        _prefs.Save("Capital", ChosenCapital > 0 ? ChosenCapital : 1_000_000);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 0);
        _prefs.Save("Code", _instrumentCode);
        _prefs.Save("Name", _instrumentName);

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
