using System.Net.Http;
using AShareMotionStudio.Market;

namespace AShareMotionStudio;

/// <summary>
/// The few things that outlive a page.
///
/// Small on purpose, and it is worth saying why: the shell this app is built on
/// keeps portal sessions, a shared inventory and its invalidation rules here,
/// because there every page acted on one remote organization and had to agree
/// with the others about which. Nothing here is shared in that way — a page owns
/// its own series, its own parameters and its own render — so the only thing
/// that has to be process-wide is what is currently running, which the window
/// reads to say so in its title.
///
/// Resisting the urge to put the fetched series here is deliberate. Two pages
/// drawing two different indicators of two different things have no cache to
/// share, and a shared one would only create the question of when to invalidate
/// it.
/// </summary>
public sealed class AppServices
{
    public static AppServices Current { get; } = new();

    private AppServices()
    {
        // One HttpClient for the life of the process. A new one per request leaks sockets
        // in TIME_WAIT under repeated use, and three venue requests per fetch is repeated
        // use. The timeout is generous because the quote endpoint is occasionally slow
        // rather than broken, and each page wraps its own work in a shorter cancellation
        // anyway.
        _http = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };

        // Sent because the endpoint is a public one belonging to somebody else: a request
        // that says what it is can be identified and, if it is unwelcome, blocked
        // deliberately rather than by fingerprinting.
        _http.DefaultRequestHeaders.UserAgent.ParseAdd("AShareMotionStudio/0.1");

        Quotes = new TencentKline(_http);
    }

    private readonly HttpClient _http;

    public BackgroundWork Work { get; } = new();

    /// <summary>The one route to a quote source.</summary>
    public TencentKline Quotes { get; }
}
