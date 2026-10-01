using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media.Animation;

namespace MarketMotionStudio;

/// <summary>
/// Back and forward through the pages visited, as a browser keeps them.
///
/// Pages, not what was asked of them. Every page here is cached by the frame, so
/// going back to one is going back to what it was showing — the period chosen,
/// the preview as it stood — not a fresh page that has to fetch again.
///
/// Ported from AgolAdminKit, where the same two buttons sit in the same place for
/// the same reason: the pane's own back button is turned off here, and the pane
/// itself is hidden behind its toggle on a narrow window — which is exactly when
/// the 9:16 preview wants the width.
///
/// A page the market has taken out of the pane is stepped over rather than opened.
/// That cannot happen today: switching market needs a restart, and a restart
/// begins with an empty history. The check is kept because the two facts are
/// decided in different places, and only one of them has to change.
/// </summary>
public sealed partial class MainWindow
{
    /// <summary>Far more than anyone steps back through; a bound so the list cannot grow all day.</summary>
    private const int HistoryLimit = 50;

    private readonly List<string> _backHistory = [];
    private readonly List<string> _forwardHistory = [];
    private string? _currentTag;

    /// <summary>Which way the navigation under way is moving through the history; 0 for a new visit.</summary>
    private int _historyStep;

    private void WireHistory()
    {
        // Handled events too: the preview surface and the parameter panel take
        // the press for themselves, and the side buttons should still mean back
        // and forward over them.
        Root.AddHandler(UIElement.PointerPressedEvent, new PointerEventHandler(OnHistoryPointerPressed), handledEventsToo: true);

        // Names and tooltips are set here rather than by x:Uid: the buttons carry
        // an icon and no label, so the resource would have to name an attached
        // property of a control in another namespace, a key form this app has
        // never used. The words are the same ones the Settings item's update
        // button gets, set the same way.
        NameHistoryButton(HistoryBackButton, "NavHistoryBack", "NavHistoryBackTip");
        NameHistoryButton(HistoryForwardButton, "NavHistoryForward", "NavHistoryForwardTip");

        SettleHistoryButtons();
    }

    private static void NameHistoryButton(Button button, string nameKey, string tipKey)
    {
        var tip = Localization.Strings.Get(tipKey);

        ToolTipService.SetToolTip(button, tip);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(button, Localization.Strings.Get(nameKey));
    }

    /// <summary>
    /// Called with every page shown. A new visit puts the page it leaves on
    /// the back list and forgets what was ahead, as a browser does; a step
    /// through the history has already moved the lists itself.
    /// </summary>
    private void RecordVisit(string tag)
    {
        var step = _historyStep;
        _historyStep = 0;

        if (tag == _currentTag)
        {
            return;
        }

        if (step == 0)
        {
            if (_currentTag is not null)
            {
                _backHistory.Add(_currentTag);

                if (_backHistory.Count > HistoryLimit)
                {
                    _backHistory.RemoveAt(0);
                }
            }

            _forwardHistory.Clear();
        }

        _currentTag = tag;
        SettleHistoryButtons();
    }

    /// <summary>The page slides in from the side it is on in the history; a new visit enters as before.</summary>
    private NavigationTransitionInfo HistoryTransition() => _historyStep switch
    {
        < 0 => new SlideNavigationTransitionInfo { Effect = SlideNavigationTransitionEffect.FromLeft },
        > 0 => new SlideNavigationTransitionInfo { Effect = SlideNavigationTransitionEffect.FromRight },
        _ => new EntranceNavigationTransitionInfo(),
    };

    private void OnHistoryBack(object sender, RoutedEventArgs e) => StepHistory(-1);

    private void OnHistoryForward(object sender, RoutedEventArgs e) => StepHistory(+1);

    private void OnHistoryPointerPressed(object sender, PointerRoutedEventArgs e)
    {
        var pressed = e.GetCurrentPoint(Root).Properties;

        if (pressed.IsXButton1Pressed)
        {
            StepHistory(-1);
            e.Handled = true;
        }
        else if (pressed.IsXButton2Pressed)
        {
            StepHistory(+1);
            e.Handled = true;
        }
    }

    /// <summary>
    /// Goes one page back or forward. A page no longer in the pane is passed over
    /// rather than opened: the whole-market turnover page, once a market without a
    /// whole-market figure is chosen.
    /// </summary>
    private void StepHistory(int step)
    {
        var from = step < 0 ? _backHistory : _forwardHistory;
        var to = step < 0 ? _forwardHistory : _backHistory;

        while (from.Count > 0)
        {
            var tag = from[^1];
            from.RemoveAt(from.Count - 1);

            if (!IsOffered(tag))
            {
                continue;
            }

            if (_currentTag is not null)
            {
                to.Add(_currentTag);
            }

            _historyStep = step;
            GoTo(tag);

            // The selection change navigates at once; this only matters when
            // it did not, so the next ordinary visit is not taken for a step.
            _historyStep = 0;
            break;
        }

        SettleHistoryButtons();
    }

    /// <summary>
    /// Moves the pane's selection rather than the frame, because the pane owns
    /// which page is shown and a page reached another way would leave the two
    /// disagreeing. Assigning the selection it already has raises nothing, so
    /// that case navigates directly.
    /// </summary>
    private void GoTo(string tag)
    {
        var destination = Nav.MenuItems
            .Concat(Nav.FooterMenuItems)
            .OfType<NavigationViewItem>()
            .FirstOrDefault(item => item.Tag as string == tag);

        if (destination is null)
        {
            return;
        }

        if (ReferenceEquals(Nav.SelectedItem, destination))
        {
            Navigate(tag);
        }
        else
        {
            Nav.SelectedItem = destination;
        }
    }

    private bool IsOffered(string tag) =>
        Nav.MenuItems
            .Concat(Nav.FooterMenuItems)
            .OfType<NavigationViewItem>()
            .Any(item => item.Tag as string == tag && item.Visibility == Visibility.Visible);

    private void SettleHistoryButtons()
    {
        HistoryBackButton.IsEnabled = _backHistory.Count > 0;
        HistoryForwardButton.IsEnabled = _forwardHistory.Count > 0;
    }
}
