using Microsoft.Graphics.Canvas;
using Windows.Foundation;
using Windows.UI;

namespace MarketMotionStudio.Render;

/// <summary>
/// The row of cards a multi-instrument frame ends on: one card per track, in the colour of its
/// own line, directly above the data-source credit.
///
/// It is the answer to the question such a frame leaves open. Names ride the leading ends of the
/// curves while they move, which is where a reader is looking — but the last thing anyone wants
/// off a comparison is the figures, and a figure on a moving label is a figure that has to be
/// chased. So the closing stretch puts them all in one row under the plot, in the order the
/// tracks are drawn, in the same colours: who is ahead, by how much, checked against the number
/// the label was showing a moment ago.
///
/// Here rather than in each of the three renderers that draw it — one shape, drawn by the
/// holdings board and by both of the candle board's layouts, with the same measurements and the
/// same spacing, so that a reader who has watched one of these frames already knows where to look
/// on the next. What each card *says* is the renderer's business; the four renderers fill in
/// different pairs of figures.
/// </summary>
public static class TrackCards
{
    /// <summary>Distance from the credit up to the top of the row, in baseline pixels.</summary>
    public const double AboveCredit = 192;

    /// <summary>How tall a card is.</summary>
    public const double Height = 132;

    /// <summary>
    /// The room a frame keeps between its plot's foot and the top of the row: the date row, which
    /// every chart here draws under its own baseline.
    ///
    /// Stated as a second distance rather than folded into <see cref="AboveCredit"/> so that the
    /// gap a renderer passes to <see cref="FrameContext.BaselineAbove"/> can be *read* as its two
    /// parts, which is the difference between this and the two constants it replaces.
    /// </summary>
    public const double DateRowRoom = 238;

    /// <summary>From the plot's baseline down to the credit, with the row in it.</summary>
    public const double CreditGap = AboveCredit + DateRowRoom;

    /// <summary>
    /// One card: what the instrument is called, the colour of its line, and its two figures — the
    /// one read first and the one it is checked against. See <see cref="Draw"/>.
    /// </summary>
    /// <param name="Name">The instrument's name, in the interface language.</param>
    /// <param name="NameInk">
    /// What the name is drawn in. A parameter rather than a constant because the three boards
    /// answer it two ways: the candle frame tints the name with the track's own colour, which is
    /// what makes a card identify its line at a glance, and the holdings board has always drawn
    /// it in the muted tone it uses for card labels. A frame is not the place to re-decide the
    /// other one's look.
    /// </param>
    /// <param name="Ink">The card's border and its headline figure — the track's own colour.</param>
    /// <param name="Value">The headline: the figure the card exists to state.</param>
    /// <param name="Note">The line under it, in the muted tone: what <paramref name="Value"/> is checked against.</param>
    public readonly record struct Card(
        string Name, Color NameInk, Color Ink, string Value, string Note);

    /// <summary>
    /// Draws the row across the frame's own chart width — or as far of it as the host's button
    /// rail leaves free — once every card has arrived (the caller owns the fade, as it owns when
    /// the closing stretch starts).
    ///
    /// The cards share the width equally and the name is fitted to whatever that gives it: six
    /// cards on a narrow frame is the case that has to work, and a name that runs past its own
    /// border reads as a broken layout rather than as a long name.
    /// </summary>
    /// <param name="giveWay">
    /// How much of the host's button rail the row keeps clear, on the same scale as
    /// <see cref="FrameContext.SafeRight"/> — 1 is all of it, 0 is none.
    ///
    /// Here rather than left at the full chart width, which is what this row did at first and
    /// what the pixels caught: the rail is 18% of a 1080-wide frame, the chart's right margin is
    /// 150, so the row's right edge landed **44 px inside the rail** — the last card's own
    /// figures under the avatar and the comment button in the one frame that exists to state
    /// them. A row of figures is content, and content does not spend the band a page asked to
    /// keep clear. It costs the frame nothing to ask: the switch that decides this is already
    /// on all four pages, and the two that offer to use the band get the wider row with it.
    /// </param>
    public static void Draw(
        CanvasDrawingSession session, FrameContext context, IReadOnlyList<Card> cards, double opacity,
        double giveWay = 1)
    {
        if (cards.Count == 0 || opacity <= 0)
        {
            return;
        }

        var left = context.ChartLeft;
        var right = Math.Min(context.ChartRight, context.SafeRight(giveWay));
        var gap = context.Px(14);
        var cardWidth = (right - left - (gap * (cards.Count - 1))) / cards.Count;
        var cardHeight = context.Px(Height);
        var y = context.CreditLine - context.Px(AboveCredit);
        var radius = (float)context.Px(14);

        using var noteFormat = Ink.Format(context.Px(24));
        using var valueFormat = Ink.Format(context.Px(34), bold: true);

        for (var i = 0; i < cards.Count; i++)
        {
            var card = cards[i];
            var x = left + (i * (cardWidth + gap));
            var box = new Rect(x, y, cardWidth, cardHeight);
            var cx = x + (cardWidth / 2);

            session.FillRoundedRectangle(box, radius, radius, Ink.Fade(Palette.CardFill, opacity));
            session.DrawRoundedRectangle(
                box, radius, radius, Ink.Fade(card.Ink, 0.75 * opacity), (float)context.Px(1.5));

            var nameSize = Ink.FitSize(
                session, card.Name, context.Px(22), cardWidth - context.Px(20), bold: false);

            using (var fitted = Ink.Format(nameSize))
            {
                Ink.Centred(session, card.Name, cx, y + context.Px(40), fitted, card.NameInk, opacity);
            }

            Ink.Centred(session, card.Value, cx, y + context.Px(80), valueFormat, card.Ink, opacity);
            Ink.Centred(session, card.Note, cx, y + context.Px(114), noteFormat, Palette.Muted, opacity);
        }
    }
}
