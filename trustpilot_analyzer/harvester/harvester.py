import httpx
import json
from parsel import Selector

def fetch_next_data(url: str):
    """
    Fetches the __NEXT_DATA__ JSON object from a Trustpilot page.

    Args:
        url: The URL of the Trustpilot page to scrape.

    Returns:
        A dictionary containing the __NEXT_DATA__ JSON object, or None if not found.
    """
    try:
        # Use headers to mimic a real browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        with httpx.Client(headers=headers, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")
        return None
    except httpx.HTTPStatusError as exc:
        print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        return None

    selector = Selector(text=response.text)
    next_data_script = selector.css('script#__NEXT_DATA__::text').get()

    if not next_data_script:
        print("Could not find __NEXT_DATA__ script tag.")
        return None

    try:
        next_data_json = json.loads(next_data_script)
        return next_data_json
    except json.JSONDecodeError:
        print("Failed to decode JSON from __NEXT_DATA__.")
        return None

if __name__ == '__main__':
    # Example usage:
    test_domain = "store.manutd.com"
    test_url = f"https://www.trustpilot.com/review/{test_domain}"
    print(f"Fetching data for: {test_url}")
    
    data = fetch_next_data(test_url)
    
    if data:
        print("Successfully fetched __NEXT_DATA__.")
        if 'props' in data and 'pageProps' in data['props'] and 'businessUnit' in data['props']['pageProps']:
            business_unit = data['props']['pageProps']['businessUnit']
            print(f"Business Name: {business_unit.get('displayName')}")
            print(f"TrustScore: {business_unit.get('trustScore')}")
            print(f"Number of reviews: {business_unit.get('numberOfReviews')}")
        else:
            print("Could not find expected data in __NEXT_DATA__ JSON.")

        # Save the full JSON data to a file
        output_path = "trustpilot_data.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Full __NEXT_DATA__ JSON saved to {output_path}")
    else:
        print("Failed to fetch __NEXT_DATA__.")
