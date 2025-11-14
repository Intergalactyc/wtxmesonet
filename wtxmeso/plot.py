import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.collections import Collection

class View:
    def __init__(self, name: str, plot_funcs: list, nrows=None, ncols=None):
        # Plot functions should return a twin axes (if one exists) or None
        self.name = name
        self.plot_funcs = plot_funcs
        self.axes = []
        self.twins = [[] for _ in self.plot_funcs]
        n_plots = len(self.plot_funcs)
        self.nrows = nrows or int(np.ceil(np.sqrt(n_plots)))
        self.ncols = ncols or int(np.ceil(n_plots / self.nrows))

    def create_axes(self, fig):
        self.axes = []

        for i, func in enumerate(self.plot_funcs, start=1):
            ax = fig.add_subplot(self.nrows, self.ncols, i)
            ax.set_visible(False)
            self.axes.append(ax)

    def draw(self):
        for i, (func, ax) in enumerate(zip(self.plot_funcs, self.axes)):
            ax.clear()
            ax.set_visible(True)
            twin = func(ax.figure, ax)
            if twin:
                self.twins[i] = [twin]
            self._make_legend_interactive(ax, twin)

        # for i, ax in enumerate(self.axes):
        #     if i // self.ncols < self.nrows - 1:
        #         ax.set_xticklabels([])

        self.axes[0].figure.tight_layout()

    def hide(self):
        for ax, twin_list in zip(self.axes, self.twins):
            ax.set_visible(False)
            for twin in twin_list:
                twin.remove()

    def _make_legend_interactive(self, ax, ax2=None):
        # ax2 is twin axes
        handles, labels = ax.get_legend_handles_labels()
        if ax2 is not None:
            h2, l2 = ax2.get_legend_handles_labels()
            handles += h2
            labels += l2

        if not handles:
            return

        leg = ax.legend(handles, labels, markerscale=4)

        legend_map = {}
        for leg_handle, orig in zip(leg.legend_handles, handles):
            leg_handle.set_picker(True)
            legend_map[leg_handle] = orig

        def on_pick(event):
            # not working for twin ax...
            leg_handle = event.artist
            orig = legend_map.get(leg_handle)
            if orig is None:
                return

            if isinstance(orig, Line2D):
                visible = not orig.get_visible()
                orig.set_visible(visible)
            elif isinstance(orig, Collection):
                visible = not orig.get_visible()
                orig.set_visible(visible)

            leg_handle.set_alpha(1.0 if visible else 0.2)
            ax.figure.canvas.draw_idle()

        ax.figure.canvas.mpl_connect("pick_event", on_pick)

class InteractivePlotter:
    def __init__(self, name: str, views: list[View], figsize=(11.,6.5)):
        self.name = name
        self.views = views
        self.current = 0
        self.fig = plt.figure(figsize=figsize)

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
        view_name = ""
        for i, view in enumerate(self.views):
            if i == self.current:
                view.draw()
                view_name = view.name
            else:
                view.hide()
        self.fig.suptitle(f"{self.name} - {view_name} (View {self.current+1}/{len(self.views)})")
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
