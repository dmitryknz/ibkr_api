import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sqlite3
from typing import List, Tuple, Optional

class PriceDataManager:
    """
    Класс для управления данными цен с разными таймфреймами
    """
    def __init__(self, db_path: str = "data/price_data.db"):
        """
        Инициализация менеджера данных
        
        Args:
            db_path (str): Путь к файлу базы данных
        """
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Инициализация базы данных"""
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Подключаемся к базе данных
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу для минутных данных
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS minute_data (
            symbol TEXT,
            timestamp DATETIME,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (symbol, timestamp)
        )
        ''')
        
        # Создаем таблицу для пятиминутных данных
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS five_minute_data (
            symbol TEXT,
            timestamp DATETIME,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (symbol, timestamp)
        )
        ''')
        
        # Создаем индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_minute_symbol ON minute_data(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_minute_timestamp ON minute_data(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_five_minute_symbol ON five_minute_data(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_five_minute_timestamp ON five_minute_data(timestamp)')
        
        conn.commit()
        conn.close()
        
    def save_minute_data(self, symbol: str, data: List[Tuple[datetime, float, float, float, float, int]]):
        """
        Сохранение минутных данных
        
        Args:
            symbol (str): Тикер инструмента
            data (List[Tuple]): Список кортежей (timestamp, open, high, low, close, volume)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Подготавливаем данные для вставки
            values = []
            for ts, o, h, l, c, v in data:
                # Ensure timestamp is in proper format
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                values.append((symbol, ts.isoformat(), o, h, l, c, v))
            
            # Вставляем данные
            cursor.executemany('''
            INSERT OR REPLACE INTO minute_data (symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', values)
            
            conn.commit()
            print(f"Saved {len(values)} minute bars for {symbol}")
            
        except Exception as e:
            print(f"Error saving minute data: {e}")
            raise
        finally:
            conn.close()
        
    def save_five_minute_data(self, symbol: str, data: List[Tuple[datetime, float, float, float, float, int]]):
        """
        Сохранение пятиминутных данных
        
        Args:
            symbol (str): Тикер инструмента
            data (List[Tuple]): Список кортежей (timestamp, open, high, low, close, volume)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Подготавливаем данные для вставки
        values = [(symbol, ts, o, h, l, c, v) for ts, o, h, l, c, v in data]
        
        # Вставляем данные
        cursor.executemany('''
        INSERT OR REPLACE INTO five_minute_data (symbol, timestamp, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', values)
        
        conn.commit()
        conn.close()
        
    def get_minute_data(self, symbol: str, start_time: Optional[datetime] = None, 
                       end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Получение минутных данных
        
        Args:
            symbol (str): Тикер инструмента
            start_time (datetime): Начальное время
            end_time (datetime): Конечное время
            
        Returns:
            pd.DataFrame: DataFrame с данными
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM minute_data WHERE symbol = ?"
            params = [symbol]
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
                
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                # Convert timestamp strings to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                print(f"Retrieved {len(df)} minute bars for {symbol}")
            else:
                print(f"No minute data found for {symbol}")
            
            return df
            
        except Exception as e:
            print(f"Error retrieving minute data: {e}")
            raise
        finally:
            conn.close()
        
    def get_five_minute_data(self, symbol: str, start_time: Optional[datetime] = None, 
                            end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Получение пятиминутных данных
        
        Args:
            symbol (str): Тикер инструмента
            start_time (datetime): Начальное время
            end_time (datetime): Конечное время
            
        Returns:
            pd.DataFrame: DataFrame с данными
        """
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM five_minute_data WHERE symbol = ?"
        params = [symbol]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
            
        query += " ORDER BY timestamp"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
        
    def aggregate_to_five_minutes(self, symbol):
        """Агрегирует минутные данные в пятиминутные"""
        try:
            # Получаем минутные данные
            df = self.get_minute_data(symbol)
            if df is None or df.empty:
                return
            
            # Универсальное приведение timestamp к datetime
            ts = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce', utc=True)
            if ts.isnull().any():
                # Пробуем еще раз без параметров для оставшихся NaT
                ts2 = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
                ts = ts.combine_first(ts2)
            df['timestamp'] = ts
            
            # Округляем время до 5 минут
            df['timestamp'] = df['timestamp'].dt.floor('5min')
            
            # Группируем по 5-минутным интервалам
            grouped = df.groupby('timestamp').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).reset_index()
            
            # Сохраняем агрегированные данные, преобразуя timestamp к строке
            self.save_five_minute_data(symbol, [
                (row['timestamp'].isoformat(), row['open'], row['high'], row['low'], row['close'], row['volume'])
                for _, row in grouped.iterrows()
            ])
            
        except Exception as e:
            print(f"Ошибка при агрегации данных: {e}")
            print(f"Тип timestamp: {type(df['timestamp'].iloc[0]) if not df.empty else 'empty'}")
            if not df.empty:
                print(f"Пример timestamp: {df['timestamp'].iloc[0]}")
        
    def get_latest_data(self, symbol: str, timeframe: str = 'minute') -> pd.DataFrame:
        """
        Получение последних данных
        
        Args:
            symbol (str): Тикер инструмента
            timeframe (str): Таймфрейм ('minute' или 'five_minute')
            
        Returns:
            pd.DataFrame: DataFrame с последними данными
        """
        table = 'minute_data' if timeframe == 'minute' else 'five_minute_data'
        
        conn = sqlite3.connect(self.db_path)
        query = f"""
        SELECT * FROM {table}
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        df = pd.read_sql_query(query, conn, params=[symbol])
        conn.close()
        
        return df
        
    def clear_minute_data(self, symbol: str):
        """
        Удаляет все минутные данные для указанного символа
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM minute_data WHERE symbol = ?", (symbol,))
        conn.commit()
        conn.close() 