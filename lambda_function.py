import json
import time
import requests  # type: ignore
import boto3  # type: ignore
import pandas as pd  # type: ignore
from datetime import date
from jobspy import scrape_jobs  # type: ignore
from io import StringIO
from supabase import create_client, Client  # type: ignore
import math
from table_schema import ai_added_cols_schema, get_all_col_names
from job_spy_cols import job_spy_expected_cols
from utils import extract_location_details, send_gmail
import os

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BATCH_FILE_PATH = os.environ["BATCH_FILE_PATH"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def validate_env_vars():
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "BATCH_FILE_PATH", "OPENAI_API_KEY"]
    for var in required_vars:
        if var not in os.environ:
            raise EnvironmentError(f"Missing environment variable: {var}")

validate_env_vars()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
s3_client = boto3.client("s3")

prompt = f"""
Given the following job description return JSON following the JSON schema: {str(ai_added_cols_schema)}, filling in values as accurately as possible in the context of the job description.
Job Description:
"""

location = "Sydney NSW"
country = "Australia"

def make_request(url, headers, data=None, files=None, method="post"):
    if method.lower() == "post":
        response = requests.post(url, headers=headers, json=data, files=files)
    else:
        response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def lambda_handler(event, context):

    try:
        # Scrape jobs
        jobs = scrape_jobs(
            site_name="indeed",
            search_term="",
            location=location,
            results_wanted=999,
            hours_old=24,
            country_indeed=country,
            enforce_annual_salary=True,
        )
        
        # Ensure all required columns are present
        for column in job_spy_expected_cols:
            if column not in jobs.columns:
                jobs[column] = None

        jobs = jobs.assign(
            location_suburb=lambda df: df["location"].apply(lambda loc: extract_location_details(loc)[0]),
            location_state=lambda df: df["location"].apply(lambda loc: extract_location_details(loc)[1]),
            location_country=lambda df: df["location"].apply(lambda loc: extract_location_details(loc)[2])
        )

        if jobs.empty:
            raise Exception("No jobs found")
        
        print(f"First row: {jobs.iloc[0]}")

        # Prepare batch requests data
        requests_data = []
        for i, row in jobs.iterrows():
            desc = row.get("description", "")

            request = {
                "custom_id": row["id"],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-2024-08-06",
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": ai_added_cols_schema,
                    },
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt + desc},
                    ],
                    "max_tokens": 1000,
                },
            }
            requests_data.append(request)

        # Create and upload the batch file
        with open(BATCH_FILE_PATH, "w") as f:
            for request in requests_data:
                f.write(json.dumps(request) + "\n")

        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

        with open(BATCH_FILE_PATH, "rb") as batch_file:
            files = {
                "file": (BATCH_FILE_PATH, batch_file),
                "purpose": (None, "batch"),
            }
            response = make_request("https://api.openai.com/v1/files", headers, files=files)

        file_id = response["id"]

        # Create the batch job
        headers["Content-Type"] = "application/json"
        data = {
            "input_file_id": file_id,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
        }
        response = make_request("https://api.openai.com/v1/batches", headers, data=data)
        batch_id = response["id"]
        print(f"Batch job created with ID: {batch_id}")

        # Poll for batch job completion
        url = f"https://api.openai.com/v1/batches/{batch_id}"
        poll_interval = 5
        max_wait_time = 600  # Maximum wait time of 10 minutes
        total_wait_time = 0
        output_file_id = ""

        while total_wait_time < max_wait_time:
            response = make_request(url, headers, method="get")
            status = response["status"]
            if status == "completed":
                output_file_id = response["output_file_id"]
                break
            time.sleep(poll_interval)
            total_wait_time += poll_interval
        else:
            print("Batch job timed out")
            return {"statusCode": 500, "body": json.dumps("Batch job timed out")}

        # Get the batch results
        url = f"https://api.openai.com/v1/files/{output_file_id}/content"
        results_content = requests.get(url, headers=headers).content

        # Process results and join with original DataFrame
        results = []
        for line in results_content.splitlines():
            result = json.loads(line)
            response_body = json.loads(
                result["response"]["body"]["choices"][0]["message"]["content"]
            )
            response_body["custom_id"] = result["custom_id"]
            results.append(response_body)

        results_df = pd.DataFrame(results)
        final_df = jobs.merge(results_df, left_on="id", right_on="custom_id")

        # Convert date_posted to Unix timestamp
        final_df["date_posted_unix_ts"] = pd.to_datetime(final_df["date_posted"]).apply(
            lambda x: int(x.timestamp())
        )

        # Rename the columns accordingly
        final_df = final_df.rename(columns={"id": "job_spy_id"})

        # Keep only the necessary columns for the Supabase table
        final_df = final_df[get_all_col_names()]

        # Convert the DataFrame to a list of dictionaries and remove NaN values
        cleaned_records = final_df.dropna().to_dict(orient="records")

        # Write to Supabase
        try:
            response = supabase.table("jobs").insert(cleaned_records).execute()
        except Exception as exception:
            raise exception

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Processed and stored in supabase successfully"}),
        }
    except Exception as e:
        print(e)
        return {"statusCode": 500, "body": json.dumps("There was an error")}
