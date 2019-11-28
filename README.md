"# bobble-validation-backend" 

Allow connections to Cloud SQL (In directory holding Cloud_sql_proxy)<br />
Cloud_sql_proxy -instances=<PROJECT-ID>:<REGION>:<SQL-INSTANCE-ID>=tcp:3306<br />

In Command Line connect to Cloud SQL<br />
#For windowsset SQLALCHEMY_DATABASE_URI=mysql+pymysql://<username>:<password>@127.0.0.1/<database-name><br />
#For Unixexport SQLALCHEMY_DATABASE_URI=mysql+pymysql://<username>:<password>@127.0.0.1/<database-name>