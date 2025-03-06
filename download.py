import os

import requests

# Base URL pattern for the JSON files
BASE_URL = "https://raw.githubusercontent.com/bible-api/kjv/refs/heads/master/{}.json"

# Create output directory if it doesn't exist
output_dir = "downloaded_jsons"
os.makedirs(output_dir, exist_ok=True)


def download_json(file_number):
    url = BASE_URL.format(file_number)
    response = requests.get(url)
    if response.status_code == 200:
        filename = os.path.join(output_dir, f"{file_number}.json")
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {url} (Status code: {response.status_code})")


def main():
    for i in range(1, 67):  # Files 1.json through 66.json
        download_json(i)
    print("Download complete.")


if __name__ == "__main__":
    main()
