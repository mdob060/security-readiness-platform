from pydantic import BaseModel


class PciDssControlResult(BaseModel):
    requirement_code: str
    description: str
    check_type: str
    status: str  # pass, fail, unknown
    detail: str


class PciDssReport(BaseModel):
    compliance_percentage: float
    controls: list[PciDssControlResult]


class Fail2banJailStatus(BaseModel):
    jail: str
    currently_failed: int
    total_failed: int
    currently_banned: int
    total_banned: int
    banned_ips: list[str]


class CveChecklistItem(BaseModel):
    cve_id: str
    title: str
    severity: str
    note: str
