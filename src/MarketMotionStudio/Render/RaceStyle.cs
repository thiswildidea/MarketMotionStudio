namespace MarketMotionStudio.Render;

/// <summary>
/// How the race draws its field. The bar race is the original; the other four re-stage the
/// same interpolated ranking — every one of them reads the same per-frame values, slots and
/// axis the bars do, so a style switch changes the drawing and never the standings.
///
/// The five names, their staging code and their pacing come over from NbaMotionStudio's
/// career-race renderer, where they shipped first. Two adaptations travel with them: a race
/// of companies and sectors has no headshots, so every place the career board drew a face
/// draws a badge — the plate and its ring, with the racer's own first character inside —
/// and a board whose rows can go either way (the extreme days) sizes its columns by the
/// same magnitude it ranks by, so a −7.7% day stands as tall as a +8.1% one.
/// </summary>
public enum RaceStyle
{
    /// <summary>Horizontal bars overtaking one another — the original race.</summary>
    Bar,

    /// <summary>Three medal columns on a podium, the ranks below as slim rows.</summary>
    Podium,

    /// <summary>One column per racer, side by side, reordering like a skyline.</summary>
    Skyline,

    /// <summary>Tiered cards — a throne on top, then 2, then 3, then slim rows.</summary>
    Pyramid,

    /// <summary>The skyline with a camera: it races globally, then walks up the board,
    /// pushing in on each column through to the first — a big badge, the name, the
    /// total — and pulls back out to the whole chart. Same standings, two movements plus
    /// the walk.</summary>
    FocusTour,
}
