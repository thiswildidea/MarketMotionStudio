using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Foundation;

namespace MarketMotionStudio.Controls;

/// <summary>
/// A horizontal wrap panel: children keep their own natural width and flow onto the
/// next line when the row runs out.
///
/// The grid panels the framework ships are uniform-cell — every item gets the first
/// item's width — which was invisible while the interface was Chinese and became a
/// row of clipped buttons the moment a translation outgrew 「苹果」. Presets and
/// pickers are chips of genuinely varying width, so they want this instead.
/// </summary>
public sealed class WrapPanel : Panel
{
    protected override Size MeasureOverride(Size available)
    {
        var limit = double.IsInfinity(available.Width) ? double.MaxValue : available.Width;
        var x = 0.0;
        var y = 0.0;
        var line = 0.0;
        var widest = 0.0;

        foreach (var child in Children)
        {
            child.Measure(new Size(limit, double.MaxValue));

            var w = child.DesiredSize.Width;

            if (x > 0 && x + w > limit)
            {
                x = 0;
                y += line;
                line = 0;
            }

            x += w;
            line = Math.Max(line, child.DesiredSize.Height);
            widest = Math.Max(widest, x);
        }

        return new Size(widest, y + line);
    }

    protected override Size ArrangeOverride(Size final)
    {
        var x = 0.0;
        var y = 0.0;
        var line = 0.0;

        foreach (var child in Children)
        {
            var w = child.DesiredSize.Width;

            if (x > 0 && x + w > final.Width)
            {
                x = 0;
                y += line;
                line = 0;
            }

            child.Arrange(new Rect(x, y, w, child.DesiredSize.Height));
            x += w;
            line = Math.Max(line, child.DesiredSize.Height);
        }

        return final;
    }
}
