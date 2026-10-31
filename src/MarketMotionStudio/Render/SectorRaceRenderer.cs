using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Brushes;
using Microsoft.Graphics.Canvas.Geometry;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The sector race: horizontal bars overtaking one another, their order changing to the last
/// frame — the port of `sector_race_studio.html`'s render path.
///
/// What makes it smooth is that **the ranking itself is interpolated**. The naive approach —
/// snap each row to its new position every time a trading day passes — moves the whole field in
/// steps. Instead every day's ranking is precomputed, playback maps to a fractional day index,
/// and a row's vertical position is its two neighbouring days' ranks eased with a smoothstep
/// while its length interpolates linearly: two rows that trade places cross over smoothly
/// rather than swapping. The whole thing is a pure function of the frame's progress, which is
/// what lets a scrubbed preview and a frame-by-frame export agree.
///
/// The axis range is interpolated per day too, for the same reason — otherwise the whole field
/// rescales in one jump at each midnight — with fixed headroom on both ends because the value
/// labels sit outside the bar's end until the bar is long enough to hold them inside.
/// </summary>
public sealed class SectorRaceRenderer : IFrameRenderer, IFaceWarmup
{
    /// <summary>The left gutter's name column, in baseline pixels.</summary>
    private const double GutterLeft = 176;

    /// <summary>The right gutter's value-label column.</summary>
    private const double GutterRight = 130;

    /// <summary>
    /// The largest a row's text is allowed to be, in baseline pixels.
    ///
    /// This was 30, and 30 was a size the frame mostly never reached: the text used to be measured
    /// against the **row** (34% of the pitch), so a board of eight rows asked for 50 and got the
    /// cap, while a board of fifteen — the market-cap race, the densest in the app — asked for 27
    /// and got 27. Every board in the app looked like the cap except the one with the most rows to
    /// fit, which is the one whose text most needed the room. On the preview, drawn at about a
    /// third of the frame, 27 baseline pixels is a glyph eight *screen* pixels tall, and a CJK
    /// character has no strokes left at eight pixels: it reads as a grey smudge, while the sector
    /// race next to it in the menu reads as words.
    /// </summary>
    private const double LabelCap = 36;

    /// <summary>
    /// What share of its own bar a row's text may take up.
    ///
    /// Against the bar rather than against the row, because the bar is what the text has to sit on
    /// or beside: the row pitch sets how close two rows are, and the bar sets how tall each one is
    /// drawn. Tying the text to the pitch made a row that draws a *thin* bar report the same size
    /// as a row twice its height, which is why the dense board came out smallest of all.
    /// </summary>
    private const double LabelOfBar = 0.72;

    /// <summary>Baseline rows between the plot's bottom and the credit.</summary>
    private const double CreditGap = 74;

    private const double HeaderTopFraction = 0.278;

    private readonly SectorRaceSeries _series;

    private readonly RaceMetric _metric;

    /// <summary>The per-day ranking: rank[k][i] is racer k's position on day i, 0 leading.</summary>
    private readonly int[][] _rank;

    /// <summary>
    /// Per racer, the first day it is on the board for; past the end for one that never is.
    ///
    /// A field whose rows do not all start together — the index race carries 1950 next to 2020 —
    /// and the row has to be *out* of the ranking and not merely at the bottom of it: a racer
    /// ranked last still holds a place, and a board of twelve that shows five would draw its five
    /// rows with seven holes between them, because the holes are the places the absent ones are
    /// keeping warm.
    /// </summary>
    private readonly int[] _starts;

    /// <summary>The axis range per day, precomputed with its headroom.</summary>
    private readonly double[] _axisMin;

    private readonly double[] _axisMax;

    /// <param name="showTop">
    /// How many of the field's places the frame shows. The sector race passes nothing — every
    /// entrant is a row — while a market-cap board passes fifteen: it is handed a field of sixty
    /// listings and asks for the fifteen that were largest at each moment, which is what makes its
    /// membership change over time.
    /// </param>
    /// <param name="rankByMagnitude">
    /// Rank by size rather than by signed value, for a board whose rows can go either way.
    ///
    /// Off by default, because a race of cumulative returns or of turnovers is a race *up*: the
    /// signed value is the standing. A board of the largest single-day moves is the other kind,
    /// where −7.7% belongs next to +8.1% and a signed sort buries every drop under every rise.
    /// Only the ranking changes — the bar still grows to whichever side of the zero axis its own
    /// sign says.
    ///
    /// **A constructor argument and not a property**, which is the one thing this page's first
    /// build got wrong: the whole ranking table is precomputed here, before an object initialiser
    /// runs, so `new SectorRaceRenderer(...) { RankByMagnitude = true }` sorted by sign and said
    /// nothing. The frame drew the eight biggest rises and the seven smallest falls — a plausible
    /// picture of the wrong board — while the page's own status line, which ranked by magnitude
    /// itself, reported the correct days. Nothing in the UI could tell the two apart.
    /// </param>
    public SectorRaceRenderer(
        SectorRaceSeries series, RaceMetric metric, TimeSpan duration, int showTop = int.MaxValue,
        bool rankByMagnitude = false, TitleStyle? titleStyle = null, TitleStyle? subtitleStyle = null)
    {
        _series = series;
        _metric = metric;
        _rankByMagnitude = rankByMagnitude;
        Duration = duration;
        TotalMs = duration.TotalMilliseconds;
        _showTop = Math.Clamp(showTop, 1, Math.Max(1, series.Racers));

        _title = new TitleBlock(64, titleStyle, () => TitleSettings.MainStyle);
        _subtitle = new TitleBlock(40, subtitleStyle, () => TitleSettings.SubtitleStyle);

        var values = series.ReturnsOrAmounts(metric);

        _rank = new int[series.Racers][];

        _starts = new int[series.Racers];

        for (var k = 0; k < series.Racers; k++)
        {
            _rank[k] = new int[series.Days];
            _starts[k] = Math.Max(0, series.StartOf(k));
        }

        var field = new List<int>(series.Racers);
        var order = new int[series.Racers];

        for (var i = 0; i < series.Days; i++)
        {
            // Only the rows on the board are ranked. The rest are filed after them, in roster
            // order, so that a row joining later does not disturb the order of the ones already
            // racing — and so that their places are the ones below the frame's last row, where
            // nothing is drawn anyway.
            field.Clear();

            for (var k = 0; k < series.Racers; k++)
            {
                if (i >= _starts[k])
                {
                    field.Add(k);
                }
            }

            for (var n = 0; n < field.Count; n++)
            {
                order[n] = field[n];
            }

            // Magnitude, when the page asks for it: a board of the day's biggest moves either
            // way wants −7% beside +8%, and ranking the signed values would file every drop
            // below every rise however small the rise was.
            Array.Sort(order, 0, field.Count, Comparer<int>.Create(
                (a, b) => Rank(values[b][i]).CompareTo(Rank(values[a][i]))));

            var absent = field.Count;

            for (var k = 0; k < series.Racers; k++)
            {
                if (i >= _starts[k])
                {
                    continue;
                }

                order[absent++] = k;
            }

            for (var pos = 0; pos < order.Length; pos++)
            {
                _rank[order[pos]][i] = pos;
            }
        }

        // The axis range per day, with the headroom the labels need. Both ends: the labels sit
        // outside the bar's end, so without room the longest bar pushes its label into the names.
        //
        // Measured over the **rows the frame shows**, not over the whole field. A market-cap board
        // is handed sixty listings and draws fifteen; scaling to all sixty would leave the bars in
        // the top of the frame at a fifth of their width, because whoever is sixtieth is included
        // in a range only that row needs.
        _axisMin = new double[series.Days];
        _axisMax = new double[series.Days];

        for (var i = 0; i < series.Days; i++)
        {
            var low = double.MaxValue;
            var high = double.MinValue;

            for (var k = 0; k < series.Racers; k++)
            {
                // Neither a row below the frame's last place nor one that has not joined yet:
                // the first is off the bottom, the second is not on the board at all, and a zero
                // from the second would pull the axis towards a value nobody drew.
                if (_rank[k][i] >= _showTop || i < _starts[k])
                {
                    continue;
                }

                low = Math.Min(low, values[k][i]);
                high = Math.Max(high, values[k][i]);
            }

            if (low > high)
            {
                low = high = 0;
            }

            var lo = Math.Min(low, 0);
            var hi = Math.Max(high, 0);
            var span = (hi - lo) is var s && s == 0 ? 1 : s;

            _axisMin[i] = lo < 0 ? lo - (span * 0.22) : lo;
            _axisMax[i] = hi > 0 ? hi + (span * 0.16) : hi;
        }
    }

    /// <summary>Rows the frame shows, at most.</summary>
    private readonly int _showTop;

    /// <summary>How the field is staged. Bar is the original; the other four draw the
    /// same interpolated standings as a podium, a skyline, a pyramid or the skyline
    /// under a camera. A property and not a constructor argument — it changes only how
    /// the frame is drawn, never how the ranking table was built, so the page can set
    /// it in the object initialiser without re-reading a thing.</summary>
    public RaceStyle Style { get; set; } = RaceStyle.Bar;

    /// <summary>Where the badges' pictures come from, or null for the first-character
    /// badge everywhere. Set once by the page in the object initialiser; the badge asks
    /// it per row and falls back to the character while a picture is still landing.
    ///
    /// <para>Assigning starts every racer's download right away — no device needed for
    /// that, only the disk — so by the time a user switches to a badge-wearing style the
    /// pictures are mostly on disk, and an export's warm-up is a formality.</para>
    ///
    /// <para>The cache keys by <see cref="CompanyLogoCache.KeyOf"/>, so wiring it on a
    /// board of indexes, dates or coins changes nothing — their codes carry no key.</para></summary>
    public CompanyLogoCache? Faces
    {
        get => _faces;

        set
        {
            _faces = value;

            if (value is { } cache)
            {
                foreach (var key in FaceKeys)
                {
                    cache.Ensure(key);
                }
            }
        }
    }

    private CompanyLogoCache? _faces;

    /// <summary>Every racer's logo key — what the export's warm-up waits for.</summary>
    public string[] FaceKeys =>
        [.. _series.Entries
            .Select(e => CompanyLogoCache.KeyOf(e.Code))
            .Where(k => k.Length > 0)
            .Distinct()];

    /// <summary>The export's warm-up: every logo either on this device or known absent
    /// before the first frame, so a file never draws the fallback a ready picture
    /// stands behind.</summary>
    public async Task PrepareAsync(CanvasDevice device)
    {
        if (Faces is not { } cache || FaceKeys.Length == 0)
        {
            return;
        }

        await cache.WarmAsync(FaceKeys);

        foreach (var key in FaceKeys)
        {
            cache.Peek(device, key);
        }
    }

    public string Title { get; set; } = string.Empty;

    /// <summary>The user's own line under the title, drawn before the date-range line.
    /// Empty draws nothing. Its style falls back to the global subtitle default.</summary>
    public string Subtitle { get; set; } = string.Empty;

    public bool ShowTitle { get; set; } = true;

    /// <summary>The wrapped headline.</summary>
    private readonly TitleBlock _title;

    /// <summary>The user's own subtitle, smaller than the headline and on the same line grid.</summary>
    private readonly TitleBlock _subtitle;

    /// <summary>
    /// How many lines the title took on the frame being drawn — what the header's rows below it
    /// and the plot's top edge are moved by. Set once at the top of <see cref="Draw"/>.
    /// </summary>
    private int _titleLines;

    /// <summary>How many lines the user's subtitle took, so the rows below it shift down.</summary>
    private int _subtitleLines;

    /// <summary>Whether the user's subtitle row exists on this frame at all.</summary>
    private bool SubtitleShown => ShowTitle && Subtitle.Length > 0;

    /// <summary>
    /// Leave out a row whose value is zero at this moment, for a field whose rows have not all
    /// happened yet.
    ///
    /// The extreme-day board carries twenty-four candidate days and draws fifteen, and a day
    /// that is still in the future has no move to show. Ranked by magnitude it sits at the
    /// bottom of the field, which is not far enough: with only five days behind it the frame
    /// still had fifteen rows on it, ten of them reading 0.00%. A row that has not happened
    /// yet is not on the board at all, which is also how the board comes to fill up as the
    /// years pass.
    /// </summary>
    public bool HideEmptyRows { get; set; }

    /// <summary>
    /// Colour the bar by the sign of its value rather than by a hash of its code.
    ///
    /// One colour per row is what lets a viewer follow a company up a market-cap board. A board
    /// of single-day moves has nothing to follow — every row is one day, and what the viewer is
    /// reading is which way it went. So the bar is red for a rise and green for a fall, the
    /// pair this app uses everywhere, and the hashed palette is left to the pages whose rows
    /// are things that persist.
    /// </summary>
    public bool ColourBySign { get; set; }

    /// <summary>Read once, in the constructor: the ranking table depends on it.</summary>
    private readonly bool _rankByMagnitude;

    private double Rank(double value) => _rankByMagnitude ? Math.Abs(value) : value;

    /// <summary>
    /// The resource key for the amount metric's unit word. Overridable because the metric is
    /// 亿 *of something* and only the page knows what: the sector race's turnover is 亿元, a
    /// market-cap race's is 亿元, 亿港元 or 亿美元 depending on the market in force, and a label
    /// naming the wrong currency is a label nobody can check.
    /// </summary>
    public string UnitKey { get; set; } = "SectorUnitYi";

    /// <summary>The metric's own unit word, on every value label.</summary>
    private string Unit => _metric is RaceMetric.Return ? "%" : Strings.Get(UnitKey);

    private int Decimals => _metric is RaceMetric.Return ? 2 : 0;

    public void Draw(CanvasDrawingSession session, FrameContext context)
    {
        var t = context.Progress * TotalMs;

        // One clock for everything the frame reads — board, axis, header date. The
        // focusing tour squeezes the race into the window before the lens opens, and the
        // squeeze has to move the *whole* frame together: a board drawn on the squeezed
        // clock under a header date still ticking the real one would sit a caption over
        // final standings the race had not reached yet. See RaceClock.
        var clock = RaceClock(t);

        // Before the rows and the axis: both are placed against the bottom of the header block,
        // which is placed by how many lines the title took.
        _titleLines = _title.For(session, ResolvedTitle(), context, ShowTitle).Lines;

        _subtitleLines = SubtitleShown
            ? _subtitle.For(session, Subtitle, context, true).Lines
            : 0;

        context.Backdrop.Fill(session, context, Palette.Background);

        // One standings table, five stagings. The axis belongs to the bars alone — the
        // other styles carry their scale in the columns' own heights.
        var state = StateAt(clock);

        if (Style is RaceStyle.Bar)
        {
            DrawAxis(session, context, t, state);
            DrawRows(session, context, t, state);
        }
        else if (Style is RaceStyle.Podium)
        {
            DrawPodium(session, context, t, state);
        }
        else if (Style is RaceStyle.Skyline)
        {
            DrawSkyline(session, context, t, state);
        }
        else if (Style is RaceStyle.FocusTour)
        {
            DrawFocusTour(session, context, t, state);
        }
        else
        {
            DrawPyramid(session, context, t, state);
        }

        DrawFooter(session, context, t);
        DrawHeader(session, context, t, state);
        DrawProgress(session, context);
    }

    /// <summary>Animation shape: the source's own proportions.</summary>
    private double TotalMs { get; set; }

    public TimeSpan Duration { get; set; }

    private double IntroMs => Math.Min(2200, TotalMs * 0.05);

    private double FinaleStart => TotalMs - FinaleMs;

    private double FinaleMs => Math.Clamp(TotalMs * 0.12, 2500, 8000);

    private double RaceSpan => Math.Max(1, TotalMs - IntroMs - FinaleMs);

    /// <summary>
    /// Everything one moment needs: each racer's value, its interpolated slot, and the
    /// interpolated axis range. A pure function of the time — no state carried between frames.
    /// </summary>
    private (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) StateAt(double t)
    {
        var values = _series.ReturnsOrAmounts(_metric);

        var p = Easing.Ramp(t, IntroMs, RaceSpan);
        var pos = p * (_series.Days - 1);

        var i0 = (int)Math.Clamp(Math.Floor(pos), 0, _series.Days - 2);
        var i1 = Math.Min(_series.Days - 1, i0 + 1);
        var f = _series.Days > 1 ? Math.Clamp(pos - i0, 0, 1) : 0;
        var fe = SmoothStep(f);

        var vals = new double[_series.Racers];
        var slots = new double[_series.Racers];
        var finals = new int[_series.Racers];

        for (var k = 0; k < _series.Racers; k++)
        {
            vals[k] = Lerp(values[k][i0], values[k][i1], f);
            slots[k] = Lerp(_rank[k][i0], _rank[k][i1], fe);
            finals[k] = _rank[k][^1];
        }

        return (vals, slots, finals,
            Lerp(_axisMin[i0], _axisMin[i1], f),
            Lerp(_axisMax[i0], _axisMax[i1], f),
            (int)Math.Round(pos));
    }

    private void DrawAxis(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var a = Easing.Ramp(t, 400, 1200);
        if (a <= 0)
        {
            return;
        }

        var (top, bottom) = PlotArea(context);
        var (x0, _) = PlotColumns(context);
        var zx = ZeroX(context, state);

        session.DrawLine(
            new((float)zx, (float)(top - context.Px(10))),
            new((float)zx, (float)(bottom + context.Px(10))),
            Ink.Fade(Palette.Grid, a),
            (float)Math.Max(1, context.Px(2)));
    }

    private void DrawRows(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (top, bottom) = PlotArea(context);
        var (x0, x1) = PlotColumns(context);
        var plotW = x1 - x0;

        // The rows the frame shows, which is not the number of racers on a board: sixty listings
        // race for fifteen places, and the row height is set by the places.
        var rows = Math.Min(_showTop, Math.Max(1, _series.Racers));
        var rowH = (bottom - top) / rows;
        var barH = Math.Min(rowH * 0.64, context.Px(96));
        var nameSize = Math.Min(LabelCap, (barH / context.Scale) * LabelOfBar);

        var span = (state.AxisMax - state.AxisMin) is var s && s == 0 ? 1 : s;
        var zx = x0 + ((0 - state.AxisMin) / span) * plotW;

        // Trailing rows first, so a leader overlaps whoever it is passing.
        var order = Enumerable.Range(0, _series.Racers).OrderByDescending(k => state.Slots[k]).ToArray();

        // Not `using`: the name format is cached across frames. See NameFormat.
        var nameFormat = NameFormat(session, context, nameSize);

        using var strongFormat = Ink.Format(context.Px(nameSize), bold: true);
        using var valueFormat = Ink.Format(context.Px(nameSize), bold: true);

        var lastRow = rows - 1;

        var raw = _series.ReturnsOrAmounts(_metric);

        foreach (var k in order)
        {
            // Not on the board yet — see the note on `_starts`. This is the row the index race
            // keeps leaving out: an index whose history begins after the board's first month has
            // no change to show, and drawing it at 0.00% would rank it above every index that
            // was ever down.
            if (state.DayIndex < _starts[k])
            {
                continue;
            }

            // A row whose day has not come yet is not on the board — see HideEmptyRows.
            if (HideEmptyRows && raw[k][state.DayIndex] == 0)
            {
                continue;
            }

            // A field is wider than the board, so a row can be off the bottom of it. Rather than
            // have a listing pop in at the moment it takes fifteenth place, it fades over the
            // place below — which is also what makes "who is falling out" legible.
            var overflow = state.Slots[k] - lastRow;
            var fade = overflow <= 0 ? 1 : Math.Max(0, 1 - overflow);

            if (fade <= 0)
            {
                continue;
            }

            var intro = Easing.Ramp(t, 300 + (k * 60), 700);
            if (intro <= 0)
            {
                continue;
            }

            intro = Math.Min(intro, fade);

            // By the code, not by the index: the field is sixty listings and the palette has
            // sixteen colours, so index-based colours would repeat between rows that can stand
            // next to each other. Hashed, two listings that happen to share a colour are two
            // listings that are unlikely to be adjacent.
            // The same two tones Palette.Return ends on at full depth, so a bar's colour and
            // the value label beside it agree about which way the day went.
            var colour = ColourBySign
                ? (state.Values[k] >= 0 ? Rgb(0xEF, 0x44, 0x44) : Rgb(0x22, 0xC5, 0x5E))
                : Palette.Race16[Palette.RaceIndex(_series.Entries[k].Code)];
            var yc = top + ((state.Slots[k] + 0.5) * rowH);
            var vx = x0 + ((state.Values[k] - state.AxisMin) / span) * plotW;

            var left = Math.Min(zx, vx);
            var right = Math.Max(zx, vx);
            var w = Math.Max(context.Px(3), (right - left) * Easing.OutCubic(intro));
            var bx = vx >= zx ? zx : zx - w;

            // The champion gets a glow through the closing stretch, so the final frame has a focus.
            var champion = t > FinaleStart && state.Finals[k] == 0;

            void Bar(CanvasDrawingSession ds)
            {
                using var brush = new CanvasLinearGradientBrush(
                    ds,
                    [
                        new CanvasGradientStop { Position = 0f, Color = Ink.Fade(colour, 0.55) },
                        new CanvasGradientStop { Position = 1f, Color = Ink.Fade(colour, 0.98) },
                    ])
                {
                    StartPoint = new((float)bx, 0),
                    EndPoint = new((float)(bx + w), 0),
                };

                ds.FillRoundedRectangle(
                    (float)bx, (float)(yc - (barH / 2)), (float)w, (float)barH,
                    (float)context.Px(6), (float)context.Px(6), brush);
            }

            if (champion)
            {
                // shadowBlur 26 → sigma ~13.
                Ink.Glow(session, context.Px(13), 0.85, Bar);
            }

            Bar(session);

            // The name sits in the left gutter, right-aligned against the plot.
            //
            // White for **every** row, not only the champion's. It used to be pale blue
            // (#C9D8F5) with the leader in white, which made the one thing on this board that is
            // not data the dimmest thing on it: at the preview's third of the frame the pale blue
            // reads as grey, and a name is read before a bar is. The champion is marked by its
            // glow instead — a mark that costs nobody else any contrast.
            var nameColour = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);

            Ink.RightMiddle(session, _series.Entries[k].Name,
                x0 - context.Px(NameRightGap), yc, nameFormat, nameColour, intro);

            // The value follows the bar's end outside it; a bar long enough holds its own label
            // inside. Outside, the axis's proportional headroom cannot guarantee room for a label
            // of fixed pixel width — the longest bar is the one that would push its label into
            // the names, and by construction it is also the one long enough to hold it inside.
            var text = ValueText(state.Values[k]);
            var textWidth = Ink.Measure(session, text, valueFormat);
            var inside = w >= textWidth + context.Px(26);

            // Inside, the label is written *on* the bar, so the ink has to be chosen from that bar's
            // own colour and not from the frame. White is right on the dark half of the palette and
            // unreadable on the light half — white on the amber this board hands out is 2.1:1,
            // under the 3:1 floor even for large text — and the market-cap race is drawn entirely in
            // the light half's company. A board coloured by sign keeps white for both signs: there
            // the colours *are* the meaning, and a rise and a fall of the same size written in two
            // different inks would read as two different kinds of label.
            Color insideInk = ColourBySign
                ? Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF)
                : Ink.OnTopOf(colour);

            Color valueColour = inside
                ? insideInk
                : _metric is RaceMetric.Return
                    ? (state.Values[k] >= 0 ? Palette.Emphasis : Rgb(0x4A, 0xDE, 0x80))
                    : colour;

            if (vx >= zx)
            {
                if (inside)
                {
                    Ink.RightMiddle(session, text, bx + w - context.Px(13), yc, valueFormat, valueColour, intro);
                }
                else
                {
                    Ink.LeftAt(session, text, bx + w + context.Px(12), yc, valueFormat, valueColour, intro);
                }
            }
            else
            {
                if (inside)
                {
                    Ink.LeftAt(session, text, bx + context.Px(13), yc, valueFormat, valueColour, intro);
                }
                else if (bx - context.Px(12) - textWidth < x0)
                {
                    // Outside, on the near side, there is no room: the bar points left and its left
                    // end is close to the plot's own left edge, so a label right-aligned at that end
                    // runs back over the name column and the row reads as one string —
                    // "恒生科技−40.55%". The axis's 22% headroom puts the *most* negative value at
                    // about 16% of the plot's width, which is 36 baseline pixels, and a label is
                    // wider than that; so this is not a rare frame but the one row that is furthest
                    // down in every frame of a board that has a fall on it. Put the label beyond
                    // the zero axis instead, where a short fall has the frame to itself.
                    Ink.LeftAt(session, text, zx + context.Px(12), yc, valueFormat, valueColour, intro);
                }
                else
                {
                    Ink.RightMiddle(session, text, bx - context.Px(12), yc, valueFormat, valueColour, intro);
                }
            }
        }
    }

    private CanvasTextFormat? _names;

    private double _namesFor = -1;

    /// <summary>
    /// The left gutter's format, sized down until the longest name fits the room it is given.
    ///
    /// The room used to be the gutter alone — 150 baseline pixels, less a 24-pixel inset. That is
    /// the right room for a board whose rows say 能源 and 材料, and it is not the right room for
    /// one whose rows say 中国石油化工股份: eight characters is about 261 baseline pixels at the
    /// size a fifteen-row board draws at, so the fit shrank the **whole column** to 19 — every row,
    /// including 腾讯 and 美团 — to keep one name inside a band that was drawn as a column but is
    /// not one.
    ///
    /// It is not a column, because the names are right-aligned against the plot: they end at the
    /// same x and reach left as far as each one needs. What they may use is therefore everything
    /// between the frame's edge and the plot — the gutter **and** the frame's left margin, which on
    /// a bar race holds nothing at all, there being no Y axis on this renderer. See NameRoom.
    ///
    /// **One size for the whole column**, not one per row: rows scaled individually read as a
    /// ransom note rather than as a list. And computed **once**, not per frame — a 2,700-frame
    /// export would otherwise measure every name 2,700 times for an answer that cannot change.
    /// </summary>
    private CanvasTextFormat NameFormat(CanvasDrawingSession session, FrameContext context, double wanted)
    {
        if (_names is not null && Math.Abs(_namesFor - wanted) < 0.01)
        {
            return _names;
        }

        var (x0, _) = PlotColumns(context);

        // Everything between the frame's edge and the plot, not only the gutter — see NameRoom.
        var room = x0 - context.Px(NameRightGap) - context.Px(NameEdgeInset);
        var size = wanted;

        foreach (var entry in _series.Entries)
        {
            if (entry.Name.Length > 0)
            {
                size = Math.Min(size, Ink.FitSize(session, entry.Name, context.Px(wanted), room, bold: true));
            }
        }

        _names?.Dispose();

        _namesFor = wanted;
        _names = Ink.Format(context.Px(Math.Max(wanted * 0.5, size)), bold: true);

        return _names;
    }

    /// <summary>How far a name's right edge stops short of the plot.</summary>
    private const double NameRightGap = 14;

    /// <summary>
    /// How far the longest name may reach towards the frame's left edge.
    ///
    /// Small, and deliberately not the frame's left margin: the margin is how far the *nearest
    /// content* sits from the edge, and on this renderer the title block is what sets it — a name
    /// that runs past it is not overlapping anything, it is using empty frame. What this constant
    /// guards against is a name touching the edge itself, which is the one place it cannot go.
    /// </summary>
    private const double NameEdgeInset = 16;

    private string ValueText(double value) =>
        (_metric is RaceMetric.Return && value > 0 ? "+" : string.Empty)
        + value.ToString("N" + Decimals.ToString(CultureInfo.InvariantCulture), CultureInfo.InvariantCulture)
        + Unit;

    private void DrawFooter(CanvasDrawingSession session, FrameContext context, double t)
    {
        var a = Easing.Ramp(t, FinaleStart - 1200, 900);
        if (a <= 0)
        {
            return;
        }

        using var format = Ink.Format(context.Px(20));

        Ink.Centred(session, Strings.Get("StudioCredit"), context.Width / 2, context.CreditLine,
            format, Palette.Credit, a * 0.8);
    }

    private void DrawHeader(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var a = Easing.Ramp(t, 0, 1000);
        var cx = context.Width / 2;

        var title = ResolvedTitle();

        _title.Draw(session, context, title, _title.For(session, title, context, ShowTitle), Palette.Title, a);

        // The user's own subtitle, on the line after the title's last. The date-range line
        // below it stays where it was, shifted down by the subtitle's own rows.
        if (SubtitleShown)
        {
            _subtitle.Draw(
                session, context, Subtitle, _subtitle.For(session, Subtitle, context, true),
                Palette.Moving, a, lineOffset: _titleLines);
        }

        using (var plain = Ink.Format(context.Px(26)))
        using (var strong = Ink.Format(context.Px(26), bold: true))
        {
            var unit = _series.Racers == 0 ? string.Empty : UnitWord;

            Ink.Runs(
                session,
                [
                    (Iso(_series.Dates[0]) + " " + Strings.Get("StockRangeJoiner") + " " + Iso(_series.Dates[^1]) + " · ",
                        Palette.StockMuted, plain),
                    (_series.Days.ToString(CultureInfo.InvariantCulture), Palette.Emphasis, strong),
                    (" " + Span + " · " + _series.Racers.ToString(CultureInfo.InvariantCulture) + " " + unit,
                        Palette.StockMuted, plain),
                ],
                cx, context.HeaderRow(0.188, _titleLines) + (SubtitleShown ? context.Px(_subtitleLines * FrameContext.TitleLineHeight) : 0), a);
        }

        using (var format = Ink.Format(context.Px(40), bold: true))
        {
            Ink.Centred(session, Iso(_series.Dates[state.DayIndex]), cx,
                context.HeaderRow(0.222, _titleLines) + (SubtitleShown ? context.Px(_subtitleLines * FrameContext.TitleLineHeight) : 0), format, Palette.Moving, a);
        }
    }

    private static void DrawProgress(CanvasDrawingSession session, FrameContext context)
    {
        var height = (float)Math.Max(4, context.Height * 0.003);
        var y = (float)(context.Height - height);

        session.FillRectangle(0, y, (float)context.Width, height, Palette.ProgressTrack);

        Ink.FillHorizontal(
            session,
            new Rect(0, y, context.Width * Math.Clamp(context.Progress, 0, 1), height),
            Palette.RaceProgressFill,
            context.Width);
    }

    /// <summary>The plot's rows: the top anchored to the header block, the bottom to the credit.</summary>
    private (double Top, double Bottom) PlotArea(FrameContext context)
    {
        var top = context.HeaderRow(HeaderTopFraction, _titleLines)
            + (SubtitleShown ? context.Px(_subtitleLines * FrameContext.TitleLineHeight) : 0);
        var bottom = context.CreditLine - context.Px(CreditGap);

        return (top, bottom);
    }

    /// <summary>The plot's left and right, gutters inside the user's margins.</summary>
    private (double Left, double Right) PlotColumns(FrameContext context) =>
        (context.Margins.Left + context.Px(GutterLeft),
         context.Width - context.Margins.Right - context.Px(GutterRight));

    private double ZeroX(FrameContext context,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (x0, x1) = PlotColumns(context);
        var span = (state.AxisMax - state.AxisMin) is var s && s == 0 ? 1 : s;

        return x0 + ((0 - state.AxisMin) / span) * (x1 - x0);
    }

    /// <summary>“{list} 涨幅竞速” / “{list} 成交额竞速” — the source's own auto-title shape.</summary>
    private string AutoTitle() => Strings.Format(
        _metric is RaceMetric.Return ? "SectorAutoTitleReturn" : "SectorAutoTitleAmount",
        ListLabel);

    /// <summary>
    /// The headline this frame draws: what the user typed, or the auto-title. One place, because
    /// the text measured at the top of <see cref="Draw"/> and the text drawn in the header have to
    /// be the same string.
    /// </summary>
    private string ResolvedTitle() => Title.Length > 0 ? Title : AutoTitle();

    /// <summary>The roster's name, supplied by the page — it knows which list was chosen.</summary>
    public string ListLabel { get; set; } = string.Empty;

    /// <summary>
    /// The word after the count of them — 个交易日 for a daily series, 个月 for a monthly one.
    ///
    /// Supplied by the page, and this one used to be read straight off the string table here.
    /// That was a claim about the data, made by a renderer that cannot see the data: when the
    /// market-cap board inherited this renderer and became monthly, every frame it drew announced
    /// "12 个交易日" for twelve months. The page knows what interval it asked the source for; the
    /// renderer only knows how many rows came back.
    ///
    /// Empty means a daily race, which is what this renderer was written for.
    /// </summary>
    public string SpanWord { get; set; } = string.Empty;

    private string Span => SpanWord.Length > 0 ? SpanWord : Strings.Get("StockTradingDaysUnit");

    /// <summary>
    /// The count word for the header line — 个板块, 只个股, 只候选. Supplied by the page because it
    /// belongs to the roster, not to the metric: a key keyed on the metric here is how
    /// `[SectorUnitPercent]` ended up rendered literally in a shipped frame.
    /// </summary>
    public string UnitWord { get; set; } = string.Empty;

    // ---- the column stagings: podium, skyline, pyramid, the focusing tour ---------------
    //
    // Ported from NbaMotionStudio's StatRaceRenderer, where the career race shipped all
    // five stagings first. The differences are the two named in RaceStyle's own remark:
    // no headshots (a badge draws where a face would), and columns sized by the same
    // magnitude the board ranks by, so the extreme-day board's falls stand as tall as
    // its rises. Everything else — the interpolated slots, the pacing, the tour's clock
    // — reads straight off the same StateAt the bar rows do.

    /// <summary>Gold, silver, bronze — the podium's three inks, flat so the columns read
    /// at preview scale.</summary>
    private static readonly Color[] Medals =
    [
        Color.FromArgb(0xFF, 0xF5, 0xC5, 0x42),
        Color.FromArgb(0xFF, 0xC9, 0xD2, 0xE0),
        Color.FromArgb(0xFF, 0xC9, 0x8A, 0x5B),
    ];

    private static readonly Color MedalInk = Color.FromArgb(0xFF, 0x0D, 0x14, 0x24);
    private static readonly Color BadgePlate = Color.FromArgb(0xFF, 0x16, 0x21, 0x3C);
    private static readonly Color RowInk = Color.FromArgb(0xFF, 0xC7, 0xD2, 0xE8);

    private static Color Medal(int rank) => Medals[Math.Clamp(rank, 0, Medals.Length - 1)];

    /// <summary>
    /// How many slim rows the pyramid's histogram holds — the places past the throne.
    ///
    /// Capped, and deliberately small: a board whose field is wide enough to need twenty
    /// rows is a board for the bar staging. Six cards and eight rows is what a throne
    /// reads as, and the cap is what buys each of those rows the height to be read at all.
    /// </summary>
    private const int PyramidRows = 8;

    /// <summary>
    /// The design height of one pyramid histogram row: the share of the frame the rows
    /// reserve before the throne takes the rest. A target rather than a rule — the
    /// throne has a floor, and when the rows' share would push the throne under it the
    /// rows take what is left instead.
    /// </summary>
    private const double PyramidRowPitch = 80;

    /// <summary>The design row every measure inside <see cref="DrawSlimRow"/> scales against.</summary>
    private const double SlimRowPitch = 60;

    /// <summary>The slim row's bar thickness, in design rows.</summary>
    private const double SlimBar = 22;

    /// <summary>The slim row's badge diameter, in design rows.</summary>
    private const double SlimBadge = 46;

    /// <summary>The slim row's rank and name type size, in design rows.</summary>
    private const double SlimFont = 26;

    /// <summary>What share of the row past the badge the name column may take.</summary>
    private const double SlimNameShare = 0.46;

    /// <summary>The column heights read the value the way the ranking reads it: by the
    /// signed value on a board of things that race up, by magnitude on the extreme-day
    /// board, whose falls are as much the point as its rises. A signed read on that
    /// board would seat a −7.7% day on the podium as a stub.</summary>
    private double HeightOf(double value) => _rankByMagnitude ? Math.Abs(value) : value;

    /// <summary>
    /// The badge every staging shows where the career board drew a headshot: the dark
    /// plate and its medal ring, and inside — a **company logo** when the racer is a
    /// listed company and its picture has landed, otherwise the racer's own first
    /// character. One character, because a name is spelled out in full beside the
    /// column anyway — the badge is what the eye holds onto while the columns cross.
    /// </summary>
    private void DrawBadge(
        CanvasDrawingSession session, FrameContext context,
        string code, string name, double cx, double cy, double radius, Color ring, double alpha)
    {
        if (alpha <= 0)
        {
            return;
        }

        session.FillCircle((float)cx, (float)cy, (float)radius, Ink.Fade(BadgePlate, alpha));

        var faced = TryFace(session, code, cx, cy, radius * 2, alpha);

        session.DrawCircle((float)cx, (float)cy, (float)radius, Ink.Fade(ring, alpha), (float)(radius * 0.07));

        if (faced)
        {
            return;
        }

        var initial = name.Length > 0 ? name[..1] : "?";

        using var format = Ink.Format(radius * 1.1, bold: true);

        Ink.Centred(session, initial, cx, cy, format, RowInk, alpha);
    }

    /// <summary>The racer's company logo, drawn through the device-keyed cache —
    /// true when a picture went down, false when the badge should keep its character.
    /// A miss starts the download; the invalidation repaints when it lands.</summary>
    private bool TryFace(
        CanvasDrawingSession session, string code, double cx, double cy, double size, double alpha)
    {
        if (Faces is not { } cache || alpha <= 0)
        {
            return false;
        }

        var key = CompanyLogoCache.KeyOf(code);

        if (key.Length == 0)
        {
            return false;
        }

        var face = cache.Peek(session.Device, key);

        if (face is null)
        {
            cache.Ensure(key);

            return false;
        }

        // Scale, place in frame pixels, then the session's letterbox — the order the
        // career board's rows settled on after the matrix-order lesson.
        var saved = session.Transform;
        session.Transform = System.Numerics.Matrix3x2.CreateScale((float)(size / CompanyLogoCache.Size))
            * System.Numerics.Matrix3x2.CreateTranslation((float)(cx - (size / 2)), (float)(cy - (size / 2)))
            * saved;

        using (session.CreateLayer((float)Math.Clamp(alpha, 0, 1)))
        {
            session.DrawImage(face, 0, 0);
        }

        session.Transform = saved;

        return true;
    }

    /// <summary>The three-point crown over a reigning leader. Size is the crown's width;
    /// baseY is where its bottom edge sits.</summary>
    private static void Crown(
        CanvasDrawingSession session, double cx, double baseY, double size, double alpha)
    {
        using var path = new CanvasPathBuilder(session);
        var s = size;

        path.BeginFigure((float)(cx - s), (float)baseY);
        path.AddLine((float)(cx - s), (float)(baseY - (s * 0.52)));
        path.AddLine((float)(cx - (s * 0.5)), (float)(baseY - (s * 0.18)));
        path.AddLine((float)cx, (float)(baseY - s));
        path.AddLine((float)(cx + (s * 0.5)), (float)(baseY - (s * 0.18)));
        path.AddLine((float)(cx + s), (float)(baseY - (s * 0.52)));
        path.AddLine((float)(cx + s), (float)baseY);
        path.EndFigure(CanvasFigureLoop.Closed);

        using var geometry = CanvasGeometry.CreatePath(path);

        session.FillGeometry(geometry, Ink.Fade(Medals[0], alpha));
    }

    /// <summary>
    /// The podium staging: three medal columns — the leader centred and crowned, silver
    /// and bronze flanking — their heights the values themselves, and every rank past
    /// the podium a slim row underneath. A column's place comes straight off the
    /// interpolated slot, so an overtake is the two columns crossing, exactly as the
    /// bar race's rows cross; the medal inks follow the nearest rank through the swap.
    /// </summary>
    private void DrawPodium(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (top, bottom) = PlotArea(context);
        var cx = context.Width / 2;
        var day = state.DayIndex;

        var colArea = (bottom - top) * 0.60;
        var yBase = top + colArea;
        var colMaxH = Math.Max(context.Px(80), colArea - context.Px(150));
        var colW = context.Px(120);
        var gap = context.Px(28);
        var leftCx = cx - colW - gap;
        var rightCx = cx + colW + gap;

        var rowTop = yBase + context.Px(30);
        var rowH = context.Px(54);
        var capacity = (int)Math.Max(0, Math.Floor((bottom - rowTop) / rowH));

        // One name size for the whole column, fitted to the room the bar leaves it — the
        // same rule the pyramid's rows use, so the two stagings' histograms read alike.
        using var rowNameFormat = SlimNameFormat(session, context, rowH, out var rowNameWidth);

        using var rankFormat = Ink.Format(context.Px(34), bold: true);
        using var valueFormat = Ink.Format(context.Px(24), bold: true);

        var axisDenom = Math.Max(state.AxisMax, 1e-9);

        for (var k = 0; k < _series.Racers; k++)
        {
            if (day < _starts[k])
            {
                continue;
            }

            var intro = Easing.Ramp(t, 300 + (k * 60), 700);
            if (intro <= 0)
            {
                continue;
            }

            var s = state.Slots[k];
            var value = state.Values[k];
            var name = _series.Entries[k].Name;

            if (s < 3)
            {
                // Slot 0 is the centre, 1 the left column, 2 the right; the interpolated
                // slot slides the column between them, so a swap is a crossing.
                var px = s <= 1 ? Lerp(cx, leftCx, s) : Lerp(leftCx, rightCx, s - 1);
                var rank = Math.Clamp((int)Math.Round(s), 0, 2);
                var medal = Medal(rank);
                var a = intro * Math.Clamp((3.05 - s) / 0.45, 0, 1);

                if (a <= 0)
                {
                    continue;
                }

                var h = Math.Max(context.Px(44), (HeightOf(value) / axisDenom) * colMaxH);

                session.FillRoundedRectangle(
                    (float)(px - (colW / 2)), (float)(yBase - h), (float)colW, (float)h,
                    (float)context.Px(10), (float)context.Px(10), Ink.Fade(medal, a));

                Ink.Centred(session, (rank + 1).ToString(CultureInfo.InvariantCulture),
                    px, yBase - context.Px(20), rankFormat, MedalInk, a);

                if (h > context.Px(96))
                {
                    Ink.Centred(session, ValueText(value), px, yBase - h + context.Px(36),
                        valueFormat, MedalInk, a);
                }

                var badgeR = context.Px(40);
                var badgeCy = yBase - h - badgeR - context.Px(10);

                DrawBadge(session, context, _series.Entries[k].Code, name, px, badgeCy, badgeR + context.Px(3), medal, a);

                var nameSize = Math.Min(context.Px(26),
                    Ink.FitSize(session, name, context.Px(26), colW + context.Px(90), bold: true));

                using var nameFormat = Ink.Format(nameSize, bold: true);

                var nameY = badgeCy - badgeR - (rank == 0 ? context.Px(46) : context.Px(22));

                Ink.Centred(session, name, px, nameY, nameFormat, RowInk, a);

                if (rank == 0)
                {
                    Crown(session, px, badgeCy - badgeR - context.Px(10), context.Px(22), a);
                }
            }
            else
            {
                // Same overflow rule as the pyramid's rows: `capacity` places past the
                // podium, a fade across the last slot of travel, gone one slot later.
                var a = intro
                    * Math.Clamp((s - 2.55) / 0.5, 0, 1)
                    * Math.Clamp(capacity + 3 - s, 0, 1);

                if (a <= 0)
                {
                    continue;
                }

                var yc = rowTop + ((s - 3 + 0.5) * rowH);

                DrawSlimRow(session, context, k, s, value, yc, a, state.AxisMax, rowH, rowNameFormat, rowNameWidth);
            }
        }
    }

    /// <summary>
    /// The skyline staging: one column per board place, side by side, heights the values
    /// themselves. A column's x comes off the interpolated slot, so the whole line
    /// reorders the way a bar race's rows do — columns crossing as ranks change. The
    /// podium three get badges and names above their columns; the rest a rank number, so
    /// the eye can still follow a chaser down the line.
    /// </summary>
    private void DrawSkyline(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (top, bottom) = PlotArea(context);
        var day = state.DayIndex;
        var places = Math.Min(_showTop, Math.Max(1, _series.Racers));

        var x0 = context.Margins.Left + context.Px(6);
        var x1 = context.Width - context.Margins.Right - context.Px(6);
        var pitch = (x1 - x0) / places;
        var colW = Math.Min(pitch * 0.62, context.Px(46));
        var yBase = bottom - context.Px(8);
        var maxH = Math.Max(context.Px(60), yBase - top - context.Px(150));

        using var rankFormat = Ink.Format(context.Px(22), bold: true);

        var axisDenom = Math.Max(state.AxisMax, 1e-9);

        for (var k = 0; k < _series.Racers; k++)
        {
            if (day < _starts[k])
            {
                continue;
            }

            var intro = Easing.Ramp(t, 240 + (k * 50), 700);
            if (intro <= 0)
            {
                continue;
            }

            var s = state.Slots[k];
            var a = intro * Math.Clamp((places - 0.55 - s) / 0.45 + 1, 0, 1);

            if (a <= 0)
            {
                continue;
            }

            var value = state.Values[k];
            var name = _series.Entries[k].Name;
            var xc = x0 + (pitch * (s + 0.5));
            var h = Math.Max(context.Px(8), (HeightOf(value) / axisDenom) * maxH);
            var colour = ColourBySign
                ? (value >= 0 ? Rgb(0xEF, 0x44, 0x44) : Rgb(0x22, 0xC5, 0x5E))
                : Palette.Race16[Palette.RaceIndex(_series.Entries[k].Code)];

            session.FillRoundedRectangle(
                (float)(xc - (colW / 2)), (float)(yBase - h), (float)colW, (float)h,
                (float)context.Px(4), (float)context.Px(4), Ink.Fade(colour, a));

            var rank = (int)Math.Round(s);

            if (rank < 3)
            {
                var badgeR = Math.Min(context.Px(28), pitch * 0.72);
                var badgeCy = yBase - h - badgeR - context.Px(8);

                DrawBadge(session, context, _series.Entries[k].Code, name, xc, badgeCy, badgeR + context.Px(2.5), Medal(rank), a);

                // Name, then value, stacked above the badge — both fitted to the column's
                // own pitch, because a label measured against a wider room is what ran
                // across the neighbour's label. The value sits between name and crown.
                var label = ValueText(value);
                var nameSize = Math.Min(context.Px(20), Ink.FitSize(session, name, context.Px(20), pitch * 0.98, bold: true));
                var valueSize = Math.Min(nameSize * 0.92, Ink.FitSize(session, label, nameSize * 0.92, pitch * 0.98, bold: true));

                using var nameFormat = Ink.Format(nameSize, bold: true);
                using var valueFormat = Ink.Format(valueSize, bold: true);

                var nameY = badgeCy - badgeR - context.Px(10);
                var valueY = nameY - (nameSize * 1.3);

                Ink.Centred(session, name, xc, nameY, nameFormat, RowInk, a);
                Ink.Centred(session, label, xc, valueY, valueFormat, Medal(rank), a);

                if (rank == 0)
                {
                    Crown(session, xc, valueY - (valueSize * 1.4), context.Px(18), a);
                }
            }
            else
            {
                Ink.Centred(session, (rank + 1).ToString(CultureInfo.InvariantCulture),
                    xc, yBase - h - context.Px(16), rankFormat, Palette.Credit, a);
            }
        }
    }

    /// <summary>
    /// The focusing tour: a skyline staged in three camera movements.
    ///
    /// The first movement is the race itself — the whole line growing and reordering, with
    /// only the top columns the camera will visit marked. Then the lens opens: it walks the
    /// board from a lower place to first, one column at a time, centring it, widening it,
    /// opening a big badge above it with the name and the total, everything else dimmed to
    /// an outline of itself. Then it pulls back and hands the chart back whole.
    ///
    /// Every column still reads off the same interpolated slot and the same values the
    /// plain skyline uses. Through the tour the standings are frozen at the final frame,
    /// because the tour is about who finished where, not another pass of the race.
    /// </summary>
    private void DrawFocusTour(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var total = TotalMs;
        var tourStart = total * TourStartFraction;
        var tourEnd = total * TourEndFraction;

        // The board under the lens is the one `state` already carries: Draw built it on
        // RaceClock, which squeezes the race to finish exactly as the lens starts opening,
        // so the tour begins on a settled board. Only the lens's own choreography below
        // reads the real clock — the walk is staged time, not race time.

        // Only as many visits as there are columns to visit — a narrow board gets a
        // short tour, not one with stops pointing at nothing.
        var places = Math.Min(_showTop, Math.Max(1, _series.Racers));
        var focuses = Math.Min(TourFocuses, places);

        var zoom = TourZoom(t, tourStart, tourEnd, total, focuses);
        var (firstPlace, secondPlace, move) = TourBeat(t, tourStart, tourEnd, focuses);

        var (top, bottom) = PlotArea(context);

        var x0 = context.Margins.Left + context.Px(6);
        var x1 = context.Width - context.Margins.Right - context.Px(6);
        var pitch = (x1 - x0) / places;
        var colW = Math.Min(pitch * 0.62, context.Px(46));
        var yBase = bottom - context.Px(8);

        // The close-up needs air above its column for badge, name and total. Take it out of
        // the columns' headroom as the lens opens, and shorten them by the same breath, so
        // even the tallest one cannot reach up into the header.
        var headroom = context.Px(150) + (context.Px(120) * zoom);
        var maxH = Math.Max(context.Px(60), yBase - top - headroom);
        var heightScale = 1 - (0.26 * zoom);

        // Board place → racer. The tour runs on a frozen board, so one racer per place;
        // while the race is still running the rounding can briefly share and the last wins.
        var byPlace = new (int Racer, double Slot, double Value, double X)[places];
        var taken = new bool[places];

        for (var k = 0; k < _series.Racers; k++)
        {
            if (state.DayIndex < _starts[k])
            {
                continue;
            }

            var s = state.Slots[k];
            var place = (int)Math.Round(s);

            if (place < 0 || place >= places)
            {
                continue;
            }

            byPlace[place] = (k, s, state.Values[k], x0 + (pitch * (s + 0.5)));
            taken[place] = true;
        }

        // Where the lens is pointing — between the outgoing column and the incoming one, so
        // the pan is continuous. The whole line slides by that much: a camera pan, not a zoom.
        var firstX = taken[firstPlace] ? byPlace[firstPlace].X : context.Width / 2;
        var secondX = taken[secondPlace] ? byPlace[secondPlace].X : context.Width / 2;
        var shift = (context.Width / 2 - Lerp(firstX, secondX, move)) * zoom;

        DrawTourGround(session, context, state, byPlace, taken, places, pitch, colW, yBase,
            maxH, heightScale, shift, t, firstPlace, secondPlace, move, zoom, focuses);

        DrawTourDots(session, context, bottom, t, move, firstPlace, focuses);
    }

    /// <summary>The line, then the close-ups drawn over it: a focused column can never be
    /// covered by the neighbour it has just left behind.</summary>
    private void DrawTourGround(
        CanvasDrawingSession session, FrameContext context,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state,
        (int Racer, double Slot, double Value, double X)[] byPlace, bool[] taken, int places,
        double pitch, double colW, double yBase, double maxH, double heightScale,
        double shift, double t, int firstPlace, int secondPlace, double move, double zoom,
        int focuses)
    {
        using var rankFormat = Ink.Format(context.Px(22), bold: true);

        var wide = Lerp(colW, Math.Min(pitch * 2.6, context.Px(300)), zoom);
        var axisDenom = Math.Max(state.AxisMax, 1e-9);

        for (var place = 0; place < places; place++)
        {
            if (!taken[place])
            {
                continue;
            }

            var (k, s, value, _) = byPlace[place];
            var intro = Easing.Ramp(t, 240 + (k * 50), 700);
            var a = intro * Math.Clamp((places - 0.55 - s) / 0.45 + 1, 0, 1) * (1 - (0.82 * zoom));

            if (a <= 0)
            {
                continue;
            }

            var x = byPlace[place].X + shift;
            var h = Math.Max(context.Px(8), (HeightOf(value) / axisDenom) * maxH) * heightScale;
            var w = place == firstPlace || place == secondPlace ? wide : colW;
            var name = _series.Entries[k].Name;

            session.FillRoundedRectangle(
                (float)(x - (w / 2)), (float)(yBase - h), (float)w, (float)h,
                (float)context.Px(4), (float)context.Px(4),
                Ink.Fade(Palette.Race16[Palette.RaceIndex(_series.Entries[k].Code)], a));

            if (place < focuses)
            {
                // The mark is this staging's whole point: a column the camera will come to
                // carries its ring even with no lens on it.
                var badgeR = Math.Min(context.Px(28), pitch * 0.72);
                var badgeCy = yBase - h - badgeR - context.Px(8);

                DrawBadge(session, context, _series.Entries[k].Code, name, x, badgeCy, badgeR + context.Px(2.5), TourRing(place), a);
            }
            else
            {
                Ink.Centred(session, (place + 1).ToString(CultureInfo.InvariantCulture),
                    x, yBase - h - context.Px(16), rankFormat, Palette.Credit, a);
            }
        }

        if (zoom <= 0)
        {
            return;
        }

        // Outgoing first, fading; incoming second, arriving in its place.
        if (taken[firstPlace] && firstPlace != secondPlace)
        {
            DrawTourCloseUp(session, context, state, byPlace[firstPlace], firstPlace, PlotArea(context).Top,
                yBase, maxH, heightScale, shift, wide, zoom * (1 - move));
        }

        if (taken[secondPlace])
        {
            DrawTourCloseUp(session, context, state, byPlace[secondPlace], secondPlace, PlotArea(context).Top,
                yBase, maxH, heightScale, shift, wide, zoom * move);
        }
    }

    /// <summary>One column under the lens: widened, crowned if it leads, its badge opened
    /// above it, then the name, then the total.</summary>
    private void DrawTourCloseUp(
        CanvasDrawingSession session, FrameContext context,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state,
        (int Racer, double Slot, double Value, double X) entry, int place,
        double top, double yBase, double maxH, double heightScale, double shift,
        double wide, double alpha)
    {
        if (alpha <= 0)
        {
            return;
        }

        var k = entry.Racer;
        var x = entry.X + shift;
        var value = entry.Value;
        var ring = TourRing(place);
        var h = Math.Max(context.Px(8), (HeightOf(value) / Math.Max(state.AxisMax, 1e-9)) * maxH) * heightScale;
        var barTop = yBase - h;

        session.FillRoundedRectangle(
            (float)(x - (wide / 2)), (float)barTop, (float)wide, (float)h,
            (float)context.Px(6), (float)context.Px(6), Ink.Fade(ring, alpha));

        // Everything above the column is fitted to the air the column left it — badge, name
        // and total scale together, so a short leader and a tall one both read.
        var room = barTop - top;
        var badge0 = context.Px(130);
        var name0 = context.Px(28);
        var value0 = context.Px(36);
        var f = Math.Clamp(room / (badge0 + (name0 * 1.3) + (value0 * 1.35) + context.Px(46)), 0.5, 1);

        var badgeSize = badge0 * f;
        var nameSize = name0 * f;
        var valueSize = value0 * f;

        var valueY = barTop - context.Px(14 * f);
        var nameY = valueY - (valueSize * 1.25);
        var badgeCy = nameY - (nameSize * 1.15) - (badgeSize / 2);

        var name = _series.Entries[k].Name;

        DrawBadge(session, context, _series.Entries[k].Code, name, x, badgeCy, badgeSize / 2 + context.Px(3 * f), ring, alpha);

        var width = context.Width - context.Margins.Left - context.Margins.Right - context.Px(48);

        using var nameFormat = Ink.Format(Ink.FitSize(session, name, nameSize, width, bold: true), bold: true);
        using var valueFormat = Ink.Format(valueSize, bold: true);

        Ink.Centred(session, name, x, nameY, nameFormat, RowInk, alpha);
        Ink.Centred(session, ValueText(value), x, valueY, valueFormat, ring, alpha);

        if (place == 0)
        {
            Crown(session, x, badgeCy - (badgeSize / 2) - context.Px(8 * f), context.Px(24 * f), alpha);
        }
    }

    /// <summary>One dot per place the camera visits, so the viewer can tell how far through
    /// the walk up the board the tour has got.</summary>
    private void DrawTourDots(
        CanvasDrawingSession session, FrameContext context, double bottom, double t,
        double move, int firstPlace, int focuses)
    {
        var visible = Math.Min(Easing.Ramp(t, IntroMs, 900), 1 - Easing.Ramp(t, TotalMs - 300, 300));

        if (visible <= 0)
        {
            return;
        }

        var cy = bottom + context.Px(18);
        var span = context.Width - context.Margins.Left - context.Margins.Right - context.Px(80);
        var pitch = Math.Min(context.Px(22), span / Math.Max(1, focuses - 1));
        var left = (context.Width / 2) - (pitch * (focuses - 1) / 2);

        for (var i = 0; i < focuses; i++)
        {
            var place = focuses - i - 1;
            var current = place == firstPlace;
            var colour = current ? TourRing(place) : Color.FromArgb(0xFF, 0x2A, 0x3A, 0x5C);
            var a = visible * (current ? Lerp(1, 0.55, move) : 0.75);

            session.FillCircle((float)(left + (i * pitch)), (float)cy, (float)context.Px(4),
                Ink.Fade(colour, a));
        }
    }

    /// <summary>
    /// The clock the race board reads. On the focusing tour the race is squeezed into the
    /// window before the lens opens — <see cref="TourStartFraction"/> of the film carries
    /// the whole run, so the tour begins on a settled board — and after that moment the
    /// board holds on the final standings while the lens walks it.
    /// </summary>
    private double RaceClock(double t)
    {
        if (Style is not RaceStyle.FocusTour)
        {
            return t;
        }

        var tourStart = TotalMs * TourStartFraction;

        return tourStart > 0
            ? Math.Min(t, tourStart) / tourStart * (IntroMs + RaceSpan)
            : t;
    }

    /// <summary>How far the lens has opened: nothing until the race settles, open through
    /// the tour, and out again at the end.</summary>
    private double TourZoom(double t, double tourStart, double tourEnd, double total, int focuses)
    {
        if (t < tourStart)
        {
            return 0;
        }

        var beat = (tourEnd - tourStart) / Math.Max(1, focuses);
        var opening = SmoothStep(Math.Clamp((t - tourStart) / (beat * 0.45), 0, 1));

        if (t < tourEnd)
        {
            return opening;
        }

        return opening * (1 - SmoothStep(Math.Clamp((t - tourEnd) / (total * 0.06), 0, 1)));
    }

    /// <summary>Which column the camera is on: the lowest place first, first place last,
    /// holding on each before sliding across to the next.</summary>
    private (int First, int Second, double Move) TourBeat(
        double t, double tourStart, double tourEnd, int focuses)
    {
        var span = Math.Max(1, tourEnd - tourStart);
        var p = Math.Clamp((t - tourStart) / span * focuses, 0, focuses);
        var index = (int)Math.Clamp(Math.Floor(p), 0, focuses - 1);
        var move = SmoothStep(Math.Clamp((p - index - BeatHold) / (1 - BeatHold), 0, 1));

        var first = focuses - index;
        var second = Math.Max(1, first - 1);

        return (first - 1, second - 1, move);
    }

    /// <summary>The inks of the board's walked places — gold, silver and bronze for the
    /// podium, then a different hue each step down, so a column's standing is readable
    /// without reading a number.</summary>
    private static Color TourRing(int place) => TourRings[Math.Clamp(place, 0, TourRings.Length - 1)];

    // The walk runs from 45% of the film to 92% of it, so each column gets roughly a
    // second on screen at the app's default durations, with the race squeezed in front
    // of it and a breath of pull-back behind.
    private const double TourStartFraction = 0.45;
    private const double TourEndFraction = 0.92;
    private const double BeatHold = 0.6;
    private const int TourFocuses = 10;

    private static readonly Color[] TourRings =
    [
        Color.FromArgb(0xFF, 0xF5, 0xC5, 0x42),
        Color.FromArgb(0xFF, 0xC9, 0xD2, 0xE0),
        Color.FromArgb(0xFF, 0xC9, 0x8A, 0x5B),
        Color.FromArgb(0xFF, 0x5F, 0xA8, 0xFF),
        Color.FromArgb(0xFF, 0x34, 0xD3, 0x99),
        Color.FromArgb(0xFF, 0xA5, 0xB4, 0xFC),
        Color.FromArgb(0xFF, 0xC4, 0xB5, 0xFD),
        Color.FromArgb(0xFF, 0xF9, 0xA8, 0xD4),
        Color.FromArgb(0xFF, 0xFD, 0xBA, 0x74),
        Color.FromArgb(0xFF, 0x7D, 0xD3, 0xC0),
    ];

    /// <summary>
    /// The pyramid staging: tiered cards — the leader alone on the golden throne row, two
    /// beneath, three beneath them, and the rest as slim rows. A card's centre is its
    /// integer rank's anchor, lerped through the interpolated slot, so an overtake slides
    /// one card across a tier and the throne change is a card drifting up to the top row.
    /// </summary>
    private void DrawPyramid(
        CanvasDrawingSession session, FrameContext context, double t,
        (double[] Values, double[] Slots, int[] Finals, double AxisMin, double AxisMax, int DayIndex) state)
    {
        var (top, bottom) = PlotArea(context);
        var cx = context.Width / 2;
        var day = state.DayIndex;

        // Base geometry at scale 1 — the three card heights and the two tier gaps.
        const double BaseHeight = 96 + 30 + 70 + 24 + 56;
        var free = context.Width - context.Margins.Left - context.Margins.Right - context.Px(24);

        // The histogram comes first and the throne takes what is left. Its rows are the
        // reason this staging exists, so they reserve their own share of the frame up
        // front; the throne is then as large as the remainder allows and no larger. The
        // second tier — two cards and the air between — is the widest, so the frame's
        // width caps the throne's width before its height does: the throne grows into the
        // vertical room the rows leave (a short board's throne is a tall one) and can
        // never grow wider than the frame.
        var rows = Math.Clamp(_series.Racers - 6, 1, PyramidRows);
        var rowPitch = context.Px(PyramidRowPitch);
        var throneRoom = (bottom - top) - context.Px(24) - (rowPitch * rows);

        var sw = Math.Max(0.6, free / context.Px((236 * 2) + 28));
        var sh = Math.Max(sw, throneRoom / context.Px(BaseHeight));

        // Widths by the width scale, heights by the height scale: the two differ whenever
        // the board is short, and a card drawn with one scale for both came out either too
        // narrow to hold its name or too short to hold its badge.
        var w0 = context.Px(330) * sw;
        var h0 = context.Px(96) * sh;
        var w1 = context.Px(236) * sw;
        var h1 = context.Px(70) * sh;
        var w2 = context.Px(152) * sw;
        var h2 = context.Px(56) * sh;

        var y0 = top + (h0 / 2);
        var y1 = y0 + (h0 / 2) + context.Px(30 * sh) + (h1 / 2);
        var y2 = y1 + (h1 / 2) + context.Px(24 * sh) + (h2 / 2);

        // Anchor per integer rank: where a card centred on that rank sits.
        var anchors = new (double X, double Y, double W, double H)[6]
        {
            (cx, y0, w0, h0),
            (cx - (w1 / 2) - context.Px(14 * sw), y1, w1, h1),
            (cx + (w1 / 2) + context.Px(14 * sw), y1, w1, h1),
            (cx - w2 - context.Px(10 * sw), y2, w2, h2),
            (cx, y2, w2, h2),
            (cx + w2 + context.Px(10 * sw), y2, w2, h2),
        };

        // The rows start below the pyramid — never over it — and run down to the credit.
        // Their pitch is the target set above; it only comes down when the throne's own
        // floor took the room first, and the floor is what keeps a row from collapsing
        // onto its neighbour when a title wraps or margins close in.
        var rowTop = top + context.Px(BaseHeight * sh) + context.Px(24);
        var rowH = Math.Max(context.Px(34), Math.Min(rowPitch, (bottom - rowTop) / rows));
        var capacity = rows;

        using var nameFormat = SlimNameFormat(session, context, rowH, out var nameWidth);

        for (var k = 0; k < _series.Racers; k++)
        {
            if (day < _starts[k])
            {
                continue;
            }

            var intro = Easing.Ramp(t, 300 + (k * 60), 700);
            if (intro <= 0)
            {
                continue;
            }

            var s = state.Slots[k];
            var name = _series.Entries[k].Name;

            if (s < 6)
            {
                var i0 = Math.Clamp((int)Math.Floor(s), 0, 5);
                var i1 = Math.Min(i0 + 1, 5);
                var f = SmoothStep(Math.Clamp(s - i0, 0, 1));
                var (ax, ay, aw, ah) = anchors[i0];
                var (bx, by, bw, bh) = anchors[i1];
                var x = Lerp(ax, bx, f);
                var y = Lerp(ay, by, f);
                var w = Lerp(aw, bw, f);
                var h = Lerp(ah, bh, f);

                var rank = (int)Math.Round(s);
                var king = rank == 0;
                var a = intro * Math.Clamp((6.05 - s) / 0.45, 0, 1);

                if (a <= 0)
                {
                    continue;
                }

                session.FillRoundedRectangle(
                    (float)(x - (w / 2)), (float)(y - (h / 2)), (float)w, (float)h,
                    (float)(context.Px(12) * sw), (float)(context.Px(12) * sh),
                    Ink.Fade(Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF), 0.055 * a));

                session.DrawRoundedRectangle(
                    (float)(x - (w / 2)), (float)(y - (h / 2)), (float)w, (float)h,
                    (float)(context.Px(12) * sw), (float)(context.Px(12) * sh),
                    Ink.Fade(king ? Medals[0] : Color.FromArgb(0xFF, 0x2A, 0x35, 0x50), king ? a : 0.8 * a),
                    (float)(context.Px(king ? 2.4 : 1) * sw));

                var badgeR = (h * 0.72) / 2;
                var badgeCx = x - (w / 2) + context.Px(14 * sw) + badgeR;

                DrawBadge(session, context, _series.Entries[k].Code, name, badgeCx, y, badgeR + context.Px(2.5 * sw),
                    king ? Medals[0] : Palette.Race16[Palette.RaceIndex(_series.Entries[k].Code)], a);

                var room = w - (badgeR * 2) - context.Px(58 * sw);
                var nameSize = Math.Min(context.Px(king ? 28 : 24) * sh, Ink.FitSize(session, name, context.Px(king ? 28 : 24) * sh, room, bold: true));

                using var cardNameFormat = Ink.Format(nameSize, bold: true);
                using var valueFormat = Ink.Format(nameSize * 0.92, bold: true);

                var textX = badgeCx + badgeR + context.Px(16 * sw);

                Ink.LeftAt(session, name, textX, y - context.Px(12 * sh), cardNameFormat,
                    king ? Medals[0] : RowInk, a);
                Ink.LeftAt(session, ValueText(state.Values[k]), textX, y + context.Px(14 * sh), valueFormat, RowInk, a);

                if (king)
                {
                    Crown(session, x + (w / 2) - context.Px(26 * sw), y - (h / 2) + context.Px(6 * sh), context.Px(20 * sh), a);
                }
            }
            else
            {
                // The rows hold exactly `capacity` places past the pyramid; a member past
                // them fades across its last slot of travel, and one slot further out it
                // is gone.
                var a = intro
                    * Math.Clamp((s - 5.55) / 0.5, 0, 1)
                    * Math.Clamp(capacity + 6 - s, 0, 1);

                if (a <= 0)
                {
                    continue;
                }

                var yc = rowTop + ((s - 6 + 0.5) * rowH);

                DrawSlimRow(session, context, k, s, state.Values[k], yc, a, state.AxisMax, rowH, nameFormat, nameWidth);
            }
        }
    }

    /// <summary>
    /// One name size for a whole slim-row column: the widest name in the cast, fitted into
    /// the share of the row the labels leave the bar.
    ///
    /// One size for the column rather than one per row — rows sized individually read as a
    /// ransom note rather than as a list — and measured from the widest name rather than
    /// the longest, because a nine-character Latin name can be narrower than a
    /// four-character one in a logographic script. The width comes back with the format
    /// because the bar's own room is whatever the name does not take.
    /// </summary>
    private CanvasTextFormat SlimNameFormat(
        CanvasDrawingSession session, FrameContext context, double pitch, out double nameWidth)
    {
        var f = pitch / context.Px(SlimRowPitch);
        var barX = context.Margins.Left + context.Px(104 * f);
        var right = context.Width - context.Margins.Right - context.Px(10);
        var room = Math.Max(context.Px(120), (right - barX) * SlimNameShare);

        var widest = string.Empty;
        var widestAt = 0.0;
        using var probe = Ink.Format(context.Px(SlimFont * f), bold: true);

        for (var k = 0; k < _series.Racers; k++)
        {
            var name = _series.Entries[k].Name;
            var width = Ink.Measure(session, name, probe);

            if (width > widestAt)
            {
                widestAt = width;
                widest = name;
            }
        }

        var size = Ink.FitSize(session, widest, context.Px(SlimFont * f), room, bold: true);
        nameWidth = Ink.Measure(session, widest, Ink.Format(size, bold: true));

        return Ink.Format(size, bold: true);
    }

    /// <summary>The slim row under the podium or the pyramid: rank, a colour chip, one bar
    /// to scale with its value riding the end, the name at the edge. The row's y is the
    /// slot itself, so a member leaving the podium slides into its row without a cut.
    /// Every measure inside scales by <paramref name="pitch"/> against the design row, so
    /// a compressed row band reads small but never overlaps.</summary>
    private void DrawSlimRow(
        CanvasDrawingSession session, FrameContext context, int k, double s, double value,
        double yc, double alpha, double axisMax, double pitch, CanvasTextFormat nameFormat, double nameWidth)
    {
        var f = pitch / context.Px(SlimRowPitch);
        var x0 = context.Margins.Left + context.Px(8);
        var right = context.Width - context.Margins.Right - context.Px(10);
        var rank = (int)Math.Floor(s) + 1;

        using var rankFormat = Ink.Format(context.Px(SlimFont * f), bold: true);
        using var valueFormat = Ink.Format(context.Px(SlimFont * f), bold: true);

        Ink.RightMiddle(session, rank.ToString(CultureInfo.InvariantCulture),
            x0 + context.Px(30 * f), yc, rankFormat, Palette.Credit, alpha);

        // Where the career board drew a face: a **company logo** on its plate when the
        // racer is a listed company, otherwise the chip in the racer's own colour — the
        // same identity the bar carries, at the head of the row.
        var colour = ColourBySign
            ? (value >= 0 ? Rgb(0xEF, 0x44, 0x44) : Rgb(0x22, 0xC5, 0x5E))
            : Palette.Race16[Palette.RaceIndex(_series.Entries[k].Code)];
        var chipR = context.Px(SlimBadge * f) * 0.34;
        var chipCx = x0 + context.Px(68 * f);
        var faceKey = CompanyLogoCache.KeyOf(_series.Entries[k].Code);

        if (faceKey.Length > 0 && Faces is { } faces)
        {
            // The column badge's staging in miniature: plate, picture, and the racer's
            // own colour for the ring.
            var faceR = chipR * 1.45;

            session.FillCircle((float)chipCx, (float)yc, (float)faceR, Ink.Fade(BadgePlate, alpha));

            if (TryFace(session, _series.Entries[k].Code, chipCx, yc, faceR * 2, alpha))
            {
                session.DrawCircle((float)chipCx, (float)yc, (float)faceR,
                    Ink.Fade(colour, alpha), (float)(faceR * 0.07));
            }
            else
            {
                faces.Ensure(faceKey);

                session.FillCircle((float)chipCx, (float)yc, (float)chipR, Ink.Fade(colour, alpha));
            }
        }
        else
        {
            session.FillCircle((float)chipCx, (float)yc, (float)chipR, Ink.Fade(colour, alpha));
        }

        // The bar runs to the name and no further: the name's width is measured once for
        // the whole column, so a long name in any language costs the bar its room rather
        // than pushing the bar off the row.
        var barX = x0 + context.Px(104 * f);
        var barMax = Math.Max(context.Px(8), right - barX - nameWidth - context.Px(28 * f));
        var w = Math.Max(context.Px(4), (HeightOf(value) / Math.Max(axisMax, 1e-9)) * barMax);

        session.FillRoundedRectangle(
            (float)barX, (float)(yc - (context.Px(SlimBar * f) / 2)), (float)w, (float)context.Px(SlimBar * f),
            (float)Math.Min(context.Px(SlimBar * f) / 2, w / 2),
            (float)Math.Min(context.Px(SlimBar * f) / 2, w / 2), Ink.Fade(colour, alpha));

        // The value rides the bar's end — inside it when the bar is long enough to hold
        // its own label, just past the end when it is not. The same rule the bar staging
        // uses, for the same reason: the longest bar is the one that would push a label
        // outside into the names, and by construction it is also the one long enough to
        // hold it inside.
        var text = ValueText(value);
        var textWidth = Ink.Measure(session, text, valueFormat);
        var inside = w >= textWidth + context.Px(26 * f);

        if (inside)
        {
            Ink.RightMiddle(session, text, barX + w - context.Px(13 * f), yc, valueFormat, Ink.OnTopOf(colour), alpha);
        }
        else if (barX + w + context.Px(12 * f) + textWidth <= right - nameWidth - context.Px(8 * f))
        {
            Ink.LeftAt(session, text, barX + w + context.Px(12 * f), yc, valueFormat, colour, alpha);
        }

        Ink.RightMiddle(session, _series.Entries[k].Name, right, yc, nameFormat, RowInk, alpha);
    }

    private static string Iso(DateOnly day) => day.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    private static double Lerp(double a, double b, double t) => a + ((b - a) * t);

    private static double SmoothStep(double t) => (t * t) * (3 - (2 * t));

    private static Color Rgb(byte r, byte g, byte b) => Color.FromArgb(0xFF, r, g, b);
}

/// <summary>Every racer's chosen measure as a per-racer array over the shared days.</summary>
public static class SectorSeriesExtensions
{
    public static double[][] ReturnsOrAmounts(this SectorRaceSeries series, RaceMetric metric) =>
        metric is RaceMetric.Return ? [.. series.Returns] : [.. series.Amounts];
}
