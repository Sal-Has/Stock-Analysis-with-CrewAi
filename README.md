# Stock Analysis Tool: Visualize US Company Metrics for Informed Investments
___
The code facilitates comprehensive stock analysis by providing tools to visualize essential metrics of US companies, aiding users in making informed investment decisions based on ROI, free cash flows, and current performance data.
___
## Introduction
___
Our project aims to provide a robust solution for stock analysis, empowering users to evaluate US companies effectively. By leveraging interactive tools and visualizations, our code facilitates the exploration of crucial financial metrics like Return on Investment (ROI) and free cash flows. This enables users to make informed investment decisions based on real-time performance data, enhancing their ability to navigate the complexities of financial markets with confidence.
Our project utilizes CrewAI to streamline financial data analysis and reporting tasks .For more on this check out [Joao Moura's Github](https://github.com/joaomdmoura)

## The Tasks

1.Generate Financial Charts: Creates charts that provide insights into company performance.

2.Alert Settings: Allows users to set alerts for significant stock price changes, providing news on possible reasons for fluctuations.

3.Fluctuation Visualization: Displays price fluctuations throughout the year, aiding in understanding market trends.

4.Annotation Feature: Enables users to make annotations to track events influencing stock prices over time.

## Getting started
___
To get started with Stock Analysis Tools, follow these simple steps:

1. Installation
pip install crewai
If you want to install the 'crewai' package along with its optional features that include additional tools for agents, you can do so by using the following command: pip install 'crewai[tools]'. This command installs the basic package and also adds extra components which require more dependencies to function."

pip install 'crewai[tools]'

2.Flask: Web framework for Python.
pip install Flask

3.Plotly: Python graphing library for creating interactive plots and charts.
pip install plotly
4.Pandas: Data manipulation and analysis library.

5.Requests: HTTP library for making requests and retrieving data from APIs.

6.SQLAlchemy: SQL toolkit and Object-Relational Mapping (ORM) for Python.

7.Requests-HTML: Library for web scraping and parsing HTML.

Project Structure

project-root/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── forms.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       ├── layout.html
│       ├── index.html
│       ├── searchstock.html
│       ├── watchlist.html
│       └── dashboard.html
├── instance/
│   └── config.py
├── migrations/
│   └── versions/
├── tests/
│   └── test_app.py
├── scripts/
│   ├── data_scraper.py
│   └── analysis.py
├── config.py
├── run.py
├── requirements.txt
└── README.md
