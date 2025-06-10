import numpy as np
from datetime import datetime
from .data_manager import DataManager

class McGinleyDynamic:
    """
    McGinley Dynamic Indicator Implementation
    
    The McGinley Dynamic is a modified moving average that was designed to track markets more closely
    than traditional moving averages. It was developed by John R. McGinley, a market technician.
    
    Formula:
    MD = MD[1] + (Close - MD[1]) / (N * (Close / MD[1])^4)
    
    where:
    - MD[1] is the previous McGinley Dynamic value
    - Close is the current closing price
    - N is the period (typically 14)
    """
    
    def __init__(self, period=14, symbol=None):
        """
        Initialize the McGinley Dynamic indicator
        
        Args:
            period (int): The period for the indicator (default: 14)
            symbol (str): Symbol for data storage (optional)
        """
        self.period = period
        self.symbol = symbol
        self.data_manager = DataManager()
        self.values = []
        self.timestamps = []
        
    def calculate(self, prices, timestamps=None):
        """
        Calculate the McGinley Dynamic values for the given price series
        
        Args:
            prices (list or numpy.array): Array of closing prices
            timestamps (list): Optional list of timestamps
            
        Returns:
            numpy.array: Array of McGinley Dynamic values
        """
        if len(prices) < self.period:
            raise ValueError(f"Not enough data points. Need at least {self.period} prices.")
            
        # Convert to numpy array if not already
        prices = np.array(prices)
        
        # Initialize the result array with NaN values
        md_values = np.full_like(prices, np.nan)
        
        # Calculate initial value using SMA
        md_values[self.period - 1] = np.mean(prices[:self.period])
        
        # Calculate subsequent values using the McGinley Dynamic formula
        for i in range(self.period, len(prices)):
            prev_md = md_values[i - 1]
            current_price = prices[i]
            
            # McGinley Dynamic formula
            md_values[i] = prev_md + (current_price - prev_md) / (self.period * (current_price / prev_md) ** 4)
        
        # Store values and timestamps
        self.values = md_values.tolist()
        self.timestamps = timestamps if timestamps else [datetime.now() for _ in range(len(prices))]
        
        # Save data if symbol is provided
        if self.symbol:
            self.data_manager.save_indicator_data(
                self.symbol,
                'mcgilney_dynamic',
                self.values,
                self.timestamps
            )
            
        return md_values
    
    def get_signal(self, prices, timestamps=None):
        """
        Generate trading signals based on price crossing the McGinley Dynamic line
        
        Args:
            prices (list or numpy.array): Array of closing prices
            timestamps (list): Optional list of timestamps
            
        Returns:
            numpy.array: Array of signals (1 for buy, -1 for sell, 0 for no signal)
        """
        md_values = self.calculate(prices, timestamps)
        signals = np.zeros_like(prices)
        
        # Generate signals based on price crossing the McGinley Dynamic line
        for i in range(1, len(prices)):
            if prices[i] > md_values[i] and prices[i-1] <= md_values[i-1]:
                signals[i] = 1  # Buy signal
            elif prices[i] < md_values[i] and prices[i-1] >= md_values[i-1]:
                signals[i] = -1  # Sell signal
        
        # Save signals if symbol is provided
        if self.symbol:
            self.data_manager.save_trading_signals(
                self.symbol,
                'mcgilney_dynamic',
                signals.tolist(),
                self.timestamps
            )
                
        return signals
    
    def get_last_value(self, prices):
        """
        Get the most recent McGinley Dynamic value
        
        Args:
            prices (list or numpy.array): Array of closing prices
            
        Returns:
            float: The most recent McGinley Dynamic value
        """
        md_values = self.calculate(prices)
        return md_values[-1]
        
    def load_historical_data(self):
        """
        Load historical indicator data if available
        
        Returns:
            tuple: (values, timestamps) or (None, None) if no data available
        """
        if not self.symbol:
            return None, None
            
        return self.data_manager.load_indicator_data(self.symbol, 'mcgilney_dynamic')
        
    def load_historical_signals(self):
        """
        Load historical trading signals if available
        
        Returns:
            tuple: (signals, timestamps) or (None, None) if no data available
        """
        if not self.symbol:
            return None, None
            
        return self.data_manager.load_trading_signals(self.symbol, 'mcgilney_dynamic') 