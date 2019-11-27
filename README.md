"# bobble-validation-backend" 

Allow connections to Cloud SQL (In directory holding Cloud_sql_proxy)
Cloud_sql_proxy -instances=<PROJECT-ID>:<REGION>:<SQL-INSTANCE-ID>=tcp:3306

In Command Line connect to Cloud SQL
#For windowsset SQLALCHEMY_DATABASE_URI=mysql+pymysql://<username>:<password>@127.0.0.1/<database-name>
#For Unixexport SQLALCHEMY_DATABASE_URI=mysql+pymysql://<username>:<password>@127.0.0.1/<database-name>