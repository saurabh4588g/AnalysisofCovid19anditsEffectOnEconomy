import os
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
app = dash.Dash(__name__)
server = app.server
app.title = 'nCoViD Visualization | Visualizing CoViD19 cases around the world'
import numpy as np
import pandas as pd
from pandas_datareader import data
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.express as px
import cufflinks as cf
def non_cumulative(l):
    for i in range (len(l)-1, 0, -1):
        l[i] -= l[i-1]
    return l
def sort_by_country(country):
    temp_df = df[df['Country/Region'] == country]
    temp_df = temp_df.drop('Province/State', axis=1).drop('SNo', axis=1)
    temp_df = temp_df.groupby(['Country/Region', 'ObservationDate'], as_index=False).aggregate(['sum'], )
    temp_df.columns = df.columns[4:]
    temp_df= temp_df[temp_df['Confirmed'] != 0]
    temp_df['ConfirmedPerDay'] = non_cumulative(temp_df['Confirmed'].copy())
    temp_df['DeathsPerDay'] = non_cumulative(temp_df['Deaths'].copy())
    temp_df['RecoveredPerDay'] = non_cumulative(temp_df['Recovered'].copy())
    temp_df['Country'] = [country]*temp_df.shape[0]
    return temp_df
def stockCompare(company, attr='Close'):
    start_date = '-01-15'
    end_date = '-10-16'

    stocks20 = data.DataReader(company, 'yahoo', f'2020{start_date}', f'2020{end_date}')
    stocks19 = data.DataReader(company, 'yahoo', f'2019{start_date}', f'2019{end_date}')
    stocks18 = data.DataReader(company, 'yahoo', f'2018{start_date}', f'2018{end_date}')

    stocks18 = pd.DataFrame(stocks18[attr])
    stocks18.columns = ['2018']
    stocks18['DDMM'] = pd.Series(stocks18.index.values).apply(lambda x: '2020-'+str(x).split(' ')[0][5:]).values

    stocks19 = pd.DataFrame(stocks19[attr])
    stocks19.columns = ['2019']
    stocks19['DDMM'] = pd.Series(stocks19.index.values).apply(lambda x: '2020-'+str(x).split(' ')[0][5:]).values

    stocks20 = pd.DataFrame(stocks20[attr])
    stocks20.columns = ['2020']
    stocks20['DDMM'] = pd.Series(stocks20.index.values).apply(lambda x: '2020-'+str(x).split(' ')[0][5:]).values

    compare = pd.merge(left=stocks18, right=stocks19, on='DDMM', how='outer')
    compare = pd.merge(left=compare, right=stocks20, on='DDMM', how='outer')
    compare.set_index('DDMM', inplace=True)
    compare.sort_index(inplace=True)
    compare.fillna(method='ffill', inplace=True)
    return compare
df = pd.read_csv('https://raw.githubusercontent.com/lukefire5156/nCoViD-Viz/master/covid_19_data/covid_19_data.csv')
df['Active'] = df['Confirmed'] - df['Deaths'] - df['Recovered']
df['ObservationDate'] = pd.to_datetime(df['ObservationDate'])

df_country = sort_by_country(df['Country/Region'].value_counts().index[0])

for i in range(1, len(df['Country/Region'].value_counts())):
    temp = sort_by_country(df['Country/Region'].value_counts().index[i])
    df_country = pd.concat([df_country, temp])

df_country['Date'] = list(map(lambda x: x[1] ,df_country.index.values))
df_country = df_country.sort_index()

df['ConfirmedPerDay'] = non_cumulative(df['Confirmed'].copy())
df['DeathsPerDay'] = non_cumulative(df['Deaths'].copy())
df['RecoveredPerDay'] = non_cumulative(df['Recovered'].copy())
map_df = df_country.copy()
map_df['DateStr'] = map_df['Date'].apply(lambda x: str(x).split(' ')[0])
map_df.sort_values(by='Date', inplace=True)
dates = pd.Series(df_country['Date'].unique())
total_cases = df_country[['Confirmed','ConfirmedPerDay', 'Deaths','DeathsPerDay', 'Recovered','RecoveredPerDay', 'Active', 'Date']]
total_cases = total_cases.groupby('Date').sum()
stocks_df = pd.read_csv('https://raw.githubusercontent.com/lukefire5156/nCoViD-Viz/master/covid_19_data/NASDAQcompanylist.csv')
stock_options = []
for tic in stocks_df.index:
    val = stocks_df.loc[tic]
    stock_options.append({'label':'{} - {}'.format(val['Symbol'], val['Name']), 'value':val['Symbol']})

mapOptions = [{'label': 'Confirmed', 'value': 'Confirmed'}, {'label': 'Deaths', 'value': 'Deaths'}, {'label': 'Active', 'value': 'Active'}, {'label': 'Recovered', 'value': 'Recovered'}]
countries = [{'label': country, 'value': country} for country in df_country['Country'].unique()]
app.layout = html.Div([
    html.H1('Data Visualization CSE3020', className="app--title"),
    html.H3('These are a few visualizations of the widespread pandemic COVID19. Presented by - RITIK GUPTA [18BCE0154], AYUSH SHARMA [18BCE0172], SHASHANK RAJORIA [18BCE2231]', className = "app--subt"),
    html.H1('COVID19 Visualization Timeline'),
    html.P('Press the play button to see an animation of the spread of COVID19 globally. You can zoom in and out and move around the map as well.'),
    html.Div([
        html.H3('Select Type of Display : '),
        dcc.Dropdown( 
            id='mapsDispType',
            options=mapOptions,
            value='Confirmed',
            multi=False,
            className="dropdown"
        ),
        dcc.Graph(id="map-graph")
    ]),
    html.Div([
        html.H1('Improvement'),
        html.H3('The following graph is a logarithmic plot of the timeline of COVID19. You can double-click on the countries on the right to view their inidividual timeline'),
        dcc.Graph(
            id = 'logPlot',            
            figure = px.line(
                df_country,
                x='Confirmed',
                y='ConfirmedPerDay',
                color='Country',
                log_x=True, log_y=True,
                title='Logistic Plot'
            )
        )
    ]),
    html.Div([
        html.H1('Country-Specific'),
        html.H3('Select a Country and view its COVID timeline. You can select a section of the graph to zoom in as well.'),
        html.Div([
            html.H3('Select Country : '),
            dcc.Dropdown(
                id='countrySpreadPlot',
                options=countries,
                value="India",
                multi=False
            )
        ]),
        dcc.Graph(id="spreadPlot"),
        dcc.Graph(id="spreadPlotDaily")
    ]),
    html.Div([
        html.H1('Customizable'),
        html.H3('The following graph is an EPI Curve, it can be customized using the dropdowns below and on clicking a country to view the country specifics.'),
        html.Div([
        html.H3('Select Type of Display : '),
        dcc.Dropdown( 
            id='barDispType',
            options=mapOptions,
            value='Confirmed',
            multi=False
        )
    ]),
        html.Div([
            dcc.Dropdown(
            id='barDispSum',
            options=[{'label': 'PerDay', 'value':'PerDay'}, {'label' : 'Cumulative', 'value': ''}],
            value='',
            multi=False
        )
        ]),
        dcc.Graph(id="barPlot")
    ]),

    html.Div([
        html.H1('Financial Hit'),
        html.H3('COVID19 has hit the market! It has affected the companies and a lot of people have lost their jobs as well. The below graphs are a Spread Plot of the stock prices of the company and how COVID has affected the company over time.'),
        html.Div([
            dcc.Dropdown(
                id='company_stock_ip',
                value='AMZN',
                options=stock_options,
                multi=False
            ),
            dcc.Input(
                id='company_stock_ip_others',
                value='^BSESN',
                debounce=True
            ),
        ]),
        dcc.Graph(id='stock_spread'),
        dcc.Graph(id='covid_stock_spread')
    ])
])

@app.callback(Output("map-graph", "figure"), [Input('mapsDispType', "value")])
def make_map(disp_map):
    return px.choropleth(map_df, locations="Country", 
                    locationmode='country names', color=disp_map, 
                    hover_name="Country", 
                    animation_frame='DateStr',
                    # color_continuous_scale="peach", 
                    title=f'Countries with {disp_map} Cases')

@app.callback(
    [Output("spreadPlot", "figure"), 
    Output("spreadPlotDaily", "figure")], 
    [Input('countrySpreadPlot', 'value')]
)
def make_spread_plot(country):
    spread_data = df_country[df_country['Country']==country]
    spread_data.set_index('Date', inplace=True)

    spread_plot = spread_data[['Confirmed', 'Deaths', 'Recovered']].iplot(
        kind='spread', 
        asFigure=True,
        title= f'Spread plot of Cumulative cases in {country}'
    )

    spread_plot_daily = spread_data[['ConfirmedPerDay', 'DeathsPerDay', 'RecoveredPerDay']].iplot(
        kind='spread',
        asFigure=True,
        title= f'Spread plot of Daily cases in {country}'
    )

    return spread_plot, spread_plot_daily

@app.callback(
    Output("barPlot", "figure"), 
    [Input('barDispType', 'value'), 
    Input('barDispSum', 'value')]
)
def make_bar_plot(dispType, dispSum):
    return px.bar(
        df_country,
        x='Date',
        y=f'{dispType}{dispSum}',
        color='Country',
        title=f'EPI Curve of {dispSum} {dispType} cases'
    )

@app.callback(
    [Output('stock_spread', 'figure'), 
    Output('covid_stock_spread', 'figure')], 
    [Input('company_stock_ip', 'value'), 
    Input('company_stock_ip_others', 'value')]
)
def make_stock_spread_plot(company, company_other):
    if(company=='OTHER'):
        company = company_other
    company_stocks = stockCompare(company)
    
    company_stocks_graph = company_stocks[['2020', '2018', '2019']].iplot(
        kind='spread', 
        asFigure=True,
        title=f'Stocks Comparision of {company}'
    )

    stocks_affect = total_cases.join(company_stocks)
    stocks_affect['ConfirmedPerDay'] = stocks_affect['ConfirmedPerDay']/max(stocks_affect['ConfirmedPerDay'])
    stocks_affect['2020'] = stocks_affect['2020']/max(stocks_affect['2020'])
    stocks_affect.columns.values[-1] = 'Stock Value'
    
    stocks_affect_graph = stocks_affect[['ConfirmedPerDay', '2020']].iplot(
        kind='spread', 
        asFigure=True,
        title=f'Effect of CoViD Cases on {company} stock price'
    )
    return company_stocks_graph, stocks_affect_graph
if __name__ == '__main__':
    app.run_server()
