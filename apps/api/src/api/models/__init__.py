# Import all models here so Alembic's autogenerate can detect them.
from api.models.company import Company as Company
from api.models.datacenter_site import DatacenterSite as DatacenterSite
from api.models.hardware_product import HardwareProduct as HardwareProduct
from api.models.metric import MetricPoint as MetricPoint
from api.models.metric import MetricSeries as MetricSeries
from api.models.refresh_token import RefreshToken as RefreshToken
from api.models.research_note import AuditLog as AuditLog
from api.models.research_note import NoteEntityLink as NoteEntityLink
from api.models.research_note import ResearchNote as ResearchNote
from api.models.source_document import IngestionRun as IngestionRun
from api.models.source_document import SourceDocument as SourceDocument
from api.models.source_document import SourceEntityLink as SourceEntityLink
from api.models.user import User as User
from api.models.user_invite import UserInvite as UserInvite
