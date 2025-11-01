import pandas as pd

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
