using System.Diagnostics;
using Microsoft.UI.Xaml;

namespace AShareMotionStudio.Pages;

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
/// Plays a preview through at the speed it will be watched at.
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

    public void Start()
    {
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
        host.ShowPlaybackState(playing: false);
    }

    private void OnTick(object? sender, object e)
    {
        var total = host.PlaybackDuration.TotalSeconds;

        // A zero duration cannot happen through the slider, but it can arrive from
        // a restored preference, and dividing by it would put the position at
        // infinity and draw nothing at all.
        var progress = total <= 0 ? 1 : _clock.Elapsed.TotalSeconds / total;

        if (progress >= 1)
        {
            // Held on the last frame rather than rewound. The end of one of these
            // animations is where the statistics appear, and it is the frame people
            // want to look at after watching it — rewinding would take it away at
            // the moment it arrived.
            host.ShowMoment(1);
            Stop();
            return;
        }

        host.ShowMoment(progress);
    }
}
