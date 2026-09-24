namespace AShareMotionStudio.Render;

/// <summary>
/// The size, frame rate and bit rate a video will be written at.
///
/// Every drawing measurement in this app is expressed in **baseline pixels**
/// against 1080×1920 and multiplied by <see cref="Scale"/> at draw time. That is
/// the single rule that makes a resolution switch cost nothing: a margin the user
/// tuned at 1080p is still the same margin at 1440p, and no drawing code contains
/// a resolution.
/// </summary>
public sealed record VideoFormat(int Width, int Height, int FramesPerSecond, uint BitsPerSecond)
{
    /// <summary>
    /// The width every measurement in the app is written against. Vertical 9:16,
    /// because the output is for a phone.
    /// </summary>
    public const int BaselineWidth = 1080;

    public const int BaselineHeight = 1920;

    /// <summary>
    /// What a baseline measurement is multiplied by. Derived from the width
    /// rather than stored, so it cannot disagree with the size.
    /// </summary>
    public double Scale => (double)Width / BaselineWidth;

    /// <summary>How many frames a video of this length holds, at least one.</summary>
    public int FrameCount(TimeSpan duration) =>
        Math.Max(1, (int)Math.Round(duration.TotalSeconds * FramesPerSecond));

    /// <summary>
    /// The quality tiers, named by what they are for rather than by a number.
    /// The megabit figures are quoted at 1080p30 and scaled from there.
    /// </summary>
    public enum Quality
    {
        Standard,
        High,
        Ultra,
    }

    /// <summary>The three vertical sizes offered, shortest edge first.</summary>
    public static readonly (int Width, int Height)[] Sizes =
    [
        (720, 1280),
        (1080, 1920),
        (1440, 2560),
    ];

    /// <summary>
    /// Builds a format from the choices a user actually makes.
    ///
    /// The bit rate is scaled by pixel count and by frame rate rather than being
    /// three fixed numbers, because "high quality" means a number of bits per
    /// pixel per second and holding the megabits constant across 720p and 1440p
    /// would mean two different qualities under one label.
    /// </summary>
    public static VideoFormat Create(int width, int height, int fps, Quality quality)
    {
        var megabitsAt1080p30 = quality switch
        {
            Quality.Ultra => 16.0,
            Quality.High => 10.0,
            _ => 6.0,
        };

        var pixelRatio = (double)(width * height) / (BaselineWidth * BaselineHeight);
        var rateRatio = fps / 30.0;

        var bits = megabitsAt1080p30 * 1_000_000 * pixelRatio * rateRatio;

        return new VideoFormat(width, height, fps, (uint)Math.Round(bits));
    }

    /// <summary>What the default looks like before anyone touches a control.</summary>
    public static VideoFormat Default => Create(BaselineWidth, BaselineHeight, 30, Quality.High);

    /// <summary>
    /// The resolution part of an exported file's name, which is how someone
    /// checking a finished file confirms they got what they asked for.
    /// </summary>
    public string NameSuffix => $"{Width}x{Height}_{FramesPerSecond}fps";
}
