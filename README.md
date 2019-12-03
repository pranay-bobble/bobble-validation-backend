# bobble-validation-backend
This git repo holds the various cloud functions used for bobble validation tasks (IMAGE).

## Setup
- pip install -r requirements.txt

## API Endpoints (Cloud Functions)
create_user.py
- Used by the ADMIN to create a new pair of user
- Pass username, password and full name as json in body

log_in.py
- API endpoint used to log in
- Pass username and password as json in body
- If user exists, JWT is assigned

get_tasks.py
- Used to assign a task to a particular user
- Pass JWT in headers with key as 'x-access-token'
- If JWT is valid and has not expired, task is assigned (pending or new)
- Returns task id, input image url, output image url

submit_review.py
- Used to submit score of task assigned to user via get_tasks API
- Pass JWT in headers with key as 'x-access-token'
- Pass the task_id in url. Example: 'submit_review/<task_id>'
- Pass score for the task as json with key 'review_score'

## Running locally
### Allow connections to Cloud SQL (In directory holding Cloud_sql_proxy)<br />
Cloud_sql_proxy -instances=<PROJECT-ID>:<REGION>:<SQL-INSTANCE-ID>=tcp:3306<br />

### In Command Line connect to Cloud SQL<br />
- For windowsset SQLALCHEMY_DATABASE_URI=mysql+pymysql://<username>:<password>@127.0.0.1/<database-name><br />
- For Unixexport SQLALCHEMY_DATABASE_URI=mysql+pymysql://<username>:<password>@127.0.0.1/<database-name><br />

### Setting environment variables<br />
- set SECRET_KEY=<SECRET_KEY><br />
- set PRIVATE_KEY=<PRIVATE_KEY><br />
- set PUBLIC_KEY=<PUBLIC_KEY><br />
- set BUCKET_NAME=<BUCKET_NAME><br />
- set TASK_REVIEW_MAX_COUNT=3<br />
- set MIN_DAYS_BEFORE_FETCHING_TASK_FOR_REVIEW=1<br />

## RSA256 for JWT<br />
- Public and private keys taken from https://travistidwell.com/jsencrypt/demo/

