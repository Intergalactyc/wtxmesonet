import pandas as pd
from wtxmeso.plot import View, InteractivePlotter
import wtxmeso.units as u_

class Station:
    def __init__(self, name: str, city: str, county: str, state: str, latitude: float, longitude: float, elevation: int|float, identifier: str, logger_id: int, relocations: list[dict]):
        self.name = name
        self.city = city
        self.county = county
        self.state = state
        self.latitude = latitude # latitude in decimal degrees (+ is N, - is S)
        self.longitude = longitude # longitude in decimal degrees (+ is E, - is W)
        self.elevation = elevation # elevation in feet
        self.id_raw = identifier
        self.id = "".join(s for s in identifier if not s.isdigit())
        self.logger_id = logger_id
        self.relocations = relocations
        self.data = []
        self._data_length = 0

    def add_data(self, df: pd.DataFrame):
        self.data.append(df)
        self._data_length += len(df)

    def __str__(self):
        return f"Station(name: {self.name}, city: {self.city}, county: {self.county}, state: {self.state}, latitude: {self.latitude} degrees, longitude: {self.longitude} degrees, elevation: {self.elevation} feet, id: {self.id}, id_raw: {self.id_raw}, logger_id: {self.logger_id}, relocated: {bool(self.relocations)}, data_loaded: {bool(self.data)}, data_len: {self._data_length})"

    def __repr__(self):
        return self.__str__()

    @property
    def df(self):
        return pd.concat(self.data) if self.data else None

    def plot(self, from_reader: bool = False):
        if self.df is None:
            raise Exception(f"No data is associated with station {self.name}, nothing to plot")
        sp = StationPlot(self.name, self.df)
        sp.show(from_reader)

class StationPlot:
    def __init__(self, name: str, df: pd.DataFrame, xlabel="Time (UTC)"):
        self.df = df
        self.xlabel = xlabel

        # TODO: add validation to determine which views can be formed based on data available
            # Even better, customize the panels to only include variables with data (on top of not including fully-empty views)
        self.wind_view = View("Wind", [self._wind_panel])
        self.environment_view = View("Environment", [self._temperature_panel, self._humidity_panel, self._pressure_panel, self._sky_panel])
        #self.agricultural_view = View([])

        self._plotter = InteractivePlotter(name, [self.wind_view, self.environment_view])

    def show(self, from_reader: bool = False):
        self._plotter.show(existing_plot = from_reader)

    def _wind_panel(self, fig, ax):
        # "10m WD"
        #   "WD Standard Deviation"
        # "2m WS"
        # "20ft WS"
        #ax.errorbar(self.df.index, self.df["10m WS scalar"], self.df["WS Standard Deviation"], marker="o", markersize=1, linewidth=0, capsize=1, label="10m Wind Speed")
        ax.scatter(self.df.index, self.df["10m WS scalar"], marker="o", s=1, c="tab:blue", label="10m Wind Speed")
        # ax.scatter(self.df.index, self.df["10m WD"], marker="o", s=1, c="tab:blue", label="10m Wind Direction")
        ax.scatter(self.df.index, self.df["10m Peak Gust"], marker="o", s=1, c="tab:red", label="10m Peak Gust")
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(f"Wind Speed ({u_.WS})")

    def _temperature_panel(self, fig, ax):
        ax.scatter(self.df.index, self.df["1.5m Temp"], marker="o", s=1, label="1.5m Temperature")
        ax.scatter(self.df.index, self.df["2m Temp"], marker="o", s=1, label="2m Temperature")
        ax.scatter(self.df.index, self.df["9m Temp"], marker="o", s=1, label="9m Temperature")
        ax.scatter(self.df.index, self.df["1.5m Dewpoint"], marker="o", s=1, label="1.5m Dewpoint")
        ax.set_title("Temperature")
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(f"Temperature ({u_.T})")

    def _humidity_panel(self, fig, ax):
        ax.scatter(self.df.index, self.df["1.5m RH"], marker="o", s=1, label="1.5m Relative Humidity")
        ax.set_title("Humidity")
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(f"Relative Humidity ({u_.RH})")

    def _pressure_panel(self, fig, ax):
        ax.scatter(self.df.index, self.df["barometric pressure"], marker="o", s=1, label="Pressure")
        ax.set_title("Air Pressure")
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(f"Barometric Pressure ({u_.P})")

    def _sky_panel(self, fig, ax):
        ax2 = ax.twinx()
        ax.scatter(self.df.index, self.df["Precip"], marker="o", s=1, color="tab:blue", label="Precipitation")
        ax2.scatter(self.df.index, self.df["2m Solar Radiation"], marker="o", s=1, color="tab:red", label="Solar Radiation")
        ax.set_title("Precipitation & Solar Radiation")
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(f"Precipitation ({u_.PRECIP})")
        ax2.set_ylabel(f"Solar Irradiance ({u_.RAD})")
        return ax2

    # Additional View - Agriculture (2 panel)
        # Panel 1: Soil Temperature
            # "5cm Natural Soil Temperature"
            # "10cm Natural Soil Temperature"
            # "20cm Natural Soil Temperature"
            # "5cm Bare Soil Temperature"
            # "20cm Bare Soil Temperature"
        # Panel 2: Soil Water Content
            # "5cm Soil Water Content"
            # "20cm Soil Water Content"
            # "60cm Soil Water Content"
            # "75cm Soil Water Content"
        # "Leaf Wetness" - SKIP
