import os
import requests
import zipfile
from io import BytesIO

def create_data_folder():
    data_folder = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_folder, exist_ok=True)
    return data_folder

def download_and_unpack_zip(url, dest_folder):
    print(f"Downloading zip file from {url}...")
    response = requests.get(url)
    response.raise_for_status()

    print("Download complete. Unpacking...")

    with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(dest_folder)

    print(f"Unpacked files to {dest_folder}")

if __name__ == "__main__":
    zip_file_url = "https://bridges.monash.edu/ndownloader/articles/23306054/versions/2"

    data_folder = create_data_folder()

    download_and_unpack_zip(zip_file_url, data_folder)
