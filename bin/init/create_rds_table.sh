cd `dirname $0`/../../src
python -c 'from database.sql_db.conn import create_rds_table; create_rds_table()'