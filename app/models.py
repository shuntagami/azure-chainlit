# Keep the original imports
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.services.database import Base

# Models below are kept unchanged from the original file
# Simply move database Base reference to the new location