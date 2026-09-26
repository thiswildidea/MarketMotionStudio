namespace MarketMotionStudio;

/// <summary>How a job ended.</summary>
public enum JobOutcome
{
    Succeeded,
    Failed,
    Cancelled,
}

/// <summary>A job that has finished, reported once so it can be announced.</summary>
public sealed record FinishedJob(string Name, JobOutcome Outcome, string? Detail);

/// <summary>
/// What the app is currently doing, for anything outside the page that started
/// it.
///
/// The pages run their long work through one wrapper, so this tracks it in one
/// place rather than asking each page to report itself. The window is the
/// consumer: an export runs for a while with the window usually behind
/// something else, and the title is the only thing it can still say.
/// </summary>
public sealed class BackgroundWork
{
    private readonly Lock _gate = new();
    private readonly Dictionary<Guid, string> _running = new();

    /// <summary>Raised when work starts, stops, or reports progress.</summary>
    public event EventHandler? Changed;

    /// <summary>Raised once per job that ends, with how it ended.</summary>
    public event EventHandler<FinishedJob>? Finished;

    public bool IsBusy
    {
        get { lock (_gate) { return _running.Count > 0; } }
    }

    public IReadOnlyList<string> Running
    {
        get { lock (_gate) { return [.. _running.Values]; } }
    }

    /// <summary>
    /// Registers a job for as long as the returned handle lives. Disposing it
    /// reports the outcome, so a job cannot be left showing as running by a path
    /// that forgot to close it.
    /// </summary>
    public Job Begin(string name)
    {
        var id = Guid.NewGuid();

        lock (_gate)
        {
            _running[id] = name;
        }

        Changed?.Invoke(this, EventArgs.Empty);
        return new Job(this, id, name);
    }

    private void Update(Guid id, string label)
    {
        lock (_gate)
        {
            if (!_running.ContainsKey(id))
            {
                return;
            }

            _running[id] = label;
        }

        Changed?.Invoke(this, EventArgs.Empty);
    }

    private void End(Guid id, string name, JobOutcome outcome, string? detail)
    {
        bool known;

        lock (_gate)
        {
            known = _running.Remove(id);
        }

        if (!known)
        {
            return;
        }

        Changed?.Invoke(this, EventArgs.Empty);
        Finished?.Invoke(this, new FinishedJob(name, outcome, detail));
    }

    public sealed class Job(BackgroundWork owner, Guid id, string name) : IDisposable
    {
        private JobOutcome _outcome = JobOutcome.Succeeded;
        private string? _detail;
        private bool _ended;

        /// <summary>Replaces what this job is described as while it runs.</summary>
        public void Report(string label) => owner.Update(id, label);

        public void Failed(string detail)
        {
            _outcome = JobOutcome.Failed;
            _detail = detail;
        }

        public void Cancelled() => _outcome = JobOutcome.Cancelled;

        public void Dispose()
        {
            if (_ended)
            {
                return;
            }

            _ended = true;
            owner.End(id, name, _outcome, _detail);
        }
    }
}
