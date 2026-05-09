import sqlite3

def check_wishlist():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    print("Columns in core_wishlist:")
    cursor.execute("PRAGMA table_info(core_wishlist)")
    for col in cursor.fetchall():
        print(col)
        
    print("\nColumns in core_wishlist_products:")
    cursor.execute("PRAGMA table_info(core_wishlist_products)")
    for col in cursor.fetchall():
        print(col)
        
    conn.close()

if __name__ == "__main__":
    check_wishlist()
