using Microsoft.UI.Xaml;
using Windows.Storage;

namespace AShareMotionStudio.Pages;

/// <summary>
/// Remembers a page's parameters between runs.
///
/// **The question, never the answer.** Range, duration, resolution, margins, the chosen form, the
/// typed title — these are re-entered every session otherwise, and that friction is what makes a
/// feature go unused. A fetched series is deliberately *not* stored: it belongs to one moment, so
/// keeping it would mean deciding how long it stays true, and a stale chart is worse than an empty
/// one. This is `page-state.mdc` made concrete.
///
/// Keys are prefixed per page, because the video and layout controls are one shared control used by
/// two indicators. Without the prefix, tuning the margins for the whole-market chart would silently
/// retune the per-stock one.
/// </summary>
public sealed class StudioPreferences(string prefix)
{
    private static readonly ApplicationDataContainer Store = ApplicationData.Current.LocalSettings;

    /// <summary>
    /// Writes are coalesced. Dragging a slider raises a change per step, and a settings write per
    /// step is a hundred writes for one gesture — so the last one within the window wins.
    /// </summary>
    private readonly DispatcherTimer _debounce = new() { Interval = TimeSpan.FromMilliseconds(400) };

    private Action? _pending;

    /// <summary>
    /// Raised while a restore is in progress, so the handlers that fire as controls are assigned do
    /// not write the value being restored back over itself.
    ///
    /// Public because the *page* owns the restore, and the flag has to cover the whole of it —
    /// including the assignments the page makes to its own controls, not just the ones this class
    /// can see.
    /// </summary>
    public bool Restoring { get; set; }

    public void Save(string key, string value) => Queue(key, value);

    public void Save(string key, int value) => Queue(key, value);

    public void Save(string key, double value) => Queue(key, value);

    public void Save(string key, bool value) => Queue(key, value);

    public string GetString(string key, string fallback) =>
        Store.Values[prefix + key] as string ?? fallback;

    public int GetInt(string key, int fallback) =>
        Store.Values[prefix + key] is int v ? v : fallback;

    public double GetDouble(string key, double fallback) =>
        Store.Values[prefix + key] is double v ? v : fallback;

    public bool GetBool(string key, bool fallback) =>
        Store.Values[prefix + key] is bool v ? v : fallback;

    private void Queue(string key, object value)
    {
        if (Restoring)
        {
            return;
        }

        var name = prefix + key;
        _pending += () => Store.Values[name] = value;

        if (!_debounce.IsEnabled)
        {
            _debounce.Tick += OnTick;
        }

        // Restarted rather than left running, so a continuous drag writes once when it stops rather
        // than every 400 ms while it continues.
        _debounce.Stop();
        _debounce.Start();
    }

    private void OnTick(object? sender, object e)
    {
        _debounce.Stop();
        _debounce.Tick -= OnTick;

        var work = _pending;
        _pending = null;

        try
        {
            work?.Invoke();
        }
        catch (Exception)
        {
            // Local settings can refuse — a quota, a corrupt container. Losing a remembered slider
            // position is not worth failing the page over, and the next change will try again.
        }
    }
}
