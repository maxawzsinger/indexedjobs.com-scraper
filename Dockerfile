FROM public.ecr.aws/lambda/python:3.10

# Install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r requirements.txt

# Copy function code


COPY job_spy_cols.py ${LAMBDA_TASK_ROOT}

COPY lambda_function.py ${LAMBDA_TASK_ROOT}


COPY table_schema.py ${LAMBDA_TASK_ROOT}

COPY utils.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.lambda_handler" ]