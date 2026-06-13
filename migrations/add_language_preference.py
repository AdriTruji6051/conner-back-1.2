"""
Migration script to add language_preference column to users table
Run this script to add language support to the Conner POS system
"""
import sqlite3
import os
import sys
from datetime import datetime

def migrate():
    """Add language_preference column to users table"""
    # Get database path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, '..', 'db', 'conner.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking if migration is needed...")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'language_preference' in columns:
            print("✅ Column 'language_preference' already exists. Migration not needed.")
            return True
        
        print("📝 Adding 'language_preference' column to users table...")
        
        # Add the column with default value
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN language_preference TEXT DEFAULT 'es-MX'
        """)
        
        # Update existing users to have default language (Spanish)
        cursor.execute("""
            UPDATE users 
            SET language_preference = 'es-MX' 
            WHERE language_preference IS NULL
        """)
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'language_preference' not in columns:
            raise Exception("Column was not added successfully")
        
        # Count affected rows
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print(f"   - Added 'language_preference' column to users table")
        print(f"   - Updated {user_count} existing user(s) with default language (es-MX)")
        print(f"   - Migration timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()


def rollback():
    """Rollback the migration (remove language_preference column)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, '..', 'db', 'conner.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking if rollback is needed...")
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'language_preference' not in columns:
            print("✅ Column 'language_preference' does not exist. Rollback not needed.")
            return True
        
        print("⚠️  SQLite does not support DROP COLUMN directly.")
        print("    To rollback, you need to:")
        print("    1. Create a new table without the column")
        print("    2. Copy data from old table")
        print("    3. Drop old table")
        print("    4. Rename new table")
        print("\n    This is a destructive operation. Please backup your database first.")
        
        response = input("\n    Do you want to proceed with rollback? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Rollback cancelled by user")
            return False
        
        print("📝 Performing rollback...")
        
        # Create new table without language_preference
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL UNIQUE,
                user_name TEXT NOT NULL,
                password TEXT NOT NULL,
                role_type TEXT NOT NULL
            )
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO users_new (id, user, user_name, password, role_type)
            SELECT id, user, user_name, password, role_type
            FROM users
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE users")
        
        # Rename new table
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        conn.commit()
        
        print("✅ Rollback completed successfully!")
        print(f"   - Removed 'language_preference' column from users table")
        print(f"   - Rollback timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Conner POS - Language Support Migration")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        success = rollback()
    else:
        success = migrate()
    
    print()
    print("=" * 60)
    
    sys.exit(0 if success else 1)
