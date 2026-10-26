using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Windows.Storage;

namespace MarketMotionStudio.Render;

/// <summary>
/// Company logos for the race badges — the market's answer to the career board's
/// headshots, behind the same shape of contract: bitmaps cached **per device** (a
/// preview control and an export device are separate D3D devices and cannot share
/// one), loads deduplicated and never awaited on the draw thread, and a code with
/// no logo answered by the first-character badge the draw already knows.
///
/// The source is THS's company page: one fetch of
/// <c>basic.10jqka.com.cn/{code}/company.html</c> yields a per-company logo URL
/// (a GUID path under its own host), which is downloaded and kept in
/// LocalState/logos forever — so each code costs its two requests exactly once
/// in the app's life, and every frame after that reads the disk.
///
/// Keyed by <see cref="KeyOf"/>: only stock-shaped codes (six digits under an
/// A-share venue prefix) get a key. Indexes, boards, dates and coins are the
/// things the badge's first character is for, and they keep it.
/// </summary>
public sealed class CompanyLogoCache
{
    /// <summary>The square's device pixels — every image is masked to this on load.</summary>
    public const int Size = 96;

    /// <summary>The one cache the whole app shares: every race page's renderer meets it.</summary>
    public static CompanyLogoCache Shared { get; } = new();

    /// <summary>Hop to the UI thread for the invalidation; null on an export thread, where
    /// nobody is watching and no redraw is needed.</summary>
    public Func<Action, bool>? Marshal { get; set; }

    /// <summary>Called once a late-downloading logo lands, so the preview redraws.</summary>
    public Action? Invalidated { get; set; }

    private static readonly HttpClient Http = new()
    {
        Timeout = TimeSpan.FromSeconds(15),
    };

    static CompanyLogoCache()
    {
        Http.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (MarketMotionStudio)");
    }

    private readonly Lock _gate = new();
    private readonly ConditionalWeakTable<CanvasDevice, Dictionary<string, CanvasBitmap?>> _byDevice = new();

    /// <summary>Downloads currently running, keyed by code — one task per code at a time.</summary>
    private readonly Dictionary<string, Task<bool>> _inflight = [];

    /// <summary>Codes this process already asked for and got nothing usable back — one
    /// attempt per code per session, so a missing logo costs one pair of requests.</summary>
    private static readonly HashSet<string> Failed = [];

    /// <summary>Consecutive download failures. Five in a row means the road is down —
    /// further asks give up instantly until a success (or a restart) resets the count.</summary>
    private static int _deadNetwork;

    /// <summary>Two hops at a time, with a beat between them, and why: the source is
    /// somebody else's page, and a two-hundred-listing board assigning <see cref="Faces"/>
    /// fires two hundred Ensures at once. A burst that size is the behaviour of a scraper
    /// — the page answers it with challenge pages that simply fail the logo regex — so
    /// the downloads queue politely instead, the way the app's own market fetches do.</summary>
    private static readonly SemaphoreSlim Road = new(2, 2);

    private static string Dir => Path.Combine(ApplicationData.Current.LocalFolder.Path, "logos");

    private static string LocalPath(string key) => Path.Combine(Dir, key + ".png");

    /// <summary>
    /// The logo key a race entry's code carries, or the empty string when the entry is
    /// not a listed company: A-share stocks are six digits under <c>sh</c>/<c>sz</c>/<c>bj</c>,
    /// while indexes (<c>sh000…</c>, <c>sz399…</c>), funds, HK/US listings and coins are the
    /// shapes the first-character badge already answers for.
    /// </summary>
    public static string KeyOf(string code)
    {
        if (code.Length != 8)
        {
            return string.Empty;
        }

        var venue = code[..2].ToLowerInvariant();
        var digits = code[2..];

        return venue switch
        {
            "sh" when digits.StartsWith("60") || digits.StartsWith("68") => digits,
            "sz" when digits.StartsWith("00") || digits.StartsWith("30") => digits,
            "bj" when digits.StartsWith("43") || digits.StartsWith("83")
                   || digits.StartsWith("87") || digits.StartsWith("92") => digits,
            _ => string.Empty,
        };
    }

    /// <summary>The logo for a key on this device, or null while nothing is on disk yet —
    /// the caller draws the first-character badge for that frame.
    ///
    /// Synchronous, and the one blocking wait in the drawing path, per picture per device:
    /// the same trade the backdrop's decoder made, so a draw that has a file always has a
    /// picture.</summary>
    public CanvasBitmap? Peek(CanvasDevice device, string key)
    {
        var map = _byDevice.GetValue(device, static _ => []);

        lock (map)
        {
            if (map.TryGetValue(key, out var cached))
            {
                return cached;
            }

            var path = LocalPath(key);

            if (!File.Exists(path))
            {
                return null;
            }

            try
            {
                var bitmap = MaskedAsync(device, path).GetAwaiter().GetResult();
                map[key] = bitmap;

                return bitmap;
            }
            catch (Exception ex)
            {
                // Unreadable file or a torn-down device: record the miss so the per-frame
                // ask stops until a fresh download rewrites the file.
                Diagnostics.CrashLog.Note(
                    $"logo: {key} not decoded, {ex.GetType().Name}: {ex.Message}");

                map[key] = null;

                return null;
            }
        }
    }

    /// <summary>Starts a download if none is running. Cheap when warm; safe every frame.
    /// Fire-and-forget from the draw path — the frame that asked draws the badge, and the
    /// invalidation repaints once the file lands.</summary>
    public void Ensure(string key)
    {
        if (key.Length == 0 || File.Exists(LocalPath(key)))
        {
            return;
        }

        lock (_gate)
        {
            if (_inflight.ContainsKey(key) || Failed.Contains(key)
                || Volatile.Read(ref _deadNetwork) >= 5)
            {
                return;
            }

            _inflight[key] = DownloadAsync(key);
        }
    }

    /// <summary>Awaits the pending downloads — the export path — up to a limit. The
    /// queue is polite (two hops at a time), so a cold cache of two hundred boards'
    /// codes would take minutes to drain; an export waits its half a minute and then
    /// draws the first-character badge for whoever is still on the road, exactly as
    /// the preview does.</summary>
    public async Task WarmAsync(IReadOnlyCollection<string> keys, TimeSpan? limit = null)
    {
        foreach (var key in keys)
        {
            Ensure(key);
        }

        Task<bool>[] running;

        lock (_gate)
        {
            running = [.. _inflight.Values];
        }

        if (running.Length == 0)
        {
            return;
        }

        try
        {
            await Task.WhenAll(running).WaitAsync(limit ?? TimeSpan.FromSeconds(30));
        }
        catch (TimeoutException)
        {
            // Still on the road at the deadline: the frames fall back to the badge,
            // the way a preview does while a picture is landing.
        }
    }

    /// <summary>One code's logo: the company page names the picture, the picture lands in
    /// LocalState where <see cref="Peek"/> finds it ever after. False when the page or the
    /// picture cannot be had.</summary>
    private async Task<bool> DownloadAsync(string key)
    {
        try
        {
            var ok = await FetchAsync(key);

            if (ok)
            {
                Note();
            }

            return ok;
        }
        finally
        {
            lock (_gate)
            {
                _inflight.Remove(key);
            }
        }
    }

    private async Task<bool> FetchAsync(string key)
    {
        await Road.WaitAsync();

        try
        {
            return await FetchPoliteAsync(key);
        }
        finally
        {
            Road.Release();
        }
    }

    private static async Task<bool> FetchPoliteAsync(string key)
    {
        try
        {
            var html = await Http.GetStringAsync($"https://basic.10jqka.com.cn/{key}/company.html");

            var match = Regex.Match(
                html, "https://[^\"'\\s]+company-logo/[^\"'\\s]+\\.png",
                RegexOptions.CultureInvariant);

            if (!match.Success)
            {
                Diagnostics.CrashLog.Note($"logo: {key} page carried no logo link");

                lock (Failed)
                {
                    Failed.Add(key);
                }

                return false;
            }

            var bytes = await Http.GetByteArrayAsync(match.Value);

            // A wrong answer here is a banner or an error page wearing a .png name;
            // a real logo is a PNG of non-trivial size.
            if (bytes.Length < 500 || bytes[0] != 0x89)
            {
                Diagnostics.CrashLog.Note($"logo: {key} answer was not a picture ({bytes.Length} B)");

                lock (Failed)
                {
                    Failed.Add(key);
                }

                return false;
            }

            Volatile.Write(ref _deadNetwork, 0);

            Directory.CreateDirectory(Dir);

            var path = LocalPath(key);
            var temp = path + ".tmp";

            File.WriteAllBytes(temp, bytes);
            File.Move(temp, path, overwrite: true);

            return true;
        }
        catch (Exception ex)
        {
            Interlocked.Increment(ref _deadNetwork);

            Diagnostics.CrashLog.Note(
                $"logo: {key} download failed, {ex.GetType().Name}: {ex.Message}");

            lock (Failed)
            {
                Failed.Add(key);
            }

            return false;
        }
        finally
        {
            // The beat between hops: serial politeness, the market fetch's own rule.
            await Task.Delay(250);
        }
    }

    private void Note()
    {
        if (Invalidated is { } note)
        {
            if (Marshal is { } marshal)
            {
                marshal(note);
            }
            else
            {
                note();
            }
        }
    }

    /// <summary>Loads, cover-crops to a square and masks to a **circle** — once per image,
    /// at load time, so the draw path is a plain DrawImage. Most listings' marks are round
    /// plates anyway; a square mark loses only what a circle would cover.</summary>
    private static async Task<CanvasBitmap> MaskedAsync(CanvasDevice device, string path)
    {
        // ConfigureAwait(false) everywhere, and why it is not decoration: Peek answers
        // the draw path with a blocking GetResult, and when that path is the UI thread
        // the block must not also own the context this method's continuation wants to
        // resume on — decode finishes, queues the rest of this method to the thread
        // that is waiting for it, and the app freezes until it is killed. The awaited
        // load and the masking below are free-threaded (Win2D), so resuming on the
        // pool costs nothing; Backdrop's own blocking load stays safe for the same
        // reason a level lower — it waits on the operation's task itself, with no
        // continuation of its own to marshal back.
        var source = await CanvasBitmap.LoadAsync(device, path).AsTask().ConfigureAwait(false);

        var target = new CanvasRenderTarget(device, Size, Size, 96);
        var w = (float)source.SizeInPixels.Width;
        var h = (float)source.SizeInPixels.Height;
        var scale = Size / Math.Min(w, h);

        using (var ds = target.CreateDrawingSession())
        {
            ds.Clear(Windows.UI.Color.FromArgb(0, 0, 0, 0));

            // Radius half the side: the rounded rectangle becomes the circle the badge asks for.
            var radius = Size * 0.5f;

            using (ds.CreateLayer(1f, CanvasGeometry.CreateRoundedRectangle(
                ds, 0, 0, Size, Size, radius, radius)))
            {
                ds.Transform = System.Numerics.Matrix3x2.CreateScale(scale)
                    * System.Numerics.Matrix3x2.CreateTranslation((Size - (w * scale)) / 2f, (Size - (h * scale)) / 2f);
                ds.DrawImage(source, 0, 0);
            }
        }

        source.Dispose();

        return target;
    }
}
