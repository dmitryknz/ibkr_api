import wx
import threading
import time
import pytz
from datetime import datetime
from gui.historical_data_frame import HistoricalDataFrame
from gui.price_list_ctrl import PriceListCtrl
from core.price_data_manager import PriceDataManager
from core.ib_connector import IBapi
from utils.order_log import OrderLogger
from utils.order_utils import create_unh_contract, create_limit_order
from strategies.buy_strategy import BuyDipStrategy
from strategies.sell_strategy import SellRallyStrategy

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="UNH — стратегии + лог")
        pnl = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        # Добавляем обработчик закрытия окна
        self.Bind(wx.EVT_CLOSE, self.on_close)

        title = wx.StaticText(pnl, label="UNH")
        fnt = title.GetFont()
        fnt.MakeBold()
        fnt.PointSize += 6
        title.SetFont(fnt)
        main.Add(title, 0, wx.TOP | wx.CENTER, 10)

        # Порт подключения
        port_row = wx.BoxSizer(wx.HORIZONTAL)
        port_label = wx.StaticText(pnl, label="Порт:")
        self.port_input = wx.TextCtrl(pnl, value="7496", size=(70, -1))
        port_row.Add(port_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        port_row.Add(self.port_input, 0, wx.ALL, 5)
        main.Add(port_row, 0, wx.CENTER)

        row1 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_connect = wx.Button(pnl, label="Подключиться и подписаться")
        self.price_lbl = wx.StaticText(pnl, label="Цена: -")
        row1.Add(self.btn_connect, 0, wx.ALL | wx.CENTER, 5)
        row1.Add(self.price_lbl, 0, wx.ALL | wx.CENTER, 5)
        main.Add(row1, 0, wx.CENTER)

        # Добавляем кнопку для открытия исторических данных
        self.btn_historical = wx.Button(pnl, label="Исторические данные")
        self.btn_historical.Bind(wx.EVT_BUTTON, self.show_historical_data)
        main.Add(self.btn_historical, 0, wx.ALL | wx.CENTER, 5)

        qty_row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_qty = wx.Button(pnl, label="Стандартный размер заявки")
        self.qty_in = wx.TextCtrl(pnl, value="1", size=(60, -1))
        qty_row.Add(self.btn_qty, 0, wx.ALL, 5)
        qty_row.Add(self.qty_in, 0, wx.ALL, 5)
        main.Add(qty_row, 0, wx.CENTER)

        row_buy = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_set_diff_buy = wx.Button(pnl, label="Задать Δ (Buy)")
        self.diff_buy_in = wx.TextCtrl(pnl, value="0.1", size=(60, -1))
        self.diff_buy_lbl = wx.StaticText(pnl, label="Buy-Δ = 0.1")
        row_buy.Add(self.btn_set_diff_buy, 0, wx.ALL, 5)
        row_buy.Add(self.diff_buy_in, 0, wx.ALL, 5)
        row_buy.Add(self.diff_buy_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        main.Add(row_buy, 0, wx.CENTER)

        row_sell = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_set_diff_sell = wx.Button(pnl, label="Задать Δ (Sell)")
        self.diff_sell_in = wx.TextCtrl(pnl, value="0.1", size=(60, -1))
        self.diff_sell_lbl = wx.StaticText(pnl, label="Sell-Δ = 0.1")
        row_sell.Add(self.btn_set_diff_sell, 0, wx.ALL, 5)
        row_sell.Add(self.diff_sell_in, 0, wx.ALL, 5)
        row_sell.Add(self.diff_sell_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        main.Add(row_sell, 0, wx.CENTER)

        trade = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_buy = wx.Button(pnl, label="Купить UNH", size=(180, 60))
        self.btn_buy.SetBackgroundColour(wx.Colour(0, 200, 0))
        self.btn_sell = wx.Button(pnl, label="Продать UNH", size=(180, 60))
        self.btn_sell.SetBackgroundColour(wx.Colour(200, 0, 0))
        trade.Add(self.btn_buy, 0, wx.ALL, 10)
        trade.AddStretchSpacer()
        trade.Add(self.btn_sell, 0, wx.ALL, 10)
        main.Add(trade, 0, wx.EXPAND)

        self.btn_cancel_all = wx.Button(pnl, label="Отменить все заявки")
        main.Add(self.btn_cancel_all, 0, wx.ALL | wx.CENTER, 10)

        # Добавляем кнопку остановки всех стратегий
        self.btn_stop_all = wx.Button(pnl, label="Остановить все стратегии")
        self.btn_stop_all.SetBackgroundColour(wx.Colour(200, 200, 0))  # Желтый цвет
        main.Add(self.btn_stop_all, 0, wx.ALL | wx.CENTER, 10)

        self.logger = OrderLogger(pnl)
        main.Add(self.logger.get_ctrl(), 1, wx.EXPAND | wx.ALL, 10)

        pnl.SetSizer(main)

        self.ib = IBapi(self)
        self.default_qty = 1
        self.diff_buy = 1.0
        self.diff_sell = 0.1
        self.pending_market_action = None
        self.awaiting_market = False
        self.last_price = None
        self.strategy_buy = None
        self.strategy_sell = None
        
        # Инициализируем менеджер данных
        self.data_manager = PriceDataManager()
        
        # Запускаем обновление списков цен
        self.update_price_lists()
        self.price_update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_price_lists, self.price_update_timer)
        self.price_update_timer.Start(1000)  # Обновление каждую секунду

        self.btn_connect.Bind(wx.EVT_BUTTON, self.subscribe_price)
        self.btn_qty.Bind(wx.EVT_BUTTON, self.set_qty)
        self.btn_set_diff_buy.Bind(wx.EVT_BUTTON, self.set_diff_buy)
        self.btn_set_diff_sell.Bind(wx.EVT_BUTTON, self.set_diff_sell)
        self.btn_buy.Bind(wx.EVT_BUTTON, self.run_buy_strategy)
        self.btn_sell.Bind(wx.EVT_BUTTON, self.run_sell_strategy)
        self.btn_cancel_all.Bind(wx.EVT_BUTTON, self.cancel_all_orders)
        self.btn_stop_all.Bind(wx.EVT_BUTTON, self.stop_all_strategies)
        self.btn_historical.Bind(wx.EVT_BUTTON, self.show_historical_data)

        self.Show()

    def connect_ib(self):
        if not self.ib.isConnected():
            try:
                port = int(self.port_input.GetValue())
            except ValueError:
                self.show_message("Некорректный порт. Введите число.")
                return
            self.ib.connect("127.0.0.1", port, clientId=20)
            threading.Thread(target=self.ib.run, daemon=True).start()
            time.sleep(1)

    def subscribe_price(self, event):
        try:
            port = int(self.port_input.GetValue())
            self.ib.connect("127.0.0.1", port, 0)
            self.ib.contract = create_unh_contract()
            
            # Запускаем поток для получения данных
            api_thread = threading.Thread(target=self.ib.run, daemon=True)
            api_thread.start()
            
            # Ждем подключения
            time.sleep(1)
            
            # Подписываемся на текущие цены
            self.ib.reqMktData(1, self.ib.contract, "", False, False, [])
            
            # Запрашиваем исторические данные
            # Используем текущее время в US/Eastern
            eastern_tz = pytz.timezone('US/Eastern')
            end_time = datetime.now(eastern_tz).strftime('%Y%m%d %H:%M:%S US/Eastern')
            duration = "1 D"  # Получаем данные за последний день
            
            # Запрашиваем минутные данные
            self.ib.reqHistoricalData(
                reqId=1,
                contract=self.ib.contract,
                endDateTime=end_time,
                durationStr=duration,
                barSizeSetting="1 min",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            
            # Запрашиваем пятиминутные данные
            self.ib.reqHistoricalData(
                reqId=2,
                contract=self.ib.contract,
                endDateTime=end_time,
                durationStr=duration,
                barSizeSetting="5 mins",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            
            # Запускаем таймер для периодического обновления данных
            self.update_timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.update_historical_data, self.update_timer)
            self.update_timer.Start(60000)  # Обновляем каждую минуту
            
        except Exception as e:
            print(f"Ошибка при подключении: {e}")
            self.btn_connect.Enable(True)

    def update_historical_data(self, event):
        """Периодическое обновление исторических данных"""
        try:
            # Используем текущее время в US/Eastern
            eastern_tz = pytz.timezone('US/Eastern')
            end_time = datetime.now(eastern_tz).strftime('%Y%m%d %H:%M:%S US/Eastern')
            
            # Запрашиваем минутные данные
            self.ib.reqHistoricalData(
                reqId=1,
                contract=self.ib.contract,
                endDateTime=end_time,
                durationStr="1 D",
                barSizeSetting="1 min",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            
            # Запрашиваем пятиминутные данные
            self.ib.reqHistoricalData(
                reqId=2,
                contract=self.ib.contract,
                endDateTime=end_time,
                durationStr="1 D",
                barSizeSetting="5 mins",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
        except Exception as e:
            print(f"Ошибка при обновлении исторических данных: {e}")

    def set_qty(self, _):
        try:
            q = int(self.qty_in.GetValue())
            if q <= 0:
                raise ValueError
            self.default_qty = q
            self.show_message(f"Размер заявки = {q}")
        except ValueError:
            self.show_message("Введите положительное целое")

    def set_diff_buy(self, _):
        self._set_diff(self.diff_buy_in, "buy")

    def set_diff_sell(self, _):
        self._set_diff(self.diff_sell_in, "sell")

    def _set_diff(self, ctrl, which):
        try:
            d = float(ctrl.GetValue())
            if d <= 0:
                raise ValueError
            if which == "buy":
                self.diff_buy = d
                self.diff_buy_lbl.SetLabel(f"Buy-Δ = {d}")
            else:
                self.diff_sell = d
                self.diff_sell_lbl.SetLabel(f"Sell-Δ = {d}")
            self.show_message(f"{which.capitalize()}-Δ установлена: {d}")
        except ValueError:
            self.show_message("Введите положительное число")

    def prepare_market_order(self, action):
        self.connect_ib()
        self.pending_market_action = action
        self.awaiting_market = True
        self.ib.reqIds(1)

    def place_pending_market(self, order_id):
        if not self.awaiting_market:
            return
        order = create_limit_order(self.pending_market_action, self.default_qty)
        self.ib.placeOrder(order_id, create_unh_contract(), order)
        self.awaiting_market = False

    def run_buy_strategy(self, _):
        if self.strategy_buy is not None:
            wx.MessageBox("Стратегия покупки уже запущена", "Предупреждение", wx.OK | wx.ICON_WARNING)
            return

        if self.last_price is None:
            wx.MessageBox("Нет данных о текущей цене", "Ошибка", wx.OK | wx.ICON_ERROR)
            return

        # Создаем диалог с полем ввода цены
        dlg = wx.Dialog(self, title="Подтверждение запуска стратегии покупки", size=(500, 400))
        panel = wx.Panel(dlg)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Информация о текущих параметрах
        info_text = f"Текущая цена: {self.last_price:.2f}\nРазмер позиции: {self.default_qty}\nДельта: {self.diff_buy}"
        info = wx.StaticText(panel, label=info_text)
        info.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        main_sizer.Add(info, 0, wx.ALL | wx.EXPAND, 20)

        # Поле для ввода стартовой цены
        price_sizer = wx.BoxSizer(wx.VERTICAL)
        price_label = wx.StaticText(panel, label="Стартовая цена (оставьте пустым для немедленного запуска):")
        price_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.start_price_input = wx.TextCtrl(panel, size=(200, 30))
        self.start_price_input.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        price_sizer.Add(price_label, 0, wx.ALL, 5)
        price_sizer.Add(self.start_price_input, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(price_sizer, 0, wx.EXPAND | wx.ALL, 20)

        # Добавляем отступ
        main_sizer.AddSpacer(20)

        # Кнопки
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Запустить", size=(150, 50))
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Отмена", size=(150, 50))
        
        # Настраиваем внешний вид кнопок
        ok_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        cancel_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Устанавливаем цвета кнопок
        ok_btn.SetBackgroundColour(wx.Colour(0, 200, 0))  # Зеленый
        ok_btn.SetForegroundColour(wx.WHITE)
        cancel_btn.SetBackgroundColour(wx.Colour(200, 0, 0))  # Красный
        cancel_btn.SetForegroundColour(wx.WHITE)
        
        btn_sizer.Add(ok_btn, 0, wx.ALL, 10)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 20)

        panel.SetSizer(main_sizer)
        dlg.SetMinSize((500, 400))
        dlg.Centre()

        if dlg.ShowModal() == wx.ID_OK:
            start_price = None
            price_text = self.start_price_input.GetValue().strip()
            if price_text:
                try:
                    start_price = float(price_text)
                    if start_price <= 0:
                        raise ValueError
                except ValueError:
                    wx.MessageBox("Введите корректную цену", "Ошибка", wx.OK | wx.ICON_ERROR)
                    dlg.Destroy()
                    return

            self.strategy_buy = BuyDipStrategy(
                self.ib,
                create_unh_contract(),
                self.default_qty,
                self.diff_buy,
                self,
                start_price=start_price
            )
            self.btn_buy.SetBackgroundColour(wx.Colour(0, 150, 0))
            self.show_message("Стратегия покупки запущена")
        dlg.Destroy()

    def run_sell_strategy(self, _):
        if self.strategy_sell is not None:
            wx.MessageBox("Стратегия продажи уже запущена", "Предупреждение", wx.OK | wx.ICON_WARNING)
            return

        if self.last_price is None:
            wx.MessageBox("Нет данных о текущей цене", "Ошибка", wx.OK | wx.ICON_ERROR)
            return

        # Создаем диалог с полем ввода цены
        dlg = wx.Dialog(self, title="Подтверждение запуска стратегии продажи", size=(500, 400))
        panel = wx.Panel(dlg)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Информация о текущих параметрах
        info_text = f"Текущая цена: {self.last_price:.2f}\nРазмер позиции: {self.default_qty}\nДельта: {self.diff_sell}"
        info = wx.StaticText(panel, label=info_text)
        info.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        main_sizer.Add(info, 0, wx.ALL | wx.EXPAND, 20)

        # Поле для ввода стартовой цены
        price_sizer = wx.BoxSizer(wx.VERTICAL)
        price_label = wx.StaticText(panel, label="Стартовая цена (оставьте пустым для немедленного запуска):")
        price_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.start_price_input = wx.TextCtrl(panel, size=(200, 30))
        self.start_price_input.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        price_sizer.Add(price_label, 0, wx.ALL, 5)
        price_sizer.Add(self.start_price_input, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(price_sizer, 0, wx.EXPAND | wx.ALL, 20)

        # Добавляем отступ
        main_sizer.AddSpacer(20)

        # Кнопки
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Запустить", size=(150, 50))
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Отмена", size=(150, 50))
        
        # Настраиваем внешний вид кнопок
        ok_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        cancel_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Устанавливаем цвета кнопок
        ok_btn.SetBackgroundColour(wx.Colour(0, 200, 0))  # Зеленый
        ok_btn.SetForegroundColour(wx.WHITE)
        cancel_btn.SetBackgroundColour(wx.Colour(200, 0, 0))  # Красный
        cancel_btn.SetForegroundColour(wx.WHITE)
        
        btn_sizer.Add(ok_btn, 0, wx.ALL, 10)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 20)

        panel.SetSizer(main_sizer)
        dlg.SetMinSize((500, 400))
        dlg.Centre()

        if dlg.ShowModal() == wx.ID_OK:
            start_price = None
            price_text = self.start_price_input.GetValue().strip()
            if price_text:
                try:
                    start_price = float(price_text)
                    if start_price <= 0:
                        raise ValueError
                except ValueError:
                    wx.MessageBox("Введите корректную цену", "Ошибка", wx.OK | wx.ICON_ERROR)
                    dlg.Destroy()
                    return

            self.strategy_sell = SellRallyStrategy(
                self.ib,
                create_unh_contract(),
                self.default_qty,
                self.diff_sell,
                self,
                start_price=start_price
            )
            self.btn_sell.SetBackgroundColour(wx.Colour(150, 0, 0))
            self.show_message("Стратегия продажи запущена")
        dlg.Destroy()

    def stop_all_strategies(self, _):
        """Останавливает все запущенные стратегии"""
        stopped = False
        
        # Останавливаем стратегию покупки
        if self.strategy_buy is not None:
            self.strategy_buy.active = False
            self.strategy_buy = None
            self.btn_buy.SetBackgroundColour(wx.Colour(0, 200, 0))
            stopped = True
            
        # Останавливаем стратегию продажи
        if self.strategy_sell is not None:
            self.strategy_sell.active = False
            self.strategy_sell = None
            self.btn_sell.SetBackgroundColour(wx.Colour(200, 0, 0))
            stopped = True

        if stopped:
            self.show_message("Все стратегии остановлены")
        else:
            wx.MessageBox("Нет запущенных стратегий", "Информация", wx.OK | wx.ICON_INFORMATION)

    def cancel_all_orders(self, _):
        """Отменяет все активные ордера"""
        if not self.ib.isConnected():
            wx.MessageBox("Нет подключения к Interactive Brokers", "Ошибка", wx.OK | wx.ICON_ERROR)
            return

        self.show_message("Функция отмены всех ордеров отключена")

    def update_price(self, p):
        """Обновление текущей цены и сохранение в базу данных"""
        self.price_lbl.SetLabel(f"Цена: {p:.2f}")
        self.last_price = p
        
        # Сохраняем минутные данные
        current_time = datetime.now()
        self.data_manager.save_minute_data("UNH", [(
            current_time,
            p,  # open
            p,  # high
            p,  # low
            p,  # close
            0   # volume (недоступно в реальном времени)
        )])
        
        # Агрегируем в пятиминутные данные
        self.data_manager.aggregate_to_five_minutes("UNH")
        
        # Обновляем данные в окне исторических данных, если оно открыто
        if hasattr(self, 'historical_frame') and self.historical_frame:
            self.historical_frame.update_data()

    def show_message(self, txt):
        wx.MessageBox(txt, "Информация")

    def on_close(self, event):
        """Обработчик закрытия окна"""
        if hasattr(self, 'update_timer'):
            self.update_timer.Stop()
        if hasattr(self, 'price_update_timer'):
            self.price_update_timer.Stop()
        if hasattr(self, 'historical_frame') and self.historical_frame is not None:
            self.historical_frame.Destroy()
        if self.ib.isConnected():
            self.ib.disconnect()
        event.Skip()

    def update_price_lists(self, event=None):
        """Обновление списков последних цен"""
        try:
            # Обновляем данные в окне исторических данных, если оно открыто
            if hasattr(self, 'historical_frame') and self.historical_frame:
                self.historical_frame.update_data()
        except Exception as e:
            print(f"Ошибка при обновлении данных: {e}")

    def show_historical_data(self, event):
        """Открытие окна с историческими данными"""
        if not hasattr(self, 'historical_frame') or not self.historical_frame:
            self.historical_frame = HistoricalDataFrame(self, self.data_manager)
        else:
            self.historical_frame.Raise()
            self.historical_frame.update_data() 