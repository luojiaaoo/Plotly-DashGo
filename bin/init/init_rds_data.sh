cd `dirname $0`/../../src
python -c 'from database.sql_db.conn import init_rds_data; init_rds_data()'