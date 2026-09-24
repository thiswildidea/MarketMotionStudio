using Microsoft.UI.Windowing;
using Windows.Graphics;
using Windows.Storage;

namespace AShareMotionStudio;

/// <summary>
/// Where the window was last time.
///
/// The preview is a fixed 9:16 frame beside a parameter panel, so how tall the
/// window is decides how large the thing being judged appears. People size this
/// window once and deliberately; opening at the default on every launch throws
/// that away daily.
///
/// The state is stored, not the maximised bounds. A maximised window reports a
/// size that covers the screen, and restoring that as an ordinary window gives
/// something that looks maximised, is not, and cannot be restored to the size
/// the user actually chose.
/// </summary>
public static class WindowPlacement
{
    private const string Key = "WindowPlacement";

    /// <summary>
    /// Small enough that a window this size is unusable and was almost certainly
    /// never chosen. Guards against a stored zero.
    /// </summary>
    private const int Smallest = 400;

    public static void Restore(AppWindow window)
    {
        if (ApplicationData.Current.LocalSettings.Values[Key] is not string saved)
        {
            return;
        }

        var parts = saved.Split(',');

        if (parts.Length != 5 ||
            !int.TryParse(parts[0], out var x) || !int.TryParse(parts[1], out var y) ||
            !int.TryParse(parts[2], out var width) || !int.TryParse(parts[3], out var height))
        {
            return;
        }

        if (width < Smallest || height < Smallest)
        {
            return;
        }

        var wanted = new RectInt32(x, y, width, height);

        // A saved position can point at a monitor that is no longer there: a
        // laptop undocked, a screen unplugged, a resolution changed. Restoring it
        // verbatim puts the window somewhere nobody can see and looks exactly
        // like the app failing to start.
        if (!IsOnScreen(wanted))
        {
            return;
        }

        window.MoveAndResize(wanted);

        if (parts[4] == "max" && window.Presenter is OverlappedPresenter presenter)
        {
            presenter.Maximize();
        }
    }

    public static void Save(AppWindow window)
    {
        // Minimised is not a placement worth keeping. Restoring into it would
        // start the app into the taskbar with no window at all.
        if (window.Presenter is not OverlappedPresenter presenter ||
            presenter.State is OverlappedPresenterState.Minimized)
        {
            return;
        }

        var maximised = presenter.State is OverlappedPresenterState.Maximized;

        // Taken before maximising is considered, so the remembered size is the
        // one the window had as an ordinary window.
        var area = window.Position;
        var size = window.Size;

        ApplicationData.Current.LocalSettings.Values[Key] =
            $"{area.X},{area.Y},{size.Width},{size.Height},{(maximised ? "max" : "normal")}";
    }

    /// <summary>
    /// Whether any part of the rectangle lands on a display that exists now.
    ///
    /// <c>Nearest</c> rather than <c>Primary</c>: the nearest display to a
    /// rectangle on a monitor that is gone is a real one, and comparing against
    /// it is what detects that the rectangle is nowhere.
    /// </summary>
    private static bool IsOnScreen(RectInt32 rect)
    {
        var display = DisplayArea.GetFromRect(rect, DisplayAreaFallback.Nearest);

        if (display is null)
        {
            return false;
        }

        var work = display.WorkArea;

        return rect.X < work.X + work.Width &&
               rect.Y < work.Y + work.Height &&
               rect.X + rect.Width > work.X &&
               rect.Y + rect.Height > work.Y;
    }
}
