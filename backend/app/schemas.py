from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class RecordStatus(str, Enum):
    Active = "Active"
    Inactive = "Inactive"


# Keep alias used by currency router
CurrencyStatus = RecordStatus


class CurrencyCreate(BaseModel):
    currency_name: str = Field(..., min_length=1, max_length=100)
    status: RecordStatus = RecordStatus.Active


class CurrencyUpdate(BaseModel):
    currency_name: str = Field(..., min_length=1, max_length=100)
    status: RecordStatus


class CurrencyOut(BaseModel):
    currency_id: int
    currency_name: str
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CountryCreate(BaseModel):
    country_name: str = Field(..., min_length=1, max_length=100)
    country_code: str = Field(..., min_length=1, max_length=10)
    currency_id: int
    status: RecordStatus = RecordStatus.Active


class CountryUpdate(BaseModel):
    country_name: str = Field(..., min_length=1, max_length=100)
    country_code: str = Field(..., min_length=1, max_length=10)
    currency_id: int
    status: RecordStatus


class CountryOut(BaseModel):
    country_id: int
    country_name: str
    country_code: str
    currency_id: int
    currency_name: str | None = None
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StateCreate(BaseModel):
    state_name: str = Field(..., min_length=1, max_length=100)
    country_id: int
    cgst_percent: float = Field(..., ge=0, le=100)
    sgst_percent: float = Field(..., ge=0, le=100)
    igst_percent: float = Field(..., ge=0, le=100)
    status: RecordStatus = RecordStatus.Active


class StateUpdate(BaseModel):
    state_name: str = Field(..., min_length=1, max_length=100)
    country_id: int
    cgst_percent: float = Field(..., ge=0, le=100)
    sgst_percent: float = Field(..., ge=0, le=100)
    igst_percent: float = Field(..., ge=0, le=100)
    status: RecordStatus


class StateOut(BaseModel):
    state_id: int
    state_name: str
    country_id: int
    country_name: str | None = None
    cgst_percent: float
    sgst_percent: float
    igst_percent: float
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RegionCreate(BaseModel):
    region_name: str = Field(..., min_length=1, max_length=100)
    state_id: int
    status: RecordStatus = RecordStatus.Active


class RegionUpdate(BaseModel):
    region_name: str = Field(..., min_length=1, max_length=100)
    state_id: int
    status: RecordStatus


class RegionOut(BaseModel):
    region_id: int
    region_name: str
    state_id: int
    state_name: str | None = None
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RouteCreate(BaseModel):
    route_code: str = Field(..., min_length=1, max_length=50)
    region_id: int
    status: RecordStatus = RecordStatus.Active


class RouteUpdate(BaseModel):
    route_code: str = Field(..., min_length=1, max_length=50)
    region_id: int
    status: RecordStatus


class RouteOut(BaseModel):
    route_id: int
    route_code: str
    region_id: int
    region_name: str | None = None
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PlaceCreate(BaseModel):
    place_name: str = Field(..., min_length=1, max_length=100)
    region_id: int
    status: RecordStatus = RecordStatus.Active


class PlaceUpdate(BaseModel):
    place_name: str = Field(..., min_length=1, max_length=100)
    region_id: int
    status: RecordStatus


class PlaceOut(BaseModel):
    place_id: int
    place_name: str
    region_id: int
    region_name: str | None = None
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SectionCreate(BaseModel):
    section_name: str = Field(..., min_length=1, max_length=100)
    status: RecordStatus = RecordStatus.Active


class SectionUpdate(BaseModel):
    section_name: str = Field(..., min_length=1, max_length=100)
    status: RecordStatus


class SectionOut(BaseModel):
    section_id: int
    section_name: str
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BranchTypeCreate(BaseModel):
    branch_type_name: str = Field(..., min_length=1, max_length=100)
    work_collection: bool = False
    case_study: bool = False
    production: bool = False
    qc: bool = False
    billing: bool = False
    transportation: bool = False
    payment_collection: bool = False
    status: RecordStatus = RecordStatus.Active


class BranchTypeUpdate(BaseModel):
    branch_type_name: str = Field(..., min_length=1, max_length=100)
    work_collection: bool = False
    case_study: bool = False
    production: bool = False
    qc: bool = False
    billing: bool = False
    transportation: bool = False
    payment_collection: bool = False
    status: RecordStatus


class WorkType(str, Enum):
    Work = "Work"
    Application = "Application"


class WorkStage(str, Enum):
    SingleStage = "Single Stage"
    MultiStage = "Multi Stage"


class WorkCreate(BaseModel):
    work_name: str = Field(..., min_length=1, max_length=100)
    work_type: WorkType
    stage: WorkStage
    production_time: int = Field(..., ge=0, le=9999)
    section_id: int
    status: RecordStatus = RecordStatus.Active
    existing_id: int | None = None


class WorkUpdate(BaseModel):
    work_name: str = Field(..., min_length=1, max_length=100)
    work_type: WorkType
    stage: WorkStage
    production_time: int = Field(..., ge=0, le=9999)
    section_id: int
    status: RecordStatus
    existing_id: int | None = None


class WorkOut(BaseModel):
    work_id: int
    work_name: str
    work_type: WorkType
    stage: WorkStage
    production_time: int
    section_id: int | None = None
    section_name: str | None = None
    status: RecordStatus
    existing_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class QualityTypeCreate(BaseModel):
    quality_name: str = Field(..., min_length=1, max_length=100)
    status: RecordStatus = RecordStatus.Active


class QualityTypeUpdate(BaseModel):
    quality_name: str = Field(..., min_length=1, max_length=100)
    status: RecordStatus


class QualityTypeOut(BaseModel):
    quality_type_id: int
    quality_name: str
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BranchTypeOut(BaseModel):
    branch_type_id: int
    branch_type_name: str
    work_collection: bool
    case_study: bool
    production: bool
    qc: bool
    billing: bool
    transportation: bool
    payment_collection: bool
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CompanyOut(BaseModel):
    company_id: int
    company_name: str
    company_code: str
    address: str
    address2: str | None = None
    place_id: int
    place_name: str | None = None
    region_id: int
    region_name: str | None = None
    state_id: int
    state_name: str | None = None
    country_id: int
    country_name: str | None = None
    pin: str
    phone: str | None = None
    mobile: str | None = None
    email: str | None = None
    whatsapp_no: str | None = None
    gst_no: str | None = None
    ie_code: str | None = None
    iso_number: str | None = None
    logo_path: str | None = None
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BranchCreate(BaseModel):
    parent_company_id: int
    branch_type_id: int
    branch_name: str = Field(..., min_length=1, max_length=150)
    address1: str = Field(..., min_length=1, max_length=255)
    address2: str | None = Field(None, max_length=255)
    place_id: int
    pin: str = Field(..., min_length=1, max_length=20)
    state_id: int
    country_id: int
    phone: str | None = Field(None, max_length=30)
    mobile: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=150)
    whatsapp_no: str | None = Field(None, max_length=30)
    gst_no: str | None = Field(None, max_length=50)
    distribution_id: int | None = None
    iso_number: str | None = Field(None, max_length=50)
    ie_code: str | None = Field(None, max_length=50)
    status: RecordStatus = RecordStatus.Active


class BranchUpdate(BaseModel):
    parent_company_id: int
    branch_type_id: int
    branch_name: str = Field(..., min_length=1, max_length=150)
    address1: str = Field(..., min_length=1, max_length=255)
    address2: str | None = Field(None, max_length=255)
    place_id: int
    pin: str = Field(..., min_length=1, max_length=20)
    state_id: int
    country_id: int
    phone: str | None = Field(None, max_length=30)
    mobile: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=150)
    whatsapp_no: str | None = Field(None, max_length=30)
    gst_no: str | None = Field(None, max_length=50)
    distribution_id: int | None = None
    iso_number: str | None = Field(None, max_length=50)
    ie_code: str | None = Field(None, max_length=50)
    status: RecordStatus


class BranchOut(BaseModel):
    branch_id: int
    parent_company_id: int
    parent_company_name: str | None = None
    branch_type_id: int
    branch_type_name: str | None = None
    branch_name: str
    address1: str
    address2: str | None = None
    place_id: int
    place_name: str | None = None
    region_id: int
    region_name: str | None = None
    state_id: int
    state_name: str | None = None
    country_id: int
    country_name: str | None = None
    pin: str
    phone: str | None = None
    mobile: str | None = None
    email: str | None = None
    whatsapp_no: str | None = None
    gst_no: str | None = None
    distribution_id: int | None = None
    distribution_name: str | None = None
    iso_number: str | None = None
    ie_code: str | None = None
    status: RecordStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CustomerCreate(BaseModel):
    branch_name: str = Field(..., min_length=1, max_length=150)
    contact_person: str | None = Field(None, max_length=150)
    address: str = Field(..., min_length=1, max_length=255)
    address1: str | None = Field(None, max_length=255)
    place_id: int
    route_id: int
    region_id: int
    state_id: int
    country_id: int
    currency_id: int
    distribution_id: int
    linked_branch_id: int
    gst_no: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=30)
    mobile: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=150)
    whatsapp_no: str | None = Field(None, max_length=30)
    current_balance: float = 0
    inclusive_tax: bool = False
    remarks: str | None = Field(None, max_length=500)


class CustomerUpdate(BaseModel):
    branch_name: str = Field(..., min_length=1, max_length=150)
    contact_person: str | None = Field(None, max_length=150)
    address: str = Field(..., min_length=1, max_length=255)
    address1: str | None = Field(None, max_length=255)
    place_id: int
    route_id: int
    region_id: int
    state_id: int
    country_id: int
    currency_id: int
    distribution_id: int
    linked_branch_id: int
    gst_no: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=30)
    mobile: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=150)
    whatsapp_no: str | None = Field(None, max_length=30)
    current_balance: float = 0
    inclusive_tax: bool = False
    remarks: str | None = Field(None, max_length=500)
    head_office_id: int | None = None
    billing_office_id: int | None = None


class CustomerOut(BaseModel):
    customer_id: int
    branch_name: str
    contact_person: str | None = None
    address: str
    address1: str | None = None
    place_id: int
    place_name: str | None = None
    route_id: int
    route_code: str | None = None
    region_id: int
    region_name: str | None = None
    state_id: int
    state_name: str | None = None
    country_id: int
    country_name: str | None = None
    currency_id: int
    currency_name: str | None = None
    distribution_id: int
    distribution_name: str | None = None
    linked_branch_id: int
    linked_branch_name: str | None = None
    gst_no: str | None = None
    phone: str | None = None
    mobile: str | None = None
    email: str | None = None
    whatsapp_no: str | None = None
    current_balance: float
    inclusive_tax: bool
    remarks: str | None = None
    head_office_id: int | None = None
    head_office_name: str | None = None
    billing_office_id: int | None = None
    billing_office_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SchedulerWorkType(str, Enum):
    New = "New"
    Repeat = "Repeat"


class ArchType(str, Enum):
    Upper = "Upper"
    Lower = "Lower"
    Both = "Both"


class SchedulerDetailIn(BaseModel):
    scheduler_detail_id: int | None = None
    work_id: int
    patient_name: str = Field(..., min_length=1, max_length=150)
    arch: ArchType
    quality_type_id: int
    additional_requirements: str | None = Field(None, max_length=500)
    rate: float = Field(0, ge=0)
    qty: float = Field(1, ge=0)
    extra_charge: float = Field(0, ge=0)
    discount: float = Field(0, ge=0)
    final_rate: float = Field(0, ge=0)
    remarks: str | None = Field(None, max_length=500)


class SchedulerDetailOut(BaseModel):
    scheduler_detail_id: int
    scheduler_id: int
    sl_no: int
    work_no: str
    work_id: int
    work_name: str | None = None
    patient_name: str
    arch: ArchType
    quality_type_id: int
    quality_name: str | None = None
    additional_requirements: str | None = None
    rate: float
    qty: float
    extra_charge: float
    discount: float
    final_rate: float
    remarks: str | None = None
    has_case: bool = False
    case_approval_status: str | None = None


class SchedulerCreate(BaseModel):
    customer_id: int
    billing_party_id: int
    sending_party_id: int
    work_type: SchedulerWorkType = SchedulerWorkType.New
    work_received_date: date
    completion_date: date
    details: list[SchedulerDetailIn] = Field(default_factory=list)


class SchedulerUpdate(BaseModel):
    customer_id: int
    billing_party_id: int
    sending_party_id: int
    work_type: SchedulerWorkType
    work_received_date: date
    completion_date: date
    details: list[SchedulerDetailIn] = Field(default_factory=list)


class SchedulerOut(BaseModel):
    scheduler_id: int
    customer_id: int
    customer_name: str | None = None
    route_id: int
    route_code: str | None = None
    fin_year: str
    order_no: int
    mdo_code: str
    billing_party_id: int
    billing_party_name: str | None = None
    sending_party_id: int
    sending_party_name: str | None = None
    work_type: SchedulerWorkType
    work_received_date: date
    completion_date: date
    details: list[SchedulerDetailOut] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SchedulerNextCodeOut(BaseModel):
    route_id: int
    route_code: str
    fin_year: str
    order_no: int
    mdo_code: str


class SexType(str, Enum):
    M = "M"
    F = "F"


class StlModelQuality(str, Enum):
    Good = "Good"
    Bad = "Bad"


class TypeOfPlan(str, Enum):
    BothArch = "BOTH ARCH"
    UpperArchOnly = "UPPER ARCH ONLY"
    LowerArchOnly = "LOWER ARCH ONLY"


class TypeOfCaseStudy(str, Enum):
    CasualReport = "CASUAL REPORT"
    VideoReport = "VIDEO REPORT"


class AllergyType(str, Enum):
    Plastic = "PLASTIC"
    Metal = "METAL"
    Latex = "LATEX"
    Food = "FOOD"
    Medication = "MEDICATION"


class CaseFileKind(str, Enum):
    extra_oral = "extra_oral"
    intra_oral = "intra_oral"
    ceph = "ceph"
    opg = "opg"
    video = "video"
    concern_video = "concern_video"


class CaseFileOut(BaseModel):
    file_id: int
    scheduler_detail_id: int
    file_kind: CaseFileKind
    file_path: str
    original_name: str | None = None
    content_type: str | None = None


class CaseStudyIn(BaseModel):
    working_doctor_name: str | None = Field(None, max_length=150)
    clinic_name: str | None = Field(None, max_length=150)
    mobile_no: str | None = Field(None, max_length=30)
    email_id: str | None = Field(None, max_length=150)
    patient_name: str | None = Field(None, max_length=150)
    age: str | None = Field(None, max_length=20)
    sex: SexType | None = None
    patient_availability: str | None = Field(None, max_length=255)
    next_appointment_date: date | None = None
    stl_model_quality: StlModelQuality | None = None
    chief_complaint: str | None = Field(None, max_length=1000)
    other_concerns: str | None = Field(None, max_length=1000)
    type_of_plan: TypeOfPlan | None = None
    type_of_case_study: TypeOfCaseStudy | None = None
    suggestions_from_doctor: str | None = Field(None, max_length=1000)
    deciduous_tooth: str | None = Field(None, max_length=255)
    rotation: str | None = Field(None, max_length=255)
    molar_relation: str | None = Field(None, max_length=255)
    overjet: str | None = Field(None, max_length=255)
    overbite: str | None = Field(None, max_length=255)
    missing_teeth: str | None = Field(None, max_length=255)
    midline_shift: str | None = Field(None, max_length=255)
    crossbite: str | None = Field(None, max_length=255)
    arch_shape: str | None = Field(None, max_length=255)
    deepbite: str | None = Field(None, max_length=255)
    open_bite: str | None = Field(None, max_length=255)
    spacing: str | None = Field(None, max_length=255)
    caries_decay_root_stump: str | None = Field(None, max_length=255)
    impaction: str | None = Field(None, max_length=255)
    periodontal_status: str | None = Field(None, max_length=255)
    extraction: str | None = Field(None, max_length=255)
    rct: str | None = Field(None, max_length=255)
    crown_bridge_implant: str | None = Field(None, max_length=255)
    tongue_thrusting: bool = False
    bruxism: str | None = Field(None, max_length=255)
    mouth_breathing: bool = False
    thumb_sucking: bool = False
    lip_biting: bool = False
    medications: str | None = None
    allergies: AllergyType | None = None
    remarks: str | None = Field(None, max_length=1000)


class CaseApprovalStatus(str, Enum):
    Pending = "Pending"
    Approved = "Approved"


class CaseStudyOut(CaseStudyIn):
    exists: bool = False
    case_id: int | None = None
    scheduler_detail_id: int
    work_no: str | None = None
    approval_status: CaseApprovalStatus = CaseApprovalStatus.Pending
    approved_at: datetime | None = None
    files: dict[str, list[CaseFileOut]] = Field(default_factory=dict)


class DistributionDetailIn(BaseModel):
    work_id: int
    prime_rate: float = Field(0, ge=0)
    supreme_rate: float = Field(0, ge=0)
    supreme_plus_rate: float = Field(0, ge=0)
    collection_charge: float = Field(0, ge=0)
    collection_percentage: float = Field(0, ge=0, le=100)


class DistributionDetailOut(BaseModel):
    distribution_detail_id: int
    distribution_id: int
    work_id: int
    work_name: str | None = None
    prime_rate: float
    supreme_rate: float
    supreme_plus_rate: float
    collection_charge: float
    collection_percentage: float


class DistributionCreate(BaseModel):
    distribution_name: str = Field(..., min_length=1, max_length=150)
    section_id: int
    currency_id: int
    company_id: int
    effective_from: date
    effective_to: date
    status: RecordStatus = RecordStatus.Active
    details: list[DistributionDetailIn] = Field(default_factory=list)


class DistributionUpdate(BaseModel):
    distribution_name: str = Field(..., min_length=1, max_length=150)
    section_id: int
    currency_id: int
    company_id: int
    effective_from: date
    effective_to: date
    status: RecordStatus
    details: list[DistributionDetailIn] = Field(default_factory=list)


class DistributionOut(BaseModel):
    distribution_id: int
    distribution_name: str
    section_id: int
    section_name: str | None = None
    currency_id: int
    currency_name: str | None = None
    company_id: int
    company_name: str | None = None
    effective_from: date
    effective_to: date
    status: RecordStatus
    details: list[DistributionDetailOut] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
