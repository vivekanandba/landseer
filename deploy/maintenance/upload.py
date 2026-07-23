"""Upload a local file to GCS (auth via ADC / the Cloud Run runtime SA)."""
import sys

from google.cloud import storage


def main():
    bucket_name, local_path, dest_path = sys.argv[1], sys.argv[2], sys.argv[3]
    client = storage.Client()
    client.bucket(bucket_name).blob(dest_path).upload_from_filename(local_path)
    print(f"[maint] uploaded gs://{bucket_name}/{dest_path}")


if __name__ == "__main__":
    main()
