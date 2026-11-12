from database import initialize_database


def main():
    # Create or update the database table while preserving existing records.
    initialize_database()
    print("Database and table created successfully!")


if __name__ == "__main__":
    main()
