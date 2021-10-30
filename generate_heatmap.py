import datetime as dt
import json
import sys
import webbrowser

import pandas as pd
import html
import plotly.graph_objects as go
import plotly.express as px

week_day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
category_order = {
    'year': [2017, 2018, 2019, 2020, 2021],
    'month': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
              'October', 'November', 'December'],
    'weekday': week_day_names,
}


def get_conversation_type(conversation):
    if conversation['threadProperties']:
        return 'group'
    else:
        return 'personal'


def decode_html(text):
    if text:
        return html.unescape(text)


def convert_conversation_to_dataframe(conversation):
    messages = conversation['MessageList']
    df = pd.DataFrame(messages)
    if not messages:
        return df

    df['group_type'] = get_conversation_type(conversation)
    df['group_name'] = decode_html(conversation['displayName'])
    df['originalarrivaltime'] = pd.to_datetime(df.originalarrivaltime).dt.tz_convert('Asia/Dhaka')

    return df


def preprocess_data(data):
    df = pd.concat([
        convert_conversation_to_dataframe(indv_conversation)
        for indv_conversation in data['conversations']
        if indv_conversation['id'] not in ['48:calllogs']
    ])
    df = df[df.group_type == 'group']
    df['weekofyear'] = df.originalarrivaltime.dt.weekofyear
    df['weekday'] = df.originalarrivaltime.apply(lambda x: week_day_names[x.weekday()])
    df['weekday_no'] = df.originalarrivaltime.dt.weekday
    df['hour'] = df.originalarrivaltime.dt.hour
    df['year'] = df.originalarrivaltime.dt.year
    df['month'] = df.originalarrivaltime.dt.strftime("%B")
    df['month_no'] = df.originalarrivaltime.dt.month

    bins = [0, 4, 8, 12, 16, 20, 24]
    labels = [
        'Late Night (12 am-4 am)',
        'Early Morning (4am-8am)',
        'Morning (8am-12pm)',
        'Noon (12pm-4pm)',
        'Eve (4pm-8pm)',
        'Night (8pm-12am)'
    ]
    df['part_of_day'] = pd.cut(df['hour'], bins=bins, labels=labels, include_lowest=True)

    return df


def plot_year_vs_count(df):
    temp_df = df.groupby('year').count().reset_index()
    temp_df = temp_df.rename(columns={'id': 'count'})
    temp_df = temp_df[['year', 'count']]
    fig = px.bar(
        temp_df,
        x='year',
        y='count',
        title='Messages Count over 5Y',
        height=500,
        width=700
    )
    return fig


def plot_user_vs_count(df):
    temp_df = df.groupby('displayName').count().reset_index()
    temp_df = temp_df.rename(columns={'id': 'count'})
    temp_df = temp_df[['displayName', 'count']]
    temp_df.sort_values(by='count', inplace=True)
    fig = px.bar(
        temp_df,
        y='displayName',
        x='count',
        title='Count Over Users',
    )
    fig.update_xaxes(rangeslider_visible=True)
    return fig


def plot_2021_week_vs_count(df):
    all_year_df = pd.DataFrame()
    for name, group in df[df['group_type'] == 'group'].groupby('year'):
        temp_df = group
        temp_df = temp_df.groupby(['month', 'month_no']).count().reset_index()
        temp_df = temp_df.rename(columns={'id': 'count'})
        temp_df = temp_df[['month', 'count', 'month_no']]
        temp_df['year'] = name

        all_year_df = pd.concat([all_year_df, temp_df])

    fig = px.bar(
        all_year_df,
        y='count',
        x='month',
        title='Month vs Count By Year',
        height=600,
        facet_col='year',
        category_orders=category_order
    )
    return fig


def plot_2021_weekday_vs_count(df):
    all_year_df = pd.DataFrame()
    for name, group in df[df['group_type'] == 'group'].groupby('year'):
        temp_df = group
        temp_df = temp_df.groupby(['weekday', 'weekday_no']).count().reset_index()
        temp_df = temp_df.rename(columns={'id': 'count'})
        temp_df = temp_df[['weekday', 'count', 'weekday_no']]
        temp_df['year'] = name

        all_year_df = pd.concat([all_year_df, temp_df])

    all_year_df.sort_values(by='weekday_no', inplace=True)
    all_year_df.sort_values(by='year', ascending=False, inplace=True)
    fig = px.bar(
        all_year_df,
        y='count',
        x='weekday',
        title='Week vs Count By Year',
        height=600,
        facet_col='year',
        category_orders=category_order
    )
    return fig


def plot_time_of_day(df):
    temp_df = df.groupby(['hour']).count().reset_index()
    temp_df = temp_df.rename(columns={'id': 'count'})
    temp_df = temp_df[['hour', 'count']]
    fig = px.bar(
        temp_df,
        y='count',
        x='hour',
        title='Time of Day',
        height=600,
    )
    fig.update_xaxes(type='category')

    return fig


def plot_part_of_day(df):
    temp_df = df.groupby(['year', 'part_of_day']).count().reset_index()
    temp_df = temp_df.rename(columns={'id': 'count'})
    temp_df = temp_df[['year', 'part_of_day', 'count']]

    fig = px.bar(
        temp_df,
        y='count',
        x='part_of_day',
        title=f'Count by Part of Day by Year',
        height=900,
        facet_col='year',
        category_orders=category_order
    )

    return fig


def plot_part_of_day_vs_weekofyear(df):
    temp_df = df.groupby(['year', 'weekofyear', 'part_of_day']).count().reset_index()
    temp_df = temp_df.rename(columns={'id': 'count'})
    temp_df = temp_df[['year', 'weekofyear', 'part_of_day', 'count']]
    fig = px.density_heatmap(
        temp_df,
        x='weekofyear',
        y='part_of_day',
        z='count',
        title='2021 by Week',
        color_continuous_scale='gnbu',
        nbinsx=52,
        facet_row='year',
        category_orders=category_order,
    )
    fig.update_xaxes(type='category')

    return fig


if __name__ == '__main__':
    json_data = json.load(open(sys.argv[1], encoding='utf-8'))
    all_data = preprocess_data(json_data)
    print('Data set created...')

    with open('test.html', 'w') as output_file:
        # plot_year_vs_count(all_data).write_html(output_file)
        # plot_user_vs_count(all_data).write_html(output_file)
        plot_part_of_day(all_data).write_html(output_file)
        plot_part_of_day_vs_weekofyear(all_data).write_html(output_file)
        plot_2021_week_vs_count(all_data).write_html(output_file)
        plot_2021_weekday_vs_count(all_data).write_html(output_file)
        plot_time_of_day(all_data).write_html(output_file)

    webbrowser.open('test.html')
