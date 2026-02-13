import pandas as pd
from datetime import datetime

def extract_reviews(data):
    """
    Extracts the list of individual reviews from the __NEXT_DATA__ object.
    This is typically only the first page of reviews (~20).
    """
    if not data:
        return []
    try:
        return data['props']['pageProps']['reviews']
    except (KeyError, TypeError):
        return []

def calculate_recent_reviews_count(data, days=7):
    """
    Calculates the number of reviews in the last 'days' days.
    Note: This is limited by the number of reviews available in the initial data fetch (usually 20).
    """
    reviews = extract_reviews(data)
    if not reviews:
        return 0
    
    try:
        df = pd.DataFrame(reviews)
        if 'dates' not in df.columns:
            return 0
            
        # Extract publishedDate
        published_dates = df['dates'].apply(lambda x: x.get('publishedDate') if isinstance(x, dict) else None)
        published_dates = pd.to_datetime(published_dates, utc=True)
        
        published_dates = published_dates.dropna()
        if published_dates.empty:
            return 0
            
        # Use current time as reference, but handle potential future data in test files
        now = pd.Timestamp.now(tz='UTC')
        max_date = published_dates.max()
        reference_date = max_date if max_date > now else now
        
        cutoff = reference_date - pd.Timedelta(days=days)
        return int(published_dates[published_dates >= cutoff].count())
    except Exception:
        return 0

def extract_main_page_star_distribution(data):
    """Extracts the overall star distribution data from the main page."""
    try:
        # Accessing filters -> reviewStatistics -> ratings
        ratings = data['props']['pageProps']['filters']['reviewStatistics']['ratings']
        
        rating_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
        data_list = []
        total_count = ratings.get('total', 0)
        
        if total_count == 0:
            return pd.DataFrame()
        
        for key, rating_val in rating_map.items():
            count = ratings.get(key, 0)
            data_list.append({'rating': rating_val, 'count': count})
                
        df = pd.DataFrame(data_list)
        if not df.empty:
            df['percentage'] = (df['count'] / total_count) * 100
            df = df.sort_values('rating')
            
        return df
    except (KeyError, TypeError):
        return pd.DataFrame()

def extract_aggregate_star_distribution(data):
    """Extracts the overall star distribution data from the transparency page."""
    try:
        # Accessing reviewStatistics -> starsDistribution -> all
        dist = data['props']['pageProps']['reviewStatistics']['starsDistribution']['all']
        
        rating_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
        data_list = []
        total_count = 0
        
        for key, count in dist.items():
            if key in rating_map:
                data_list.append({'rating': rating_map[key], 'count': count})
                total_count += count
                
        df = pd.DataFrame(data_list)
        if not df.empty:
            df['percentage'] = (df['count'] / total_count) * 100
            df = df.sort_values('rating')
            
        return df
    except (KeyError, TypeError):
        return pd.DataFrame()

def extract_reviews_over_time(data):
    """Extracts the data for the 'reviews over time' chart from the transparency page."""
    try:
        # Accessing reviewStatistics -> monthlyDistribution -> all
        monthly_dist = data['props']['pageProps']['reviewStatistics']['monthlyDistribution']['all']
        
        data_list = []
        for star_key, dates in monthly_dist.items():
            for date_str, count in dates.items():
                try:
                    # Format is like "2025-march"
                    date_obj = datetime.strptime(date_str.title(), "%Y-%B")
                    data_list.append({'date': date_obj, 'count': count})
                except ValueError:
                    continue
                    
        df = pd.DataFrame(data_list)
        if not df.empty:
            # Aggregate counts by date across all star ratings
            df = df.groupby('date')['count'].sum().reset_index()
            df = df.sort_values('date')
        return df
    except (KeyError, TypeError):
        return pd.DataFrame()

def extract_detailed_monthly_distribution(data):
    """
    Extracts detailed monthly distribution by source and rating.
    Returns a DataFrame with columns: date, source, rating, count.
    """
    try:
        monthly_dist = data['props']['pageProps']['reviewStatistics']['monthlyDistribution']
        
        data_list = []
        rating_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
        
        for source, ratings in monthly_dist.items():
            if source == 'all': continue 
            
            for rating_key, dates in ratings.items():
                if rating_key not in rating_map: continue
                rating = rating_map[rating_key]
                
                for date_str, count in dates.items():
                    try:
                        date_obj = datetime.strptime(date_str.title(), "%Y-%B")
                        data_list.append({
                            'date': date_obj,
                            'source': source,
                            'rating': rating,
                            'count': count
                        })
                    except ValueError:
                        continue
                        
        return pd.DataFrame(data_list)
    except (KeyError, TypeError):
        return pd.DataFrame()

def extract_source_distribution(data):
    """Extracts the review source distribution data from the transparency page."""
    try:
        # Accessing reviewStatistics -> collectingMethodDistribution
        sources = data['props']['pageProps']['reviewStatistics']['collectingMethodDistribution']
        
        data_list = []
        for source, count in sources.items():
            if source != 'all':
                data_list.append({'source': source, 'count': count})
                
        df = pd.DataFrame(data_list)
        return df
    except (KeyError, TypeError):
        return pd.DataFrame()

def analyze_reply_behavior(transparency_data):
    """Extracts reply behavior information from the transparency page data."""
    if not transparency_data:
        return None
    try:
        # Accessing reviewStatistics -> replyBehavior
        behavior = transparency_data['props']['pageProps']['reviewStatistics']['replyBehavior']
        
        avg_days = behavior.get('averageDaysToReply')
        label = "N/A"
        if avg_days is not None:
            if avg_days <= 1:
                label = "1 day or less"
            elif avg_days <= 7:
                label = "1 week or less"
            else:
                label = f"{avg_days:.1f} days"
        
        # Add label to the dictionary
        behavior['label'] = label
        return behavior
    except (KeyError, TypeError):
        return None