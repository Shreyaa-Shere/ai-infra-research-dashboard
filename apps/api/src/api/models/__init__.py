# Import all models here so Alembic's autogenerate can detect them.
from api.models.user import User as User
from api.models.refresh_token import RefreshToken as RefreshToken
from api.models.company import Company as Company
from api.models.hardware_product import HardwareProduct as HardwareProduct
from api.models.datacenter_site import DatacenterSite as DatacenterSite
from api.models.research_note import ResearchNote as ResearchNote
from api.models.research_note import NoteEntityLink as NoteEntityLink
from api.models.research_note import AuditLog as AuditLog
