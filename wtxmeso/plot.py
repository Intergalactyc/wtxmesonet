import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt

class View:
    def __init__(self, plot_funcs):
        self.plot_funcs = plot_funcs
        self.axes = []

    def create_axes(self, fig):
        self.axes = [fig.add_subplot(len(self.plot_funcs), 1, i) for i in range(1, len(self.plot_funcs)+1)]
        for ax in self.axes:
            ax.set_visible(False)

    def draw(self):
        for func, ax in zip(self.plot_funcs, self.axes):
            ax.clear()
            ax.set_visible(True)
            func(ax.figure, ax)
            self._make_legend_interactive(ax)

    def hide(self):
        for ax in self.axes:
            ax.set_visible(False)

    def _make_legend_interactive(self, ax):
        handles, labels = ax.get_legend_handles_labels()
        if not handles:
            return

        leg = ax.legend(handles, labels)
        legend_map = {}

        for legline, orig in zip(leg.get_lines(), handles):
            legline.set_picker(True)
            legline.set_pickradius(5)
            legend_map[legline] = orig

        def on_pick(event):
            legline = event.artist
            orig = legend_map.get(legline)
            if orig is None:
                return
            visible = not orig.get_visible()
            orig.set_visible(visible)
            legline.set_alpha(1.0 if visible else 0.2)
            ax.figure.canvas.draw_idle()

        ax.figure.canvas.mpl_connect("pick_event", on_pick)


class InteractivePlotter:
    def __init__(self, views):
        self.views = views
        self.current = 0
        self.fig = plt.figure()

        for view in self.views:
            view.create_axes(self.fig)

        self._connect_keys()
        self._draw_current_view()

    def _connect_keys(self):
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _on_key(self, event):
        key = event.key.lower()
        if key in ("right", "left"):
            step = 1 if key == "right" else -1
            self.current = (self.current + step) % len(self.views)
            self._draw_current_view()

    def _draw_current_view(self):
        for i, view in enumerate(self.views):
            if i == self.current:
                view.draw()
            else:
                view.hide()
        self.fig.suptitle(f"View {self.current+1}/{len(self.views)}")
        self.fig.canvas.draw_idle()

    def show(self):
        self._draw_current_view()

        try:
            self.fig.canvas.manager.window.show()
            self.fig.canvas.manager.window.activateWindow()
            self.fig.canvas.manager.window.raise_()
        except AttributeError:
            pass

        self.fig.canvas.draw_idle()
