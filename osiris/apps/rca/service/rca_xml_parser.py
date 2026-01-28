from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterator, Optional
import xml.etree.ElementTree as ET

from .rca_norm import norm_text, parse_ddmmyyyy


@dataclass(frozen=True)
class OrgRow:
    code: str
    name: str
    full_name: str
    parent_code: Optional[str]
    is_top: bool


@dataclass(frozen=True)
class PostRow:
    code: str
    name: str


@dataclass(frozen=True)
class EmployeeRow:
    snils_raw: str
    tab_raw: str

    last_name: str
    first_name: str
    middle_name: Optional[str]

    date_of_birth: date

    org_code: str
    post_code: str

    state: str
    feature: str

    start_date: date
    fire_date: date

    vacation_start: Optional[date]
    vacation_end: Optional[date]

    gender: Optional[str]
    office_location: Optional[str]


def _text(parent: ET.Element, tag: str) -> Optional[str]:
    el = parent.find(tag)
    if el is None:
        return None
    return el.text


def parse_org(path: str) -> Iterator[OrgRow]:
    root = ET.parse(path).getroot()

    for org in root.findall(".//ORG"):
        code = norm_text(_text(org, "id")) or ""
        name = norm_text(_text(org, "Name")) or ""
        full_name = norm_text(_text(org, "fullName")) or name
        parent_code = norm_text(_text(org, "ParentCode"))
        is_top_txt = norm_text(_text(org, "Istop")) or "0"

        if not code or not name:
            continue

        yield OrgRow(
            code=code,
            name=name,
            full_name=full_name,
            parent_code=parent_code,
            is_top=(is_top_txt == "1"),
        )


def parse_post(path: str) -> Iterator[PostRow]:
    root = ET.parse(path).getroot()

    for post in root.findall(".//Post"):
        code = norm_text(_text(post, "id")) or ""
        name = norm_text(_text(post, "Name")) or ""
        if not code or not name:
            continue
        yield PostRow(code=code, name=name)


def parse_employee(path: str) -> Iterator[EmployeeRow]:
    root = ET.parse(path).getroot()

    for person in root.findall(".//Person"):
        snils_raw = norm_text(_text(person, "id")) or ""
        tab_raw = norm_text(_text(person, "Tab_id")) or ""

        last_name = norm_text(_text(person, "lastname")) or ""
        first_name = norm_text(_text(person, "firstname")) or ""
        middle_name = norm_text(_text(person, "middlename"))

        dob = parse_ddmmyyyy(_text(person, "dateofbirth"))
        org_code = norm_text(_text(person, "section")) or ""
        post_code = norm_text(_text(person, "position")) or ""

        state = norm_text(_text(person, "state")) or ""
        feature = norm_text(_text(person, "feature")) or ""

        start_date = parse_ddmmyyyy(_text(person, "startdate"))
        fire_date = parse_ddmmyyyy(_text(person, "firedate"))

        vacation_start = parse_ddmmyyyy(_text(person, "vacationstart"))
        vacation_end = parse_ddmmyyyy(_text(person, "vacationend"))

        gender = norm_text(_text(person, "gender"))
        office_location = norm_text(_text(person, "officelocation"))

        if not all(
            [
                snils_raw,
                tab_raw,
                last_name,
                first_name,
                dob,
                org_code,
                post_code,
                state,
                feature,
                start_date,
                fire_date,
            ]
        ):
            continue

        yield EmployeeRow(
            snils_raw=snils_raw,
            tab_raw=tab_raw,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            date_of_birth=dob,
            org_code=org_code,
            post_code=post_code,
            state=state,
            feature=feature,
            start_date=start_date,
            fire_date=fire_date,
            vacation_start=vacation_start,
            vacation_end=vacation_end,
            gender=gender,
            office_location=office_location,
        )
