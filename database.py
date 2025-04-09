import os
import logging
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    logging.error("DATABASE_URL environment variable not set!")

# Create the SQLAlchemy engine
try:
    engine = create_engine(DATABASE_URL) if DATABASE_URL else None
    Base = declarative_base()
    metadata = MetaData()
except Exception as e:
    logging.error(f"Error initializing database engine: {str(e)}")
    engine = None
    Base = None
    metadata = None

# Define the grants table
class Grant(Base):
    __tablename__ = 'grants'
    
    id = Column(Integer, primary_key=True)
    grant_id = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    funder = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    award_amount = Column(Float, nullable=True)
    eligibility = Column(Text, nullable=True)
    link = Column(String(1024), nullable=True)
    source = Column(String(255), nullable=True)
    geography = Column(String(255), nullable=True)
    topic = Column(String(255), nullable=True)
    audience = Column(String(255), nullable=True)
    funder_type = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    def to_dict(self):
        return {
            "Grant ID": self.grant_id,
            "Title": self.title,
            "Funder": self.funder,
            "Description": self.description,
            "Start Date": self.start_date,
            "Deadline": self.deadline,
            "Award Amount": self.award_amount,
            "Eligibility": self.eligibility,
            "Link": self.link,
            "Source": self.source,
            "Geography": self.geography,
            "Topic": self.topic,
            "Audience": self.audience,
            "Funder Type": self.funder_type
        }


# Function to create all tables
def create_tables():
    """Create all database tables if they don't exist."""
    if engine is None:
        logging.error("Cannot create tables: database engine not initialized")
        return False
    
    try:
        Base.metadata.create_all(engine)
        logging.info("Database tables created successfully")
        return True
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
        return False


# Function to save grants to the database
def save_grants_to_db(grants_df):
    """
    Save grants from a DataFrame to the database.
    
    Args:
        grants_df (pandas.DataFrame): DataFrame containing grant data
        
    Returns:
        bool: True if successful, False otherwise
    """
    if engine is None:
        logging.error("Cannot save grants: database engine not initialized")
        return False
    
    if grants_df.empty:
        logging.warning("Empty DataFrame provided to save_grants_to_db")
        return False
    
    try:
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # First, create tables if they don't exist
        if not create_tables():
            return False
        
        # Map DataFrame columns to database columns
        column_mapping = {
            "Grant ID": "grant_id",
            "Title": "title",
            "Funder": "funder",
            "Description": "description",
            "Start Date": "start_date",
            "Deadline": "deadline",
            "Award Amount": "award_amount",
            "Eligibility": "eligibility",
            "Link": "link",
            "Source": "source",
            "Geography": "geography",
            "Topic": "topic",
            "Audience": "audience",
            "Funder Type": "funder_type"
        }
        
        # Convert DataFrame to list of dictionaries with DB column names
        grants_data = []
        for i, row in grants_df.iterrows():
            grant_dict = {}
            for df_col, db_col in column_mapping.items():
                if df_col in row:
                    # Handle NaT (Not a Time) values for dates
                    if pd.isna(row[df_col]) or (isinstance(row[df_col], pd.Timestamp) and pd.isnull(row[df_col])):
                        grant_dict[db_col] = None
                    else:
                        grant_dict[db_col] = row[df_col]
            grants_data.append(grant_dict)
        
        # Insert new grants
        for grant_data in grants_data:
            # Check if the grant already exists (by grant_id or title+funder combo)
            if "grant_id" in grant_data and grant_data["grant_id"]:
                existing_grant = session.query(Grant).filter_by(grant_id=grant_data["grant_id"]).first()
            else:
                existing_grant = session.query(Grant).filter_by(
                    title=grant_data["title"],
                    funder=grant_data["funder"]
                ).first()
            
            if existing_grant:
                # Update existing grant
                for key, value in grant_data.items():
                    setattr(existing_grant, key, value)
            else:
                # Create new grant
                new_grant = Grant(**grant_data)
                session.add(new_grant)
        
        # Commit the changes
        session.commit()
        session.close()
        
        logging.info(f"Successfully saved {len(grants_data)} grants to database")
        return True
        
    except Exception as e:
        logging.error(f"Error saving grants to database: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


# Function to load grants from the database
def load_grants_from_db():
    """
    Load grants from the database.
    
    Returns:
        pandas.DataFrame: DataFrame containing grant data, or empty DataFrame if error
    """
    if engine is None:
        logging.error("Cannot load grants: database engine not initialized")
        return pd.DataFrame()
    
    try:
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Query all grants
        grants = session.query(Grant).all()
        
        if not grants:
            logging.info("No grants found in database")
            session.close()
            return pd.DataFrame()
            
        # Convert to list of dictionaries
        grants_data = [grant.to_dict() for grant in grants]
        
        # Convert to DataFrame
        df = pd.DataFrame(grants_data)
        
        session.close()
        
        logging.info(f"Successfully loaded {len(df)} grants from database")
        return df
        
    except Exception as e:
        logging.error(f"Error loading grants from database: {str(e)}")
        if 'session' in locals():
            session.close()
        return pd.DataFrame()


# Initialize the database
def init_db():
    """Initialize the database by creating tables."""
    if create_tables():
        logging.info("Database initialized successfully")
        return True
    else:
        logging.error("Failed to initialize database")
        return False


# Check database connection
def check_db_connection():
    """Check if database connection is working."""
    if engine is None:
        logging.error("Database engine not initialized")
        return False
    
    try:
        connection = engine.connect()
        connection.close()
        logging.info("Database connection successful")
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        return False

# Initialize database when module is imported
if engine is not None:
    init_db()