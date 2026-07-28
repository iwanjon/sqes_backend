import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class CSVRepository:
    def __init__(self, stations_file="config/stations.csv", output_dir="files"):
        self.stations_file = stations_file
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_stations_to_process(self, tgl: str, network: list = None):
        try:
            df = pd.read_csv(self.stations_file).fillna('')
            if network:
                df = df[df['network'].isin(network)]
            
            tuples = []
            for _, row in df.iterrows():
                tuples.append((
                    row['network'], row['code'], row['location'], 
                    "CSV_SENSOR", row['channel_prefixes'], row['channel_components']
                ))
            return tuples
        except Exception as e:
            logger.error(f"Failed to read {self.stations_file}: {e}")
            return []
            
    def get_station_tuples(self, station_list: list, network: list = None):
        try:
            df = pd.read_csv(self.stations_file).fillna('')
            df = df[df['code'].isin(station_list)]
            if network:
                df = df[df['network'].isin(network)]
            
            tuples = []
            for _, row in df.iterrows():
                tuples.append((
                    row['network'], row['code'], row['location'], 
                    "CSV_SENSOR", row['channel_prefixes'], row['channel_components']
                ))
            return tuples
        except Exception as e:
            logger.error(f"Failed to read {self.stations_file}: {e}")
            return []

    def get_straggler_stations(self, tgl: str, station_list: list = None):
        return [] # Disabled in CSV mode
        
    def flush_daily_data(self, tgl: str, stations: list = None, network: list = None):
        # Safely delete daily CSVs if full flush is requested
        if not stations and not network:
            for f in [f"qc_details_{tgl}.csv", f"qc_analysis_{tgl}.csv"]:
                path = os.path.join(self.output_dir, f)
                if os.path.exists(path):
                    os.remove(path)