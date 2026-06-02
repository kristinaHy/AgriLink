import sqlite3
p='f:/backupofc/AgriLink/db.sqlite3'
conn=sqlite3.connect(p)
cur=conn.cursor()
cur.execute("PRAGMA table_info('notifications_notification')")
cols=cur.fetchall()
print('columns:')
for c in cols:
    print(c)
conn.close()
