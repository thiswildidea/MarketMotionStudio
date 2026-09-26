namespace MarketMotionStudio.Render;

/// <summary>
/// The parts of a vertical video that the host app covers with its own interface.
///
/// These are proportions of the frame, not pixels, because that is how the
/// platforms behave: the caption block and the button rail scale with the screen
/// rather than sitting at fixed offsets.
///
/// Two separate jobs come out of one set of numbers, and keeping them apart
/// matters:
///
/// <list type="bullet">
/// <item><description><b>The render honours <see cref="Top"/>.</b> The title
/// block is positioned below it in every animation, so a phone's status bar and
/// the player's own chrome cannot sit on top of the one line that says what the
/// video is about. This is not optional and there is no switch for
/// it.</description></item>
/// <item><description><b>The preview can draw all three as guides.</b> That is a
/// diagnostic for the person composing the shot, and it must never reach the
/// file. The guides are drawn by the preview control and not by the frame
/// renderer the encoder calls, which is what makes that guarantee structural
/// rather than a flag somebody has to remember to clear.</description></item>
/// </list>
/// </summary>
public static class SafeArea
{
    /// <summary>Status bar and the host's own header. The render respects this.</summary>
    public const double Top = 0.12;

    /// <summary>The vertical rail of buttons down the right-hand side.</summary>
    public const double Right = 0.18;

    /// <summary>Caption, account name and the audio credit.</summary>
    public const double Bottom = 0.22;
}
