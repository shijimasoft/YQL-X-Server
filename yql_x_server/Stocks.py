import yfinance, datetime
from urllib.parse import unquote

# Cache responses per hour so we don't abuse the API and also for performance reasons.
cachedResponses = {}
cachedChartResponses = {}

def getTickerInfo(ticker):
    if ticker in cachedResponses and cachedResponses[ticker]['timestamp'] == datetime.datetime.now().strftime("%h"):
        print(f"Returning cached response for ticker {ticker}")
        return cachedResponses[ticker]
    print(f"Getting real response for ticker {ticker}")
    return getTickerInfoReal(ticker)

def getTickerInfoReal(tickerName):
    ticker = yfinance.Ticker(tickerName)
    changes = getTickerChanges(ticker)
    info = ticker.info
    if not info:
        return None
    info.update(changes)
    info.update({"timestamp": datetime.datetime.now().strftime("%h")})
    info["noopen"] = False
    if "open" not in info:
        if 'regularMarketOpen' not in info:
            info["noopen"] = True
        else:
            info['open'] = info['regularMarketOpen']
    if "volume" not in info:
        info["volume"] = 0
    if "marketCap" not in info:
        info["marketCap"] = 0
    if "dividendYield" not in info:
        info["dividendYield"] = 0
    info["sanitizedSymbol"] = sanitizeSymbol(tickerName)
    if ticker not in cachedResponses:
        cachedResponses.update({tickerName: info})
    else:
        cachedResponses[ticker] = {tickerName: info}
    return info

def getTickerChanges(ticker):
    try:
        # Check if 'regularMarketPreviousClose' and 'regularMarketPrice' are available
        if 'previousClose' in ticker.info and 'currentPrice' in ticker.info:
            previous_close = ticker.info['previousClose']
            current_price = ticker.info['currentPrice']

            # Calculate the change and change percent
            change = abs(round(previous_close - current_price, 2))
            change_percent = calculateChange(previous_close, current_price)
            print(f"Change: {change}, Change Percent: {change_percent}")
            return {"change": change, "changepercent": change_percent}
        else:
            # Data not available, return default values
            return {"change": 0, "changepercent": "0%"}
    except Exception as e:
        print(e)
        return {"change": 0, "changepercent": "0%"}

def calculateChange(current, previous):
    sign = "+"

    if current == previous:
        return "0%"
    elif current < previous:
        sign = "-"
    try:
        return sign + format((abs(current - previous) / previous) * 100.0, '.2f') + "%"
    except ZeroDivisionError:
        return "x%"

def sanitizeSymbol(s):
    return unquote(s)

def getTickerChartForRange(ticker, range):
    # Generate a cache key based on ticker and range
    cache_key = f"{ticker}_{range}"

    # Check if the data is cached and still valid
    if cache_key in cachedChartResponses and cachedChartResponses[cache_key]['timestamp'] == datetime.datetime.now().strftime("%h"):
        print(f"Returning cached response for {ticker} - {range}")
        return cachedChartResponses[cache_key]['data']

    # If not cached or cache has expired, fetch the data
    if range == "1d":
        interval = "15m"
    elif range == "5d":
        interval = "1d"
    elif range == "1m":
        range = "1mo"
        interval = "1h"
    elif range == "3m":
        range = "3mo"
        interval = "1d"
    elif range == "6m":
        range = "6mo"
        interval = "1wk"
    elif range == "1y":
        interval = "1wk"
    elif range == "2y":
        interval = "1wk"
    else:
        print(f"Unknown range: {range}")
        return None

    print("Interval = " + interval + " for range " + range)
    data_dict = yfinance.Ticker(ticker).history(period=range, interval=interval).to_dict()

    # Create the output data
    out = [{"open": data_dict["Open"][key], "high": data_dict["High"][key], "low": data_dict["Low"][key],
            "close": data_dict["Close"][key], "volume": data_dict["Volume"][key], "timestamp": key.timestamp()} for key
           in data_dict["Open"].keys()]

    # Update the cache with the new data
    cachedChartResponses[cache_key] = {'data': out, 'timestamp': datetime.datetime.now().strftime("%h")}

    return out

class Symbol:
    def __init__(self, symbol):
        self.name = symbol["sanitizedSymbol"]
        self.incomplete = False
        if symbol['noopen']:
            self.incomplete = True
        
        if not self.incomplete:
            if len(symbol['longName']) > 12:
                self.name_short = symbol['longName'][:12] + '...'
            else:
                self.name_short = symbol['longName']
            self.price = symbol['regularMarketOpen']
            self.market_cap = symbol['marketCap']
            self.volume = symbol['volume']
            self.dividend_yield = symbol['dividendYield']
            self.open = symbol['open']
            self.previous_close = symbol['previousClose']
            self.change = symbol['changepercent']
            self.change_percent = symbol['changepercent']
            self.real_time_change = symbol['changepercent']
            self.high = symbol['regularMarketDayHigh']
            self.low = symbol['regularMarketDayLow']
            self.average_volume = symbol['averageVolume']
            self.peratio = symbol['trailingPegRatio']
            self.yearrange = 0
