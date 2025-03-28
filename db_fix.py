"""
Database fix script to update database schema and fix any constraint issues.
This is a one-time script to run after modifying models.py.
"""
from app import app, db
from models import Attendance, Student

def fix_db():
    """Fix the database schema after model changes"""
    print("Starting database fix...")
    
    with app.app_context():
        # Check for db connectivity
        try:
            # Run a simple query to verify connection
            db.session.execute("SELECT 1")
            print("Database connection successful")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
        
        # Update any inconsistent data
        try:
            # Find any Absent records with non-null time_in
            absent_records = Attendance.query.filter_by(status='Absent').all()
            fixed_count = 0
            
            for record in absent_records:
                if record.time_in is not None:
                    print(f"Fixing record ID {record.id} - Student ID {record.student_id}")
                    record.time_in = None
                    fixed_count += 1
            
            if fixed_count > 0:
                print(f"Fixed {fixed_count} records")
                db.session.commit()
            else:
                print("No records needed fixing")
                
            # Recreate tables - this will apply the nullable change
            try:
                db.create_all()
                print("Successfully recreated database tables")
                return True
            except Exception as e:
                print(f"Error recreating tables: {e}")
                db.session.rollback()
                return False
                
        except Exception as e:
            print(f"Error during database fix: {e}")
            db.session.rollback()
            return False
        
if __name__ == "__main__":
    # Run the fix
    if fix_db():
        print("Database fix completed successfully!")
    else:
        print("Database fix failed.")