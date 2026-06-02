import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrilink_project.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    print('tables:', [t.name for t in connection.introspection.get_table_list(cursor)])
    try:
        desc = connection.introspection.get_table_description(cursor, 'notifications_notification')
        print('description:')
        for d in desc:
            print(d)
    except Exception as e:
        print('error getting description:', e)
