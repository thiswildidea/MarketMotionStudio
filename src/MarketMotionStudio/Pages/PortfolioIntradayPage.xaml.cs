using System.Collections.ObjectModel;
using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using MarketMotionStudio.Views;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Xaml.Media;
using Windows.UI;

namespace MarketMotionStudio.Pages;

/// <summary>One row of the book, already formatted: the list renders strings, not numbers.</summary>
public sealed class HoldingRow
{
    public HoldingRow(string name, string detail, string pnl, Color tone)
    {
        Name = name;
        Detail = detail;
        Pnl = pnl;
        Tone = new SolidColorBrush(tone);
    }

    /// <summary>The instrument, in the interface's language.</summary>
    public string Name { get; }

    /// <summary>Shares and cost, in the venue's currency.</summary>
    public string Detail { get; }

    /// <summary>Today's contribution, already signed — empty before the first fetch.</summary>
    public string Pnl { get; }

    /// <summary>Red for a gain, green for a loss, muted when there is nothing to say yet.</summary>
    public Brush Tone { get; }
}

/// <summary>
/// A portfolio's day, live: the running profit or loss from 09:30, refreshed while the market is
/// open, with the book edited by hand or by importing the broker's own filled orders.
///
/// <para>
/// **This page is the only one here whose subject is the reader.** Every other page draws a
/// market or an instrument, and the reader chooses one to look at; this one draws what they hold.
/// That is why it carries its own state — a book, a journal of confirmed trades — where the other
/// pages carry only parameters, and why the book is stored in a file rather than in preferences:
/// losing it means re-entering a position by hand from a phone screenshot.
/// </para>
///
/// <para>
/// **Live means two different things at two different moments.** During the session the page
/// re-reads the minute endpoints on a timer and the curve grows; after the close it shows the
/// finished day and the timer stops asking. The distinction is a clock, not a preference: polling
/// a settled day every thirty seconds costs the source a request per holding and answers with the
/// same numbers.
/// </para>
/// </summary>
public sealed partial class PortfolioIntradayPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("Portfolio.");

    /// <summary>The timer behind "refresh while the market is open".</summary>
    private readonly DispatcherTimer _auto = new() { Interval = TimeSpan.FromSeconds(30) };

    /// <summary>
    /// The three headline treatments, in the order the page offers them.
    ///
    /// The keys keep their <c>.Content</c> suffix because these lines are not set through
    /// <c>x:Uid</c>: the menu is filled in code, and <see cref="Strings.Get"/> reads the dotted
    /// name as a path — a key with the suffix left off resolves to nothing and the menu comes out
    /// reading <c>[PortfolioPnlTitlePlain]</c>.
    /// </summary>
    private static readonly (TitleSkin Skin, string Key)[] Skins =
    [
        (TitleSkin.Plain, "PortfolioPnlTitlePlain.Content"),
        (TitleSkin.Gilded, "PortfolioPnlTitleGilded.Content"),
        (TitleSkin.Engraved, "PortfolioPnlTitleEngraved.Content"),
    ];

    /// <summary>The headline colour the reader picked, as <c>#RRGGBB</c>; empty means
    /// "whichever this treatment comes with".</summary>
    private string _titleColour = string.Empty;

    /// <summary>True while the page is setting the picker's own colour, so the change it raises
    /// on itself is not read back as a choice.</summary>
    private bool _painting;

    private PortfolioSession? _session;

    /// <summary>The renderer the preview is drawing with, so the list can ask it where "now" is.</summary>
    private PortfolioPnlRenderer? _ticking;

    /// <summary>
    /// Which sample the list was last rebuilt for.
    ///
    /// Playback calls back sixty times a second and a session is 242 samples, so rebuilding on
    /// every callback would rebuild the whole item list four times a second for a number that has
    /// not changed since the last one. The list is rebuilt when the *sample* moves, and at that
    /// rate it is the list that moves with the picture.
    /// </summary>
    private int _listed = int.MinValue;

    /// <summary>Guards against a timer tick landing on top of a fetch already in flight.</summary>
    private bool _busy;

    /// <summary>
    /// Set when the book itself has just been edited by hand, cleared by the next
    /// <see cref="Adopt"/>.
    ///
    /// The list prefers the session's per-minute moments over the stored book, and the moments
    /// were built from the book as it was **before** the edit — showing them after an edit would
    /// put the old numbers straight back up (实测：改成 777，关掉对话框，列表还是 100). With the
    /// flag on, the list reads the stored book — the figures the reader just typed — and the
    /// replay semantics come back when the re-fetch has rebuilt the session around the new book.
    /// </summary>
    private bool _bookDirty;

    /// <summary>
    /// Waits for the typing in a fee box to stop.
    ///
    /// `ValueChanged` fires on every keystroke, and each load is a request per holding — so the
    /// rate is applied when the reader stops rather than while they are still writing "0.1".
    /// </summary>
    private readonly DispatcherTimer _feeTimer = new() { Interval = TimeSpan.FromSeconds(0.8) };

    public PortfolioIntradayPage()
    {
        InitializeComponent();

        Portfolio.EnsureLoaded();

        _feeTimer.Tick += OnFeeSettled;

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

        foreach (var (skin, key) in Skins)
        {
            // The tag carries the skin rather than its position in the menu, so a treatment
            // added in the middle cannot silently become another one.
            TitleSkinCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)skin });
        }

        RestorePreferences();
        ApplyPreviewSettings();
        RefreshBook();

        _auto.Tick += OnAutoTick;

        // The book is what this page is about, so it reads it on arrival rather than waiting for
        // a button. A page that opens empty and says "press fetch" would be showing the reader
        // their own holdings as a task.
        Loaded += async (_, _) =>
        {
            UpdateAutoTimer();

            if (_session is null)
            {
                await SilentRefreshAsync(report: false);
            }
        };

        Unloaded += (_, _) => _auto.Stop();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("PortfolioPnlPageTitle.Text");

    /// <summary>Pushes the panel's values into the preview and redraws once.</summary>
    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = VideoSettings.TitleText;
        var showTitle = VideoSettings.ShowTitle;

        if (_session is { } session && session.Samples.Count > 1)
        {
            // Scaled to the day's larger excursion on either side, so the axis holds the whole
            // session from the first frame: a chart that rescales as the curve grows makes the
            // shape of the morning unreadable while it is being drawn.
            var plan = AnimationPlan.For(
                VideoSettings.Duration,
                session.Samples.Count,
                Math.Max(Math.Abs(session.Peak), Math.Abs(session.Trough)));

            var renderer = new PortfolioPnlRenderer(
                session, plan,
                crossSafeRight: CrossCheck.IsChecked is true,
                mascot: MascotCheck.IsChecked is true,
                dynamicAxis: DynamicAxisCheck.IsChecked is true,
                lunchBreak: LunchCheck.IsChecked is true,
                skin: SelectedSkin(),
                titleColour: ChosenTitleColour())
            {
                Title = title,
                ShowTitle = showTitle,
            };

            Preview.Renderer = renderer;
            _ticking = renderer;
        }
        else
        {
            _stage.Title = title.Length > 0 ? title : Strings.Get("PortfolioPnlTitle");
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
            _ticking = null;
        }

        VideoSettings.TitlePlaceholder = Strings.Get("PortfolioPnlTitle");

        var ready = _session is { Samples.Count: > 1 };

        CoverButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        PlayButton.IsEnabled = ready;

        // Through `ShowMoment` rather than a bare `Redraw`: a switch rebuilds the renderer, and
        // the list has to be read off the same minute the new one is drawing.
        ShowMoment(Preview.Progress);
    }

    /// <summary>
    /// Rebuilds the book's list from the stored holdings — as they stand at the minute the
    /// preview is drawing.
    /// </summary>
    /// <param name="index">
    /// Which of the session's minutes to ask. Negative (or a session with no minutes) reads the
    /// closing figures: the book's own shares, and the profit the day ended with. Those two never
    /// went together — a reader watching the 09:35 sale go past saw the position behind it stay
    /// at 5,900 shares — and the point of putting the fills on a clock is that the position moves.
    /// </param>
    private void RefreshBook(int index = -1)
    {
        var rows = new List<HoldingRow>();

        var moment = !_bookDirty && _session is { Moments.Count: > 0 } live
            ? live.Moments[index < 0
                ? live.Moments.Count - 1
                : Math.Min(index, live.Moments.Count - 1)]
            : null;

        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var holding in Portfolio.Holdings)
        {
            seen.Add(holding.Code);

            var priced = _session?.Holdings.FirstOrDefault(h =>
                string.Equals(h.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            // The minute being drawn when there is one; the stored book when there is not. The
            // cost comes from the same minute, because a sale moves it — 中望软件's 700 shares at
            // 33.448 cost 300 shares at 14.444 by the close, and showing the morning's figure
            // beside the evening's share count would be a row that never existed.
            var shares = moment is not null && moment.Shares.TryGetValue(holding.Code, out var held)
                ? held
                : holding.Shares;

            var cost = moment is not null && moment.Costs.TryGetValue(holding.Code, out var paid)
                ? paid
                : holding.Cost;

            var money = (holding.IsHongKong ? "HK$" : "¥")
                + cost.ToString("0.###", CultureInfo.InvariantCulture);

            // Sold out is a state the list has to be able to say out loud. The row stays where it
            // is — dropping it would relayout the list under the reader's eye mid-animation — and
            // "0 股" on its own reads like a typo rather than like the sale that happened at
            // 09:40. The cost goes with the shares: the diluted figure on a position of zero is a
            // zero, and a zero is not what the row used to cost.
            var detail = shares > 0
                ? Strings.Format(
                    "PortfolioPnlRowDetail",
                    shares.ToString("#,##0", CultureInfo.InvariantCulture),
                    money)
                : Strings.Get("PortfolioPnlRowCleared");

            double? made = moment is not null && moment.Contributions.TryGetValue(holding.Code, out var sofar)
                ? sofar
                : priced?.DayPnl;

            var (text, tone) = priced switch
            {
                { HasSession: false } => (Strings.Get("PortfolioPnlRowClosed"), Palette.Muted),
                _ when made is { } value =>
                    (PortfolioPnlRenderer.Money(value), value >= 0 ? Palette.Emphasis : Palette.Fall),
                _ => (string.Empty, Palette.Muted),
            };

            rows.Add(new HoldingRow(InstrumentNames.Display(holding.Code, holding.Name), detail, text, tone));
        }

        // **当天买出来的仓位也要有行。** The book only carries positions held at the open; a
        // fill that opens one mid-session (顺丰 at 13:55, 公牛 at 14:56) exists in the moments
        // alone — and a list that iterates the book never grows a row for it, so the curve
        // announces the 买入 and the list sits there unmoved (实测：播放过 13:55，列表 8 行原样).
        // From its first fill's minute onward the position gets a row of its own, appended at
        // the bottom so no row the reader is watching changes place; if the day later sells it
        // flat the row stays and reads 已清仓, the same rule the book's own rows follow.
        if (moment is not null && _session is { } session)
        {
            foreach (var trade in session.Trades)
            {
                if (!seen.Add(trade.Code))
                {
                    continue;
                }

                if (moment.Minute < trade.Minute)
                {
                    continue;
                }

                moment.Shares.TryGetValue(trade.Code, out var shares);
                moment.Costs.TryGetValue(trade.Code, out var cost);

                // **A fill that leaves no position is not a row.** A code that appears in the
                // day's journal only as a sale was never held in this book — nothing opened it —
                // and appending it would add a «已清仓» line for a position that never existed
                // (实测：整表导入三行之后，列表多出六行已清仓，正是账本里已经没有的那六只
                // 当天卖出). Rows are positions; a position needs shares behind it.
                if (shares <= 0)
                {
                    continue;
                }

                var money = (trade.Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase) ? "HK$" : "¥")
                    + cost.ToString("0.###", CultureInfo.InvariantCulture);

                var detail = shares > 0
                    ? Strings.Format(
                        "PortfolioPnlRowDetail",
                        shares.ToString("#,##0", CultureInfo.InvariantCulture),
                        money)
                    : Strings.Get("PortfolioPnlRowCleared");

                double? made = moment.Contributions.TryGetValue(trade.Code, out var sofar)
                    ? sofar
                    : null;

                var (text, tone) = made is { } value
                    ? (PortfolioPnlRenderer.Money(value), value >= 0 ? Palette.Emphasis : Palette.Fall)
                    : (string.Empty, Palette.Muted);

                rows.Add(new HoldingRow(InstrumentNames.Display(trade.Code, trade.Name), detail, text, tone));
            }
        }

        Holdings.ItemsSource = rows;
        EmptyNote.Visibility = rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
    }

    private async void OnFetch(object sender, RoutedEventArgs e) => await FetchAsync(report: true);

    private async Task FetchAsync(bool report)
    {
        if (_busy)
        {
            return;
        }

        _busy = true;

        try
        {
            await RunAsync(FetchButton, async cancellation =>
            {
                var progress = new Progress<string>(message =>
                    ShowStatus(InfoBarSeverity.Informational, message));

                var session = await IntradayPnl.LoadAsync(
                    Services.Http, Services.Stocks, [.. Portfolio.Holdings],
                    [.. Portfolio.Trades], progress, cancellation, Fees(), Portfolio.Settled);

                Adopt(session);

                // No success bar: `Adopt` has just written the same sentence into the line under
                // the switch, and it stays there. The bar is for what the page cannot say itself —
                // progress while it reads, and why a read failed.
                HideStatus();
            }, TimeSpan.FromMinutes(2));
        }
        finally
        {
            _busy = false;
        }
    }

    /// <summary>
    /// The timer's own fetch: no buttons disabled, no progress line, and a failure that says
    /// nothing when there was nothing to say.
    ///
    /// Separate from <see cref="FetchAsync"/> rather than a flag on it because the two want
    /// different failures. A fetch the reader asked for that fails must say so; a background
    /// re-read that fails (the phone lost its connection for a moment) must not put an error
    /// across a frame that is still correct.
    /// </summary>
    private async Task SilentRefreshAsync(bool report)
    {
        if (_busy || Portfolio.Holdings.Count == 0)
        {
            return;
        }

        _busy = true;

        try
        {
            using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(90));

            var session = await IntradayPnl.LoadAsync(
                Services.Http, Services.Stocks, [.. Portfolio.Holdings],
                [.. Portfolio.Trades], null, cancellation.Token, Fees(), Portfolio.Settled);

            Adopt(session);
        }
        catch (OperationCanceledException)
        {
            // The window closed, or the source took longer than a refresh interval. The next
            // tick will ask again.
        }
        catch (Exception ex)
        {
            if (report)
            {
                ShowFailure("PortfolioPnlFetchFailed", ex);
            }
        }
        finally
        {
            _busy = false;
        }
    }

    /// <summary>Puts a fetched session on the page, keeping the reader's position in the clip.</summary>
    private void Adopt(PortfolioSession session)
    {
        var wasAtEnd = Preview.Progress >= 0.999 || _session is null;

        _session = session;
        _bookDirty = false;

        // The list is rebuilt from the new session at whatever minute is on screen, so the cache
        // of "which minute is it showing" has to be thrown away first — otherwise a re-read that
        // landed on the same minute index leaves the old numbers up.
        _listed = int.MinValue;

        ApplyPreviewSettings();
        RefreshBook();

        // Parked on the live edge: this page's last frame is "now", which is the frame a reader
        // wants after a refresh. A re-read that jumped the preview back to 09:30 would undo the
        // one thing they were watching.
        //
        // A reader who had scrubbed into the middle stays there — including the list, which is
        // rebuilt from the minute they are looking at rather than jumping to the close under it.
        ShowMoment(wasAtEnd ? 1 : Preview.Progress);

        // The two lines belong together and are written together: this is the number the frame is
        // drawing, said in words, and the minute it was true. Set from here rather than from the
        // fetch button, because every other path to a new session — an import, a background tick
        // — comes through `Adopt` too, and a line that only the button updates lies for the rest
        // of the day.
        SummaryText.Text = Strings.Format(
            "PortfolioPnlFetched",
            session.Day,
            session.Samples.Count,
            PortfolioPnlRenderer.Money(session.Last));

        UpdatedText.Text = Strings.Format(
            "PortfolioPnlUpdated",
            session.FetchedAt.ToString("HH:mm:ss", CultureInfo.InvariantCulture));
    }

    private void OnAutoRefreshToggled(object sender, RoutedEventArgs e)
    {
        UpdateAutoTimer();
        SavePreferences();
    }

    /// <summary>
    /// A look switch moved: rebuild the renderer and stop there.
    ///
    /// Nothing is re-read, because none of the three changes a number — they change where the same
    /// numbers sit. Re-fetching would cost a request per holding to answer the same thing, and
    /// during a session it would also move the frame under the reader.
    /// </summary>
    private void OnLookChanged(object sender, RoutedEventArgs e)
    {
        ApplyPreviewSettings();
        SavePreferences();
    }

    private void OnTitleSkinChanged(object sender, SelectionChangedEventArgs e)
    {
        // The swatch and the picker are both answerable to the treatment: until a colour is chosen
        // each shows the one this treatment comes with, so switching treatments moves both. A
        // picker left on the previous treatment's colour is worse than a stale swatch — it is the
        // control the reader would then *touch*, and touching it writes the colour it was showing:
        // switch to 镀金, open the picker, nudge it, and the headline turns white.
        PaintPicker();
        PaintSwatch();

        ApplyPreviewSettings();
        SavePreferences();
    }

    private void OnTitleColourChanged(ColorPicker sender, ColorChangedEventArgs args)
    {
        if (_prefs.Restoring || _painting)
        {
            return;
        }

        var ink = args.NewColor;

        _titleColour = string.Format(
            CultureInfo.InvariantCulture, "#{0:X2}{1:X2}{2:X2}", ink.R, ink.G, ink.B);

        PaintSwatch();
        ApplyPreviewSettings();
        SavePreferences();
    }

    /// <summary>
    /// Hands the colour back to the treatment.
    ///
    /// A picker cannot show "nothing chosen": it always has a colour, and once the reader has
    /// touched it that colour is a choice whether they meant it as one or not. So the way back
    /// to "whichever this treatment comes with" has to be a control of its own.
    /// </summary>
    private void OnTitleColourDefault(object sender, RoutedEventArgs e)
    {
        _titleColour = string.Empty;

        PaintPicker();
        PaintSwatch();

        ApplyPreviewSettings();
        SavePreferences();
    }

    private TitleSkin SelectedSkin() =>
        TitleSkinCombo.SelectedItem is ComboBoxItem { Tag: int tag } ? (TitleSkin)tag : TitleSkin.Plain;

    /// <summary>The colour the reader picked, or null when they have not picked one.</summary>
    private Color? ChosenTitleColour()
    {
        var hex = _titleColour;

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

    private void PaintSwatch() =>
        TitleSwatch.Fill = new SolidColorBrush(ChosenTitleColour() ?? TitleSkins.Default(SelectedSkin()));

    private void PaintPicker()
    {
        _painting = true;

        TitleColour.Color = ChosenTitleColour() ?? TitleSkins.Default(SelectedSkin());

        _painting = false;
    }

    /// <summary>
    /// Runs the timer only while the market is open and the switch is on.
    ///
    /// The clock is the weekday and the session's own hours, coarse on purpose: this is a
    /// polling interval, not a trading calendar, and a holiday simply means the numbers do not
    /// change between two ticks.
    /// </summary>
    private void UpdateAutoTimer()
    {
        var now = DateTime.Now;
        var minute = (now.Hour * 60) + now.Minute;

        var open = AutoRefresh.IsOn &&
                   now.DayOfWeek is not (DayOfWeek.Saturday or DayOfWeek.Sunday) &&
                   minute >= (9 * 60) + 15 &&
                   minute <= (16 * 60) + 10;

        if (open)
        {
            _auto.Start();
        }
        else
        {
            _auto.Stop();
        }
    }

    private async void OnAutoTick(object? sender, object e) => await SilentRefreshAsync(report: false);

    /// <summary>
    /// Refreshes the session after the book or the journal changed underneath it.
    ///
    /// **The wait matters.** <see cref="SilentRefreshAsync"/> quietly returns when a fetch is
    /// already in flight — the right answer for a timer tick, and exactly the wrong one here: the
    /// in-flight fetch is holding a snapshot taken **before** the change, so skipping means the
    /// session never learns about the new trades or the new book, and a playback run afterwards
    /// walks a day whose fills never reach the list (实测：导入后立刻播放，列表不动). So this
    /// waits the in-flight one out and then fetches for real.
    /// </summary>
    private async Task RefreshAfterChangeAsync(bool report)
    {
        while (_busy)
        {
            await Task.Delay(120);
        }

        await SilentRefreshAsync(report);
    }

    /// <summary>
    /// The book as **the day's last minute** leaves it — what 管理持仓 is handed to show.
    ///
    /// <para>
    /// The list under the preview already reads this: the book is the morning's, and the fills walk
    /// it forward minute by minute. The dialog used to be handed the stored book instead, so the
    /// reader checked an import of 800 shares against a dialog still saying 100 and reported that
    /// nothing had been imported (实测：列表 公牛集团 900 股 / 37.054，对话框 100 股 / 37.73).
    /// </para>
    ///
    /// <para>
    /// **The close, not the frame on screen.** A preview scrubbed to 10:47 is a re-enactment, and
    /// the position it is drawing is what the book held at 10:47 — not what the reader holds. The
    /// dialog is the real book, so it takes the day's last minute whatever the scrub bar says. Rows
    /// the book does not carry (a position opened by today's fills) are appended, exactly as the
    /// list appends them.
    /// </para>
    /// </summary>
    private List<Holding> ClosingBook()
    {
        // A book just edited by hand has a stale session behind it — the moments on hand were built
        // before the edit, and handing them back would undo the numbers the reader just typed.
        if (_bookDirty || _session is not { Moments.Count: > 0 } session)
        {
            return [.. Portfolio.Holdings];
        }

        var moment = session.Moments[^1];
        var rows = new List<Holding>();
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var holding in Portfolio.Holdings)
        {
            seen.Add(holding.Code);

            var shares = moment.Shares.TryGetValue(holding.Code, out var held) ? held : holding.Shares;
            var cost = shares > 0 && moment.Costs.TryGetValue(holding.Code, out var paid) ? paid : holding.Cost;

            rows.Add(new Holding(holding.Code, holding.Name, shares, shares > 0 ? cost : 0));
        }

        foreach (var trade in session.Trades)
        {
            if (!seen.Add(trade.Code))
            {
                continue;
            }

            moment.Shares.TryGetValue(trade.Code, out var shares);
            moment.Costs.TryGetValue(trade.Code, out var cost);

            rows.Add(new Holding(trade.Code, trade.Name, shares, shares > 0 ? cost : 0));
        }

        return rows;
    }

    private async void OnManage(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var dialog = new PortfolioDialog(ClosingBook()) { XamlRoot = XamlRoot };

        await Dialogs.ShowAsync(dialog);

        // A hand-entered book is the position as the reader says it is, which outranks every fill
        // still waiting to roll into it — letting tomorrow's roll apply those same fills on top of
        // typed numbers would move the book twice. Marking them folded keeps the roll off them
        // while the journal keeps them for today's replay.
        if (dialog.Edited)
        {
            Portfolio.MarkManualEdit();
        }

        // Whatever was on the stage was drawn from the book that just changed. Dropped rather
        // than left standing, for the reason every other page drops its series when its
        // parameters move: a frame of nine holdings under a list of eight is a plausible
        // picture of the wrong thing.
        //
        // The list is rebuilt **from the stored book** here — the moment override is switched off
        // by `_bookDirty` — because the moments on hand were built from the book as it was before
        // the edit, and showing them would put the old numbers straight back up.
        _bookDirty = true;
        RefreshBook();

        if (Portfolio.Holdings.Count == 0)
        {
            _session = null;

            // An empty book draws nothing, so nothing can be said about it. Left standing, the
            // line would report a profit nobody holds.
            SummaryText.Text = string.Empty;
            UpdatedText.Text = string.Empty;

            ApplyPreviewSettings();
            return;
        }

        await RefreshAfterChangeAsync(report: true);
    }

    private async void OnImport(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var dialog = new TradeImportDialog(ImportDay()) { XamlRoot = XamlRoot };

        var choice = await Dialogs.ShowAsync(dialog);

        if (choice == ContentDialogResult.Primary && dialog.Trades.Count > 0)
        {
            var result = Portfolio.Apply(dialog.Trades);

            RefreshBook();

            ShowStatus(
                result.Unmatched > 0 ? InfoBarSeverity.Warning : InfoBarSeverity.Success,
                Strings.Format("PortfolioPnlImported", result.Applied, result.Duplicates, result.Unmatched));

            // Waits out any fetch already running — see the note on `RefreshAfterChangeAsync`:
            // the session on hand was built before this import, and a playback started on it
            // would walk a day whose fills never reach the list.
            await RefreshAfterChangeAsync(report: true);
        }
    }

    /// <summary>
    /// The day an import is stamped with: **the day the page is drawing**, not the day the clock
    /// says it is.
    ///
    /// The page draws the last session that traded, and before the market opens that is not
    /// today — it is yesterday. Filling the dialog with `DateTime.Today` then stamps the fills
    /// with a day nothing has traded on, so an import the dialog reports as "已导入 5 笔" lands
    /// where the reader cannot see it: the curve does not move, the header's count stays at zero,
    /// and nothing on the page says why. The picker is filled in with this day and the reader can
    /// still change it — a screenshot of Monday's fills really can be imported on Tuesday.
    /// </summary>
    private DateOnly ImportDay() =>
        _session is { Day.Length: > 0 } session && DateOnly.TryParse(session.Day, out var day)
            ? day
            : DateOnly.FromDateTime(DateTime.Today);

    /// <summary>The one day this page draws, for the file names.</summary>
    private (DateOnly From, DateOnly To)? Range() =>
        _session is { } session && DateOnly.TryParse(session.Day, out var day) ? (day, day) : null;

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || Range() is not { } range || App.Window is not { } window)
        {
            return;
        }

        if (!await SubscriptionOffer.PermitAsync(XamlRoot, window))
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;

        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : Strings.Get("PortfolioPnlTitle");

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
                VideoExporter.VideoName(label, range.From, range.To, format),
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
        if (Preview.Renderer is not { } renderer || Range() is not { } range || App.Window is not { } window)
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

            var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : Strings.Get("PortfolioPnlTitle");
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
    /// Moves the preview and the scrub bar together — and the book's list with them.
    ///
    /// The list is the picture in words, so it cannot be one step behind it: at 09:35 the curve
    /// is drawn on 3,000 shares of 超图软件 because the other 5,900 were sold, and a list still
    /// reading 5,900 would have the reader counting shares that are not there.
    /// </summary>
    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        // Per sample, not per frame: sixty callbacks a second over 242 samples would rebuild the
        // item list four times a second to show the same numbers.
        var index = _ticking?.ShownIndex(progress) ?? -1;

        if (index != _listed)
        {
            _listed = index;
            RefreshBook(index);
        }

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

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        AutoRefresh.IsOn = _prefs.GetBool("Auto", true);

        CrossCheck.IsChecked = _prefs.GetBool("CrossSafeRight", false);
        MascotCheck.IsChecked = _prefs.GetBool("Mascot", false);
        DynamicAxisCheck.IsChecked = _prefs.GetBool("DynamicAxis", false);

        // On by default: it is what the day looks like, and the other three switches are off
        // because they are additions to it rather than subtractions.
        LunchCheck.IsChecked = _prefs.GetBool("Lunch", true);

        _titleColour = _prefs.GetString("TitleColour", string.Empty);
        TitleSkinCombo.SelectedIndex = _prefs.GetInt("TitleSkin", 0);

        // The mainland's own figures unless the reader has set their own. The box is filled
        // rather than left blank: a blank one reads as "nothing is charged", which is the one
        // answer here that cannot be right for anybody with a broker.
        FeeCommission.Value = _prefs.GetDouble("FeeCommission", FeeSchedule.Mainland.Commission);
        FeeMinimum.Value = _prefs.GetDouble("FeeMinimum", FeeSchedule.Mainland.Minimum);
        FeeStamp.Value = _prefs.GetDouble("FeeStamp", FeeSchedule.Mainland.Stamp);
        FeeTransfer.Value = _prefs.GetDouble("FeeTransfer", FeeSchedule.Mainland.Transfer);

        PaintPicker();
        PaintSwatch();

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Auto", AutoRefresh.IsOn);

        _prefs.Save("CrossSafeRight", CrossCheck.IsChecked is true);
        _prefs.Save("Mascot", MascotCheck.IsChecked is true);
        _prefs.Save("DynamicAxis", DynamicAxisCheck.IsChecked is true);
        _prefs.Save("Lunch", LunchCheck.IsChecked is true);
        _prefs.Save("TitleSkin", TitleSkinCombo.SelectedIndex);
        _prefs.Save("TitleColour", _titleColour);

        _prefs.Save("FeeCommission", Read(FeeCommission, FeeSchedule.Mainland.Commission));
        _prefs.Save("FeeMinimum", Read(FeeMinimum, FeeSchedule.Mainland.Minimum));
        _prefs.Save("FeeStamp", Read(FeeStamp, FeeSchedule.Mainland.Stamp));
        _prefs.Save("FeeTransfer", Read(FeeTransfer, FeeSchedule.Mainland.Transfer));

        VideoSettings.Save(_prefs);
    }

    /// <summary>What it costs to trade, as the four boxes on the page currently read.</summary>
    private FeeSchedule Fees() => new(
        Read(FeeCommission, FeeSchedule.Mainland.Commission),
        Read(FeeMinimum, FeeSchedule.Mainland.Minimum),
        Read(FeeStamp, FeeSchedule.Mainland.Stamp),
        Read(FeeTransfer, FeeSchedule.Mainland.Transfer));

    /// <summary>
    /// A rate box's value, falling back when it has not got one.
    ///
    /// `NaN` is what a `NumberBox` holds while it is empty or half-typed — including the moment
    /// before the reader finishes clearing it to type something else. Reading that as zero would
    /// drop every fee for as long as the box was mid-edit, and the day's profit would jump up
    /// and come back down again for no reason the page explains.
    /// </summary>
    private static double Read(NumberBox box, double fallback) =>
        double.IsFinite(box.Value) ? box.Value : fallback;

    /// <summary>
    /// A rate changed. Remembered at once, applied when the typing stops.
    /// </summary>
    private void OnFeeChanged(object sender, NumberBoxValueChangedEventArgs e)
    {
        // Setting the boxes from the stored preferences raises this too, and making that a
        // change would re-read the day on every visit to the page.
        if (_prefs.Restoring)
        {
            return;
        }

        SavePreferences();

        _feeTimer.Stop();
        _feeTimer.Start();
    }

    private async void OnFeeSettled(object? sender, object e)
    {
        _feeTimer.Stop();

        await FetchAsync(report: false);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
