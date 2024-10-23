import mysql.connector.pooling
from config.dash_melon_conf import SqlDbConf

config = {
    'host': SqlDbConf.HOST,
    'port': SqlDbConf.PORT,
    'user': SqlDbConf.USER,
    'password': SqlDbConf.PASSWORD,
    'database': SqlDbConf.DATABASE,
    'charset': SqlDbConf.CHARSET,
    'pool_size': SqlDbConf.POOL_SIZE,
}
pool = mysql.connector.pooling.MySQLConnectionPool(**config)

if __name__ == '__main__':
    conn = pool.get_connection()
    cursor = conn.cursor()

    # 执行SQL查询
    query = 'SELECT * FROM sys_user'
    cursor.execute(query)

    # 获取查询结果
    result = cursor.fetchall()
    print(result)

    # 关闭连接
    cursor.close()
    conn.close()

    # 获取连接
    con = pool.get_connection()
    con.start_transaction()
    cursor = con.cursor()
    sql = 'UPDATE t_emp SET sal=sal+%s WHERE deptno=%s'
    cursor.execute(sql, (200, 20))
    con.commit()
