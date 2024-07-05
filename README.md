# Stock Analysis Tool: Visualize US Company Metrics for Informed Investments
___
The code facilitates comprehensive stock analysis by providing tools to visualize essential metrics of US companies, aiding users in making informed investment decisions based on ROI, free cash flows, and current performance data.
___
## Introduction
___
Our project aims to provide a robust solution for stock analysis, empowering users to evaluate US companies effectively. By leveraging interactive tools and visualizations, our code facilitates the exploration of crucial financial metrics like Return on Investment (ROI) and free cash flows. This enables users to make informed investment decisions based on real-time performance data, enhancing their ability to navigate the complexities of financial markets with confidence.
Our project utilizes CrewAI to streamline financial data analysis and reporting tasks .For more on this check out [Joao Moura's Github](https://github.com/joaomdmoura)

## Project SetUp/Installation Instructions
___
### Dependencies
* Flask  
[Flask link](https://pypi.org/project/Flask/)

* CrewAi  
[Joao Moura's Github](https://github.com/joaomdmoura)

* QuickFs API  
[QuickFs link](https://quickfs.net/)




### Installation Steps

1. Clone the repository in your own local file:
```
git clone https://github.com/Sal-Has/Stock-Analysis-with-CrewAi.git


```
2. Create a virtual environment and activate it:
```
python -m venv venv

venv\Scripts\activate

```


3. Install the required packages:
```
pip install -r requirements.txt

```
4. Run the development server:
```
flask run

```
## Usage Instructions
___

### How to Run
1. Ensure the virtual environment is activated.
2. Run the Flask development sever:
```
flask run

```

3. Access the web application in your browser at http://127.0.0.1:5000

### Examples  

* Generate Financial Charts: Creates charts that provide insights into company performance.

* Alert Settings: Allows users to set alerts for significant stock price changes, providing news on possible reasons for fluctuations.

* Fluctuation Visualization: Displays price fluctuations throughout the year, aiding in understanding market trends.

* Annotation Feature: Enables users to make annotations to track events influencing stock prices over time.  

### Input/Output
* Input: The company ticker and the specific metric you would a chart for

## Project Structure
___
### Overview

```
RegisterandLogin/
│
├── .venv/
│   └── library root
├── crew/
├── crewai/
├── static/
│   ├── css/
│   ├── flags/
│   ├── fonts/
│   └── img/
│       ├── uploads/
│       │   └── my_script.js
│       └── script.js
├── templates/
├── .env
├── .streamlit-running
├── __init__.py
├── config.py
├── forms.py
├── models.py
├── project_structure.md
├── README.md
├── requirements.txt
├── run.py
├── stock.png
├── streamlit_app.py
├── tempCodeRunnerFile.python
└── views.py


```


 




