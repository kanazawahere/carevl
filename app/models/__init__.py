from app.models.encounter import Encounter
from app.models.patient import Patient
from app.models.observation import Observation
from app.models.diagnostic_report import DiagnosticReport
from app.models.measure_report import MeasureReport
from app.models.system_config import SystemConfig

# This ensures all models are imported and registered with the Base
# so that Base.metadata.create_all() creates all tables.
