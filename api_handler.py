import requests

class APIHandler:
    def __init__(self, api_endpoint, api_key):
        self.api_endpoint = api_endpoint
        self.api_key = api_key

    def fetch_data(self):
        headers = {"x-api-key": self.api_key}
        try:
            response = requests.get(self.api_endpoint, headers=headers)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data from API: {e}")
            return None

    def parse_data(self, data):
        # Check if data is None or empty
        if not data:
            return None

        # Parse the required fields from the data
        parsed_data = {
            "epoch": data.get("epoch"),
            "layer": data.get("layer"),
            "effectiveUnitsCommited": data.get("effectiveUnitsCommited"),
            "circulatingSupply": data.get("circulatingSupply"),
            "price": data.get("price"),
            "marketCap": data.get("marketCap"),
            "totalAccounts": data.get("totalAccounts"),
            "totalActiveSmeshers": data.get("totalActiveSmeshers"),
            "nextEpoch": data.get("nextEpoch", {})  # Fetch the nested nextEpoch dictionary
        }

        return parsed_data

# Example usage
if __name__ == "__main__":
    api_handler = APIHandler("https://smeshi-api.com/network/info")
    raw_data = api_handler.fetch_data()
    parsed_data = api_handler.parse_data(raw_data)
    print(parsed_data)