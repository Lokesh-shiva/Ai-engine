from pytrends.request import TrendReq

def get_google_trends(keyword="AI", timeframe="now 7-d"):
    """
    Fetch interest over time for a given keyword from Google Trends.

    Parameters:
        keyword (str): The keyword to search trends for.
        timeframe (str): The timeframe to fetch data (e.g., "now 7-d" for the last 7 days).

    Returns:
        DataFrame: A pandas DataFrame containing interest over time.
    """
    pytrends = TrendReq()
    pytrends.build_payload(kw_list=[keyword], timeframe=timeframe)
    return pytrends.interest_over_time()

if __name__ == "__main__":
    try:
        trends = get_google_trends()
        print(trends.head())
    except Exception as e:
        print(f"Error fetching Google Trends data: {e}")
