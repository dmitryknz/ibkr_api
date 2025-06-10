import pandas as pd
import json
from datetime import datetime
import os

class DataManager:
    """
    Класс для управления данными индикаторов
    """
    def __init__(self, data_dir="data"):
        """
        Инициализация менеджера данных
        
        Args:
            data_dir (str): Директория для хранения данных
        """
        self.data_dir = data_dir
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """Создает директорию для данных, если она не существует"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def save_price_data(self, symbol, prices, timestamps):
        """
        Сохраняет исторические цены
        
        Args:
            symbol (str): Тикер инструмента
            prices (list): Список цен
            timestamps (list): Список временных меток
        """
        df = pd.DataFrame({
            'timestamp': timestamps,
            'price': prices
        })
        
        filename = os.path.join(self.data_dir, f"{symbol}_prices.csv")
        df.to_csv(filename, index=False)
        
    def load_price_data(self, symbol):
        """
        Загружает исторические цены
        
        Args:
            symbol (str): Тикер инструмента
            
        Returns:
            tuple: (prices, timestamps) или (None, None) если файл не найден
        """
        filename = os.path.join(self.data_dir, f"{symbol}_prices.csv")
        if not os.path.exists(filename):
            return None, None
            
        df = pd.read_csv(filename)
        return df['price'].tolist(), df['timestamp'].tolist()
        
    def save_indicator_data(self, symbol, indicator_name, values, timestamps):
        """
        Сохраняет данные индикатора
        
        Args:
            symbol (str): Тикер инструмента
            indicator_name (str): Название индикатора
            values (list): Значения индикатора
            timestamps (list): Временные метки
        """
        df = pd.DataFrame({
            'timestamp': timestamps,
            'value': values
        })
        
        filename = os.path.join(self.data_dir, f"{symbol}_{indicator_name}.csv")
        df.to_csv(filename, index=False)
        
    def load_indicator_data(self, symbol, indicator_name):
        """
        Загружает данные индикатора
        
        Args:
            symbol (str): Тикер инструмента
            indicator_name (str): Название индикатора
            
        Returns:
            tuple: (values, timestamps) или (None, None) если файл не найден
        """
        filename = os.path.join(self.data_dir, f"{symbol}_{indicator_name}.csv")
        if not os.path.exists(filename):
            return None, None
            
        df = pd.read_csv(filename)
        return df['value'].tolist(), df['timestamp'].tolist()
        
    def save_trading_signals(self, symbol, indicator_name, signals, timestamps):
        """
        Сохраняет торговые сигналы
        
        Args:
            symbol (str): Тикер инструмента
            indicator_name (str): Название индикатора
            signals (list): Список сигналов (1: покупка, -1: продажа, 0: нет сигнала)
            timestamps (list): Временные метки
        """
        df = pd.DataFrame({
            'timestamp': timestamps,
            'signal': signals
        })
        
        filename = os.path.join(self.data_dir, f"{symbol}_{indicator_name}_signals.csv")
        df.to_csv(filename, index=False)
        
    def load_trading_signals(self, symbol, indicator_name):
        """
        Загружает торговые сигналы
        
        Args:
            symbol (str): Тикер инструмента
            indicator_name (str): Название индикатора
            
        Returns:
            tuple: (signals, timestamps) или (None, None) если файл не найден
        """
        filename = os.path.join(self.data_dir, f"{symbol}_{indicator_name}_signals.csv")
        if not os.path.exists(filename):
            return None, None
            
        df = pd.read_csv(filename)
        return df['signal'].tolist(), df['timestamp'].tolist() 