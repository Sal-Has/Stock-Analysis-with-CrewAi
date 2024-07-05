import json
import os
from dotenv import load_dotenv
import openai
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf
import requests  # Import requests here

load_dotenv()

plot_dir = os.path.join(os.getcwd(), 'static', 'plots')
os.makedirs(plot_dir, exist_ok=True)
openai.api_key = os.getenv('OPENAI_API_KEY')

FLASK_URL = 'http://localhost:5000/store_interaction'  # Replace with your Flask app's endpoint


def send_interaction_to_flask(user_id,user_input, assistant_response, plot_filename=None):
    data = {
        'user_id': user_id,
        'user_input': user_input,
        'assistant_response': assistant_response,
        'plot_filename': plot_filename
    }
    response = requests.post(FLASK_URL, json=data)
    if response.status_code == 200:
        print("Interaction sent successfully!")
    else:
        print("Failed to send interaction. Status code:", response.status_code)

def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period="1y").iloc[-1].Close)

def calculate_SMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])

def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])

def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period="1y").Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=14-1, adjust=False).mean()
    ema_down = down.ewm(com=14-1, adjust=False).mean()
    rs = ema_up / ema_down
    return str(100 - (100 / (1 + rs)).iloc[-1])

def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period="1y").Close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust=False).mean()

    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span=9, adjust=False).mean()
    MACD_histogram = MACD - signal

    return f'{MACD[-1]},{signal[-1]},{MACD_histogram[-1]}'


def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period="1y")
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data.Close)
    plt.title(f'{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)

    # Save plot to 'static/plots' directory
    plot_filename = os.path.join(plot_dir, f'{ticker}_stock.png')

    plt.savefig(plot_filename)
    plt.close()
    return plot_filename

functions = [
    {
        'name': 'get_stock_price',
        'description': 'Gets the latest stock price given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (for example AAPL for Apple).'
                }
            },
            'required': ['ticker']
        }
    },
    {
        "name": "calculate_SMA",
        "description": "Calculate the simple moving average for a given stock ticker and window.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company is (e.g AAPL for Apple)",
                },
                "window": {
                    "type": "string",
                    "description": "This timeframe to consider when calculating the SMA"
                }
            },
            "required": ["ticker", "window"],
        },
    },
    {
        "name": "calculate_EMA",
        "description": "Calculate the exponential moving average for a given stock ticker and a window",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for company (e.g., AAPL for Apple)"
                },
                "window": {
                    "type": "integer",
                    "description": "The timeframe to consider when calculating the EMA"
                }
            },
            "required": ["ticker", "window"],
        },
    },
    {
        "name": "calculate_RSI",
        "description": "Calculate the RSI for a given stock ticker ",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company (e.g., AAPL for Apple)",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "calculate_MACD",
        "description": "Calculate the MACD for a given stock ticker .",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company (e.g., AAPL for Apple)"
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "plot_stock_price",
        "description": "Plot the stock price for the last year given the ticker symbol of a company",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company (e.g., AAPL for Apple)",
                },
            },
            "required": ["ticker"],
        },
    },
]

available_functions = {
    "get_stock_price": get_stock_price,
    "calculate_SMA": calculate_SMA,
    "calculate_EMA": calculate_EMA,
    "calculate_RSI": calculate_RSI,
    "calculate_MACD": calculate_MACD,
    "plot_stock_price": plot_stock_price
}

if "messages" not in st.session_state:
    st.session_state['messages'] = []

st.title('Stock Analysis Chatbot Assistant')


user_input = st.text_input('Your Input:')
user_id =  st.number_input("Enter your userid", min_value=0, max_value=150)


if user_input:
    try:
        st.session_state['messages'].append({'role': 'user', 'content': f"{user_input}"})

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=st.session_state['messages'],
            functions=functions,
            function_call='auto'
        )
        response_message = response['choices'][0]['message']

        if response_message.get('function_call'):
            function_name = response_message['function_call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])
            plot_filename = None

            if function_name in ['get_stock_price', 'calculate_RSI', 'calculate_MACD']:
                args_dict = {"ticker": function_args.get('ticker')}
            elif function_name in ["calculate_SMA", "calculate_EMA"]:
                args_dict = {"ticker": function_args.get('ticker'), 'window': function_args.get('window')}
            elif function_name == "plot_stock_price":
                args_dict = {"ticker": function_args.get('ticker')}
                plot_filename = plot_stock_price(function_args.get('ticker'))
                st.image(plot_filename)

            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict)

            st.session_state['messages'].append(response_message)
            st.session_state['messages'].append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response
                }
            )
            second_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=st.session_state['messages']
            )
            assistant_response = second_response['choices'][0]['message']['content']
            st.text(assistant_response)
            st.session_state['messages'].append({'role': 'assistant', 'content': assistant_response})

            send_interaction_to_flask(user_id,user_input, assistant_response, plot_filename)

        else:
            st.text(response_message['content'])
            st.session_state['messages'].append({'role': 'assistant', 'content': response_message['content']})

    except Exception as e:
        raise e
