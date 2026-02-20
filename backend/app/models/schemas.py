from dataclasses import dataclass, field


@dataclass
class ExtractedLineItem:
    item: str
    quantity: float
    currency: str
    list_unit_price: float
    net_unit_price: float
    sku: str | None = None
    discount_percent: float | None = None
    contract_start: str | None = None
    contract_end: str | None = None


@dataclass
class ExtractedDocument:
    internal_id: str
    items: list[ExtractedLineItem]
    title: str = "Quotation"
    currency: str = "USD"
    date: str | None = None
    reseller: str | None = None
    reseller_contact: str | None = None
    expires: str | None = None
    expected_close: str | None = None
    end_user: str | None = None
    business_unit: str = "Spain"
    location: str | None = None
    serial_supported: str | None = None
    rebate: str | None = None
    opportunity: str | None = None
