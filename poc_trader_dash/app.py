import asyncio
from collections import defaultdict
from os import environ

import asyncpg
import pandas as pd
import yfinance
from plotly import express as px

db_url = environ.get("DATABASE_URL")

tradier_account = environ.get("TRADIER_LIVE_ACCOUNT")
tradier_token = environ.get("TRADIER_LIVE_API_BEARER")
tradier_url = environ.get("TRADIER_LIVE_URL")


def percent_change(start, finish):
    return ((finish - start) / start) * 100


async def run():
    connection = await asyncpg.connect(dsn=db_url)
    results = await connection.fetch(
        "select account_number, date, close from account_close_snapshots order by date asc",
    )
    await connection.close()

    account_returns = defaultdict(list)
    for record in results:
        account_returns[record.get("account_number")].append(
            (record.get("date"), record.get("close"))
        )
    dfs = []
    for account, closing_values in account_returns.items():
        returns = [
            (date, percent_change(closing_values[0][1], value)) for date, value in closing_values
        ]
        dfs.append(pd.DataFrame(returns, columns=["date", account]).set_index("date"))

    spx = yfinance.download(["^SPX"], start=dfs[0].index[0]).drop(
        columns=["Open", "Close", "High", "Low", "Volume"]
    )

    spx_returns = [
        (date.date(), percent_change(spx.values[0][0], value[0])) for date, value in spx.iterrows()
    ]
    dfs.append(pd.DataFrame(spx_returns, columns=["date", "SPX"]).set_index("date"))
    fig = px.line(pd.concat(dfs, axis=1), title="Returns")
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends
        ]
    )
    fig.show()




from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children='Title of Dash App', style={'textAlign':'center'}),
    dcc.Dropdown(df.country.unique(), 'Canada', id='dropdown-selection'),
    dcc.Graph(id='graph-content')
])

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    dff = df[df.country==value]
    return px.line(dff, x='year', y='pop')

if __name__ == '__main__':
    app.run_server(debug=True)
