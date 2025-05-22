# Work in progress for now

# Idea
Everybody tells you to buy the dip, but is this actually true?

The goal of this project is to try and predict if a stock will return to its previous value within a month after a sudden drop in price. 


# How it works 
This script takes in a pre-defined list of stocks. From these stocks we will get historical price data and determine when a price drop occurred. 
If a price drop is located we will check if the stock recovered after a month or not. 
From this we train a model on this data which will try and predict recoveries. 

If this works well you can use it to determine if you should just "buy the dip."

# Files used:
1. Got SP500 csv from some random place on the web

# Future ideas
1. replace close with high and low 
price_history_df['1 day recovery'] = 100 / price_history_df['Close'].shift(1)  * price_history_df['High'][::-1].rolling(window=1).max()[::-1]
price_history_df['1 week drop'] = 100 / price_history_df['Close'].rolling(window=7).max().shift(1) * price_history_df['Close']