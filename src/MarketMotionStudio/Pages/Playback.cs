using System.Diagnostics;
using Microsoft.UI.Xaml;

namespace MarketMotionStudio.Pages;

/// <summary>
/// A page that can show a moment of its own animation.
/// </summary>
internal interface IPlaybackHost
{
    /// <summary>How long the finished video will be.</summary>
    TimeSpan PlaybackDuration { get; }

    /// <summary>Show the frame at this fraction of the way through.</summary>
    void ShowMoment(double progress);

    /// <summary>Reflect whether playback is running, on whatever control says so.</summary>
    void ShowPlaybackState(bool playing);
}

/// <summary>
/// Plays a preview through at the speed it will be watched at, pausing where it is told to.
///
/// Wall-clock here, and deliberately: a preview exists to answer "is this too fast
/// to read", which can only be answered in real time. That is the opposite of the
/// export, which must not be tied to the clock — see <see cref="Render.IFrameRenderer"/>
/// for why the two are separate, and why the tools this replaces could not make
/// that separation.
///
/// It drives the position by elapsed time rather than by counting ticks. A dropped
/// frame then shows as a frame that was skipped, which is what a dropped frame is;
/// counting ticks instead would make a slow render come out as a video that runs
/// long, so the preview would disagree with the file about the duration.
/// </summary>
internal sealed class Playback(IPlaybackHost host)
{
    private readonly DispatcherTimer _timer = new() { Interval = TimeSpan.FromSeconds(1.0 / 60) };
    private readonly Stopwatch _clock = new();
    private bool _wired;

    /// <summary>
    /// How far into the animation playback already is, in seconds, for the time it is not
    /// running.
    ///
    /// Held rather than left on the stopwatch, because a pause and a stop are the same
    /// button here and only one of them means "from the beginning". Zeroing the clock on
    /// every start made the button read 暂停 while behaving like a rewind: a press halfway
    /// through took the picture back to the first frame and ran it again. The word on the
    /// button was a promise the class did not keep, and this is the promise.
    ///
    /// It also lets a scrub be honoured. Dragging the slider moves the picture; a press
    /// afterwards has to take the picture's word for where it is, not go back to wherever
    /// the last run happened to have stopped.
    ///
    /// Seconds, not a fraction: the duration slider can be moved while playback is paused,
    /// and a held fraction would silently re-interpret the same pause against a new length.
    /// </summary>
    private double _held;

    public bool IsPlaying => _timer.IsEnabled;

    public void Toggle()
    {
        if (IsPlaying)
        {
            Stop();
        }
        else
        {
            Start();
        }
    }

    /// <summary>
    /// Puts playback at <paramref name="progress"/>, stopping first.
    ///
    /// One path for every way the position is moved — a scrub, a "play it again" at the
    /// end — so the picture and the clock cannot be set by different callers and disagree
    /// about where they are. Stopping matters because the time already on the clock is
    /// owed to <see cref="_held"/>; carrying it across a move would add it to a position
    /// that has just been set to something else.
    /// </summary>
    public void Seek(double progress)
    {
        Stop();

        var at = Math.Clamp(progress, 0, 1);

        _held = at * host.PlaybackDuration.TotalSeconds;
        host.ShowMoment(at);
    }

    public void Start()
    {
        var total = host.PlaybackDuration.TotalSeconds;

        // Nothing left to play is not a reason to refuse; it is a reason to start over.
        // Reached on its own after a run finishes, where stopping leaves the held position
        // at the duration, and by anyone who starts a clip that is already at its end.
        if (_held >= total)
        {
            _held = 0;
        }

        if (!_wired)
        {
            _timer.Tick += OnTick;
            _wired = true;
        }

        _clock.Restart();
        _timer.Start();
        host.ShowPlaybackState(playing: true);
    }

    public void Stop()
    {
        if (!IsPlaying)
        {
            return;
        }

        _timer.Stop();
        _clock.Stop();

        // Banked, not discarded: the run is over but the position it reached is not.
        _held += _clock.Elapsed.TotalSeconds;

        host.ShowPlaybackState(playing: false);
    }

    private void OnTick(object? sender, object e)
    {
        var total = host.PlaybackDuration.TotalSeconds;

        var elapsed = _held + _clock.Elapsed.TotalSeconds;

        // A zero duration cannot happen through the slider, but it can arrive from
        // a restored preference, and dividing by it would put the position at
        // infinity and draw nothing at all.
        var progress = total <= 0 ? 1 : elapsed / total;

        if (progress >= 1)
        {
            // Held on the last frame rather than rewound. The end of one of these
            // animations is where the statistics appear, and it is the frame people
            // want to look at after watching it — rewinding would take it away at
            // the moment it arrived.
            host.ShowMoment(1);

            // Stopping banks the elapsed time, which puts the held position at the end;
            // the next start sees that and begins again. The clip is finished, so the
            // only thing left for the button to mean is "once more".
            Stop();
            return;
        }

        host.ShowMoment(progress);
    }
}
