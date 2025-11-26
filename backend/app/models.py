from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field


# -------- User models --------

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    is_admin: bool = True
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: str
    username: str
    email: EmailStr
    is_admin: bool
    is_active: bool

class UserSelfRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    captcha_a: int
    captcha_b: int
    captcha_result: int


# -------- Family models --------

class FamilyBase(BaseModel):
    name: str = Field(..., description="Human readable name, e.g. 'Juniper A3'")
    test_cycle_time_hours: float = Field(..., gt=0, description="Testing cycle time in hours for a single unit")


class FamilyCreate(FamilyBase):
    pass


class FamilyUpdate(BaseModel):
    name: Optional[str] = None
    test_cycle_time_hours: Optional[float] = Field(None, gt=0)


class FamilyPublic(FamilyBase):
    id: str
    created_by_user_id: str
    created_at: datetime
    created_by_email: Optional[EmailStr] = None   # 👈 nuevo campo



# -------- Analytics models --------

class AnalyticsCreate(BaseModel):
    family_id: str
    sku: Optional[str] = None
    quantity: int = Field(..., gt=0)
    capacity_slots: int = Field(..., gt=0, description="Number of test slots available")
    manpower_qty: int = Field(..., gt=0, description="Number of technicians available")
    units_per_manpower_per_day: int = Field(..., gt=0, description="Units each technician can process per day")
    fecha_release: datetime = Field(..., description="Target datetime when last unit must be released to next station")


class AnalyticsPublic(BaseModel):
    id: str
    family_id: str
    sku: Optional[str]
    quantity: int
    capacity_slots: int
    manpower_qty: int
    units_per_manpower_per_day: int
    fecha_release: datetime

    test_cycle_time_hours: float
    bottleneck_type: Literal["equipment", "manpower"]
    equipment_capacity_units_per_day: float
    manpower_capacity_units_per_day: float
    throughput_units_per_hour: float
    input_cycle_time_hours: float
    input_cycle_time_minutes: float
    total_duration_hours: float
    first_unit_datetime: datetime
    is_feasible: bool

    created_by_user_id: str
    created_at: datetime



class AnalyticsPublic(BaseModel):
    id: str
    family_id: str
    sku: Optional[str]
    quantity: int
    capacity_slots: int
    manpower_qty: int
    units_per_manpower_per_day: int
    fecha_release: datetime

    test_cycle_time_hours: float
    bottleneck_type: Literal["equipment", "manpower"]
    equipment_capacity_units_per_day: float
    manpower_capacity_units_per_day: float
    throughput_units_per_hour: float
    input_cycle_time_hours: float
    input_cycle_time_minutes: float
    total_duration_hours: float
    first_unit_datetime: datetime
    is_feasible: bool

    created_by_user_id: str
    created_at: datetime

    # 👇 NUEVOS
    created_by_email: Optional[EmailStr] = None
    family_name: Optional[str] = None
