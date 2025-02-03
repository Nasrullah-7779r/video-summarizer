# telemetry.py

import os
from applicationinsights import TelemetryClient
from dotenv import load_dotenv

load_dotenv()

INSTRUMENTATION_KEY = os.environ.get("INSTRUMENTATION_KEY")
if not INSTRUMENTATION_KEY:
    raise ValueError("INSTRUMENTATION_KEY not found in environment variables")

# Create a TelemetryClient instance
tc = TelemetryClient(INSTRUMENTATION_KEY)

def record_exception():
    """
    Record an exception to Application Insights.
    """
    tc.track_exception()  # Automatically captures the current exception info
    tc.flush()

def record_message(message: str, severity: str = "Information", properties: dict = None):
    """
    Record a trace message to Application Insights.
    
    Parameters:
      message: The message string to record.
      severity: One of "Verbose", "Information", "Warning", "Error", or "Critical".
      properties: Optional dictionary of custom properties.
    """
    tc.track_trace(message, severity=severity, properties=properties)
    tc.flush()
