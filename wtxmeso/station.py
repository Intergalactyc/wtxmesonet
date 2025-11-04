import pandas as pd
import matplotlib.pyplot as plt
from .plot import View, InteractivePlotter

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

    def _test_plot(self, fig, ax):
        ax.scatter(self.df.index, self.df["10m WS scalar"], s=1)
        ax.set_title("Wind speed")

    def _another(self, fig, ax):
        ax.scatter(self.df.index, self.df["1.5m Temp"], s=1)

    def plot(self):
        v1 = View([self._test_plot])
        v2 = View([self._another])
        self._plotter = InteractivePlotter([v1, v2])
        self._plotter.show()
        # In each view, allow toggling different variables on/off in interactive legend
        # Views:
            # Wind
                # "10m WS scalar" [& "WS Standard Deviation" - error bar]
                # "10m WS vector" - SKIP
                # "10m WD" [& "WD Standard Deviation" - error bar]
                # "2m WS", initially disabled
                # "20ft WS", initially disabled
                # "10m Peak Gust"
                    # 10m wind speeds: display SD error bar
            # Environment (4 panel)
                # Panel 1: Temperature & Dewpoint
                # Panel 2: Relative Humidity
                # Panel 3:
                # Panel 4:
                # "1.5m Temp"
                # "9m Temp", initially disabled
                # "2m Temp", initially disabled
                # "1.5m RH"
                # "1.5m Dewpoint", initially disabled
            # Environment
                # "barometric pressure"
                # "Precip"
                # "2m Solar Radiation"
            # Agriculture (2 panel)
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
        # fig, ax = plt.subplots()
        # 
