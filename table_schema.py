ai_added_cols_schema = {
  "name": "ai_added_cols_schema",
  "strict": True,
  "schema": {
    "type": "object",
    "properties": {
      "advertised_maximum_salary": {
        "type": "number",
        "description": "The maximum salary being advertised for the position."
      },
      "advertised_minimum_salary": {
        "type": "number",
        "description": "The minimum salary being advertised for the position."
      },
      "advertised_salary_interval": {
        "type": "string",
        "enum": ["hourly", "yearly"],
        "description": "The interval at which the salary is advertised, either hourly or yearly."
      },
      "office_type": {
        "type": "string",
        "enum": ["remote", "hybrid", "in office only"],
        "description": "The type of office setting for the job."
      },
      "non_profit_status": {
        "type": "string",
        "enum": ["non_profit", "for_profit"],
        "description": "Indicates if the job is for a non-profit organization."
      },
      "minimum_required_education": {
        "type": "string",
        "enum": ["high school", "associate degree", "bachelor degree", "master degree", "doctorate"],
        "description": "The minimum level of education required for the job."
      },
      "key_responsibilities": {
        "type": "string",
        "description": "A description of the key responsibilities for the job."
      },
      "key_required_technical_skills": {
        "type": "string",
        "description": "A description of the key technical skills required for the job."
      },
      "required_experience": {
        "type": "string",
        "description": "A description of the experience required for the job."
      }
    },
    "required": [
      "advertised_maximum_salary",
      "advertised_minimum_salary",
      "advertised_salary_interval",
      "office_type",
      "non_profit_status",
      "minimum_required_education",
      "key_responsibilities",
      "key_required_technical_skills",
      "required_experience"
    ],
    "additionalProperties": False
  }
}



non_ai_cols = [
  "job_spy_id", 
  "site", 
  "job_url", 
  "job_url_direct", 
  "title", 
  "company",
  "location_suburb", 
  "location_state", 
  "location_country", 
  "date_posted_unix_ts",
  "description", 
]

def get_all_col_names():
    # Extract the property names from the schema
    property_names = list(ai_added_cols_schema["schema"]["properties"].keys())
    
    # Combine the extracted property names with the non_ai_cols
    combined_cols = non_ai_cols + property_names
    
    return combined_cols
