from .station import Station
import os
import pathlib
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np

_HEADER = pd.read_csv(pathlib.Path(__file__).parent.joinpath("data").joinpath("header.csv"), index_col="ID")
_all_columns = list(_HEADER["Column"])
_atmo_columns = list(_HEADER.loc[_HEADER["Inclusion"].isin({"all", "atmospheric"}), "Column"])
_agri_columns = list(_HEADER.loc[_HEADER["Inclusion"].isin({"all", "agricultural"}), "Column"])

class Reader:
    def __init__(self, station_file: os.PathLike, columns: str|list=None, *args, **kwargs):
        self._columns = _all_columns
        if isinstance(columns, str):
            match columns.lower():
                case "all":
                    self._columns = _all_columns
                case "atmospheric":
                    self._columns = _atmo_columns
                case "agricultural":
                    self._columns = _agri_columns
                case _:
                    raise ValueError(f"Invalid selection columns={columns}")
        elif isinstance(columns, list):
            if isinstance(columns[0], int):
                self._columns = [_HEADER.iloc(c) for c in columns]
            else:
                self._columns = columns

        self.units = {c : r.Units for r in _HEADER.itertuples() if (c := r.Column) in self._columns and c not in {"UTC Date", "UTC Time", "Station ID"}}

        self.stations = list()
        self.stations_map = dict()
        
        self._read_stations(station_file, *args, **kwargs)

    def _read_stations(self, path: os.PathLike, *args, **kwargs):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File {path} not found")
        df = pd.read_excel(path, *args, **kwargs)
        df.apply(self._load_station, axis = 1)

    def _load_station(self, s: pd.Series):
        # It is currently unclear whether the typos (e.g. "Prevouis IDs") are internal to the database or only incident to the data I was given
        area = s["Area"].split("/")
        if len(area) == 2:
            _city = area[0].strip()
            _county = area[1].strip()
        elif len(area) == 1:
            _city = "None"
            _county = " ".join(area[0].strip().split(" ")[1:]) # convert e.g. "Southeast Cochran County" to just "Cochran County"
        else:
            _city = "Unknown"
            _county = "Unknown"
        _state = "TX" if _county != "Unknown" else "Unknown" # Default state is TX (might not handle no-city areas right?)
        if _city[-3] == " " and (st:=_city[-2:]).isupper(): # Handle both "City, ST" and "City ST" formats
            _state = st
            _city = _city[:-3].split(",")[0]

        _relocations = []
        if not pd.isna(s["Prevoius IDs"]):
            for ident, lat, lon, d in zip(str(s["Prevoius IDs"]).split("//"), str(s["Prev. Lat-decimals"]).split("//"), str(s["Prev. Lon-decimals"]).split("//"), str(s["Dates of Relocation (UTC YYYYMMDD)"]).split("//")):
                _relocations.append((ident, float(lat), float(lon), date.fromisoformat(d))) # date is UTC
                
        station = Station(
            name = s["Location"],
            city = _city,
            county = _county,
            state = _state,
            latitude = float(s["Lat-decimal"]),
            longitude = float(s["Long.-decimal"]),
            elevation = float(s["Elevation"][:-4]),
            identifier = s["ID"],
            logger_id = int(s["Logger ID"]),
            relocations = _relocations
        )
        self.stations.append(station)
        self.stations_map[station.id] = station
        return

    def _qc(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Precip" in df.columns:
            df.loc[df["Precip"] > 1.5, "Precip"] = np.nan # World record rainfall in 1 minute is 1.23 in. - discard rainfall measurements > 1.5 in.
        return df

    def load_file(self, path: os.PathLike, name: str = None, *, _tup: bool = False) -> pd.DataFrame:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File {path} not found")

        df = pd.read_csv(path, header=None, names=self._columns)
        df["Timestamp"] = df.apply(lambda row : f"{int(row['UTC Date'])}T{str(int(row['UTC Time'])).zfill(4)}", axis=1)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.tz_localize("UTC")
        df.set_index("Timestamp", drop=True, inplace=True)
        df.drop(columns=["UTC Date", "UTC Time", "Station ID"], inplace=True)

        if name is None: # default is to infer name (station ID) from filename
            name = "".join(os.path.basename(path).split(".")[:-1])

        df = self._qc(df)

        self.stations_map[name].add_data(df)

        if _tup:
            return df, name

        return df

    def read_directory(self, path: os.PathLike) -> dict[str, pd.DataFrame]:
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Directory {path} not found")
        result = dict()
        for f in os.listdir(path):
            df, name = self.load_file(os.path.join(path, f), _tup=True)
            result[name] = df
        return result

    def plot(self, figsize=(11.,6.5), padding=0.5):
        station_longitudes = [s.longitude for s in self.stations]
        station_latitudes = [s.latitude for s in self.stations]
        station_names = [s.name for s in self.stations]
        station_position_map = {(lon, lat) : s for lon, lat, s in zip(station_longitudes, station_latitudes, self.stations)}

        fig, ax = plt.subplots(figsize=figsize)

        m = Basemap(
            llcrnrlon = min(station_longitudes)-padding,
            urcrnrlon = max(station_longitudes)+padding,
            llcrnrlat = min(station_latitudes)-padding,
            urcrnrlat = max(station_latitudes)+padding,
            resolution="l",
            ax=ax
        )
        m.drawcoastlines()
        m.drawcounties()
        m.drawstates()
        m.drawcountries()
        m.drawrivers(linewidth=0.2, color="tab:blue")

        sc = m.scatter(station_longitudes, station_latitudes, 10, marker="o", color="tab:red", picker=True)

        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->"),
        )
        annot.set_visible(False)

        def on_pick(event):
            artist = event.artist
            ind = event.ind[0]
            offsets = artist.get_offsets()
            x, y = offsets[ind]
            if (pos:=(x, y)) in station_position_map:
                s = station_position_map[pos]
                s.plot(True)
            else:
                print(pos, "not found")

        def update_annot(ind):
            i = ind["ind"][0]
            x, y = sc.get_offsets()[i]
            annot.xy = (x, y)
            annot.set_text(station_names[i])
            annot.get_bbox_patch().set_alpha(0.8)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                cont, ind = sc.contains(event)
                if cont:
                    update_annot(ind)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                elif vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)
        fig.canvas.callbacks.connect('pick_event', on_pick)

        plt.show()
