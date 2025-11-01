from .station import Station
import os
import pathlib
import pandas as pd
from datetime import date, datetime

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
        # else:
        #     print(_city, _county[-3], _county[-2:])
        _relocations = []
        if not pd.isna(s["Prevoius IDs"]):
            for ident, lat, lon, d in zip(s["Prevoius IDs"].split("//"), s["Prev. Lat-decimals"].split("//"), s["Prev. Lon-decimals"].split("//"), s["Dates of Relocation (UTC YYYYMMDD)"].split("//")):
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
