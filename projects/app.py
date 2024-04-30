from flask import Flask, render_template, request, jsonify, Response
import yfinance as yf
import time
import requests
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Flask is used to connect the backend Python code and the frontend HTML page
# yfinance library is used to get live stock prices and price history for analysis
# Time is used for updating live prices and other time-related operations
# Requests is used for sending HTTP requests to external APIs like Google and News API
# BeautifulSoup is used for web scraping, particularly for extracting data from HTML
# Matplotlib is used for generating graphs and charts for stock analysis

app = Flask(__name__)

portfolio = {}  # Dictionary to store user's portfolio
venkat = {}  # Dictionary to store purchased prices of stocks
balance = 100000  # Initial balance for the user



# The chatbot_response function generates a response for the user's input by performing a Google search
# The get_news function fetches the latest business news from News API
# The display_portfolio function generates a summary of the user's portfolio including current values and profit/loss
# The generate_portfolio_pie_chart function creates a pie chart to visualize portfolio performance
# The buy_stock and sell_stock functions handle buying and selling of stocks respectively

def yahoo_search(query):
    try:
        url = f"https://search.yahoo.com/search?p={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers) #It is used to send request to theat url to get the data fro that website
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
         # Find the relevant HTML elements containing the answers
        # Adjust this part according to the structure of the website
        results = soup.find_all('div', class_='algo-sr')       #We get this class after inspecting the yahoo finance page
        return results[0].get_text() if results else "No results found"
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"     #we used try and except for error handling because in this big code we are able to see where the error happening



def get_news():
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "in",
        "category": "business",
        "apiKey": "361ff1f4a3384138b173d1e5d7df3bca'"
    } #Created a api key in the news api and added to here to get the live top news 
    # The category is specified before only to business and country set to india it always shows the top and live business news of india
    response = requests.get(url, params=params)
    data = response.json()
    articles = data.get("articles", [])
    return articles

def display_portfolio(portfolio, balance):
    portfolio_info = ""
    total_investment = 0
    current_portfolio_value = 0
    for symbol, shares in portfolio.items():
        stock = yf.Ticker(symbol + ".NS")
        current_price = stock.history(period="1d")["Close"].iloc[-1]         #The only only new thing in this function is getting the price of stock 
        current_value = current_price * shares          #Then everything is basic logic finding percentage and total investment using python
        purchased_value = venkat[symbol] * shares
        total_investment += venkat[symbol] * shares  #Total investment profit loss is calculated in the same fashion how real stock market apps calculates them
        current_portfolio_value += current_value
        profit_loss_percent = ((current_value - purchased_value) / purchased_value) * 100  #:.2f is used to convert it to 2 decimal places
        portfolio_info += f"{symbol}: {shares} shares | Purchased price: {venkat[symbol]} | Current Price: ₹{current_price:.2f} | Profit/Loss: {profit_loss_percent:.2f}%\n"

    total_info = f"\nTotal Investment: ₹{total_investment:.2f}\nCurrent Portfolio Value: ₹{current_portfolio_value:.2f}\n"
    if total_investment != 0:
        total_profit_loss_percent = ((current_portfolio_value - total_investment) / total_investment) * 100
        total_info += f"Total Profit/Loss: {total_profit_loss_percent:.2f}%\n"

    # Generate pie chart for portfolio performance
    generate_portfolio_pie_chart(portfolio)
    #Finally it returns the the complete portfolio information 
    return portfolio_info + total_info


def generate_portfolio_pie_chart(portfolio):
    labels = list(portfolio.keys())
    sizes = list(portfolio.values())

    plt.figure(figsize=(6, 6))  # It indicates the figure size
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal means it ensures the pie chart is circle 
    plt.title('Portfolio Performance')
    plt.savefig('static/portfolio_pie_chart.png')  # Save the pie chart as a PNG file
    plt.close()

def buy_stock(portfolio, balance, symbol, shares):
    # This function is to Buy a stock by sending portfolio, balance, symbol, shares to it.
    symbol = symbol.upper() #As yahoo finance only gives the information of stock with captial symbol
    try:
        stock = yf.Ticker(symbol + ".NS") # .NS is added because yahoo finance contains many countries stocks NS indicates the indian stock market.
        price = stock.history(period="1d")["Close"].iloc[-1] # To get price from it syntax is directly taken from the google to get the price
        if symbol in venkat:
            venkat[symbol] = float(f"{price:.2f}") 
        else:
            venkat[symbol] = float(f"{price:.2f}")

        total_cost = price * shares
        if total_cost > balance:
            return "Insufficient balance to buy!"   #if total cost is less than the balance it returns insufficient balance
        balance = balance - total_cost
        if symbol in portfolio:
            portfolio[symbol] += shares   
        else:
            portfolio[symbol] = shares     #If portofolio dictionary doesnt have this symbol it adds into the dictionary
        
        return f"Bought {shares} shares of {symbol} at ₹{price:.2f} each.\nRemaining balance: ₹{balance:.2f}"
    except Exception as e:
        return "Error: " + str(e)

def sell_stock(portfolio, balance, symbol, shares):
    if symbol in portfolio and portfolio[symbol] >= shares:
        stock = yf.Ticker(symbol + ".NS")
        price = stock.history(period="1d")["Close"].iloc[-1]   #It gets the live price from yahoofinance 
        balance = balance + (price * shares)
        portfolio[symbol] -= shares
        return f"Sold {shares} shares of {symbol} at ₹{price:.3f} each.\nRemaining balance: ₹{balance:.3f}"#:.3f indictes we are rounding the balance to three decimals
    else:
        return "You don't have enough shares to sell!"

def get_stock_prices(tickers):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        v = stock.history(period="1d")['Close'][0]
        data[ticker] = f"{v:.2f}"
    return data



def analyze_stock(symbol):
    # Fetch historical stock data
    stock_data = yf.download(symbol, start="2023-01-01", end="2024-04-21")

    # Calculate moving averages
    stock_data['MA50'] = stock_data['Close'].rolling(window=50).mean()
    stock_data['MA200'] = stock_data['Close'].rolling(window=200).mean()

    # Plotting stock data and moving averages
    plt.figure(figsize=(10, 6))
    plt.plot(stock_data['Close'], label='Close Price')
    plt.plot(stock_data['MA50'], label='50-Day Moving Average')
    plt.plot(stock_data['MA200'], label='200-Day Moving Average')
    plt.title(f'{symbol} Stock Analysis')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.savefig('static/stock1_analysis.png')  # Save the analysis plot as a PNG file
    plt.close()

    # Calculate returns
    stock_data['Daily Returns'] = stock_data['Close'].pct_change()
    stock_data['Cumulative Returns'] = (1 + stock_data['Daily Returns']).cumprod() - 1

    # Plotting cumulative returns
    plt.figure(figsize=(10, 6))
    plt.plot(stock_data['Cumulative Returns'], label='Cumulative Returns')
    plt.title(f'{symbol} Cumulative Returns')
    plt.xlabel('Date')
    plt.ylabel('Returns')
    plt.legend()
    plt.savefig('static/stock1_returns.png')  # Save the returns plot as a PNG file
    plt.close()
def google_search(query):
    try:
        url = f"https://www.google.com/search?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers) #Sends the request to get the information from the google
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='BNeawe s3v9rd AP7Wnd') #We got the class code by inspecting the google search page
        return results[0].get_text() if results else "No results found"
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"

def chatbot_response(user_input):
    if user_input.lower() == 'exit':
        return "Goodbye!"
    else:                                     #As we are using beautifulsoup for webscrapping it often may give 404 error beacuse of more request sent 
        return google_search(user_input)      #For solving that we also have function yahoo_serach. if we face such error just replace google_search with yahoo_search
    


# Routes for different pages: index, portfolio, buy, sell, latest_news, chatbot, analyze
# The index route displays the homepage with scrolling live stock prices
# The portfolio route shows the user's portfolio and its performance
# The buy route allows users to buy stocks
# The sell route allows users to sell stocks
# The latest_news route displays the latest business news
# The chatbot route provides a chat interface where users can ask questions
# The analyze route analyzes a stock's performance and displays relevant charts




@app.route('/')
def index():        # " / "  indicates after executing code it redirects to the index.html page 
    tickers = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS', 'MRF.NS', 'HSCL.NS'] #It has a functionality of scrolling prices on the top of the page
    stock_prices = get_stock_prices(tickers)
    return render_template('index.html', stock_prices=stock_prices) 

@app.route('/portfolio')
def view_portfolio():
    # displaying portfolio
    portfolio_info = display_portfolio(portfolio, balance) 
    return render_template('portfolio.html', portfolio_info=portfolio_info)

@app.route('/buy', methods=['GET', 'POST'])   # The buy route allows users to buy stocks
def buy():
    # buying shares and recording the prices 
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        shares = int(request.form['shares'])
        try:
            stock = yf.Ticker(symbol + ".NS")
            price = stock.history(period="1d")["Close"].iloc[-1]  #In this route sell it uses both post and get which taken value from html page and runs with this backend code and return to sell html page
            total_price = price * shares
            message = f"Price of 1 share of {symbol}: ₹{price:.2f} . Total price: ₹{total_price:.2f}."
            return render_template('buy.html', message=message, symbol=symbol, shares=shares)
        except Exception as e:
            return render_template('buy.html', message=f"Error: {str(e)}")
    return render_template('buy.html')   


@app.route('/confirm_buy', methods=['POST'])
def confirm_buy():
    symbol = request.form['symbol']      #In the above route after returning to buy.html hidden part confirm buy option we get

    shares = int(request.form['shares'])
    message = buy_stock(portfolio, balance, symbol, shares) #If we click on confirm buy it execute the buy_stock code 
    return render_template('message.html', message=message) #It return to the message page with message of these many stocks you bought

@app.route('/sell', methods=['GET', 'POST'])    # The sell route allows users to sell stocks
def sell():
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()    #In this route sell it uses both post and get which taken value from html page and runs with this backend code and return to sell html page
        shares = int(request.form['shares'])
        try:
            stock = yf.Ticker(symbol + ".NS")
            price = stock.history(period="1d")["Close"].iloc[-1]
            total_price = price * shares
            message = f"Price of 1 shares of {symbol}: ₹{price:.2f} . Total price: ₹{total_price:.2f}."
            return render_template('sell.html', message=message, symbol=symbol, shares=shares)
        except Exception as e:
            return render_template('sell.html', message=f"Error: {str(e)}")
    return render_template('sell.html')

@app.route('/confirm_sell', methods=['POST'])
def confirm_sell():
    symbol = request.form['symbol']    #In the above route after returning to sell.html hidden part confirm buy option we get

    shares = int(request.form['shares']) #If we click on confirm buy it execute the sell_stock code 
    message = sell_stock(portfolio, balance, symbol, shares) #It return to the message page with message of these many stocks you sell
    return render_template('message.html', message=message)

@app.route('/update_prices')
def update_prices():
    tickers = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS', 'TATAMOTORS.NS', 'MRF.NS', 'TCS.NS', "HSCL.NS"]
    stock_prices = get_stock_prices(tickers)
    return jsonify(stock_prices)    #this app route updates the price of tickers for every 10 seconds

@app.route('/stream')
def stream():
    tickers = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS', 'TATAMOTORS.NS', 'MRF.NS', 'TCS.NS', "HSCL.NS"]
    def event_stream():
        while True:
            yield 'data: {}\n\n'.format(jsonify(get_stock_prices(tickers)))
            time.sleep(10)  # Update after every 10 seconds 
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/latest_news')   # The latest_news route displays the latest business news
def latest_news():
    news = get_news()     #The top business news news in india is taken from newsapi.org and gives it in the stock_news.html page
    return render_template('stock_news.html', latest_news=news)

@app.route('/chatbot', methods=['GET', 'POST']) # The chatbot route provides a chat interface where users can ask question
def chatbot():
    if request.method == 'POST':
        user_input = request.form.get('user_input', '')  # From html page after we entering our query 
        if user_input:                                   #It  sends that query to the chatbot function 
            response = chatbot_response(user_input)       #In chatbot function we made it to return the google_search query using requests and beautiful soup library
            return render_template("chatbot.html", response=response)  #If input is given it generates the response and returns to the chatbot html page
        else:
            return render_template("chatbot.html", response="No input provided")
    else:
        return render_template("chatbot.html", response="")
@app.route('/analyze', methods=['POST'])  # The analyze route analyzes a stock's performance and displays relevant charts
def analyze():
    symbol = request.form['symbol'].upper()   #It is one of the major and useful functionality of this app
    analyze_stock(symbol + ".NS")             #After entering stock name it gets the complete hidtory prices af that stock
    #Using that price history and using matplotlib be made a graph of price vs day and the lines of 200 day average and 50 day average
    return render_template('analysis.html', symbol=symbol, stock_img="stock1_analysis.png", returns_img="stock1_returns.png")

if __name__ == "__main__":
    app.run(debug=True)
















