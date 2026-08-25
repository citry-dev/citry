from __future__ import annotations

from dataclasses import dataclass, replace
from threading import RLock


@dataclass(frozen=True, slots=True)
class Team:
    id: int
    department: str
    name: str


@dataclass(frozen=True, slots=True)
class Contact:
    id: int
    name: str
    email: str
    team_id: int


@dataclass(frozen=True, slots=True)
class ContactView:
    id: int
    name: str
    email: str
    team_id: int
    team_name: str
    detail_url: str
    edit_url: str


DEPARTMENTS = (
    ("engineering", "Engineering"),
    ("design", "Design"),
    ("operations", "Operations"),
)

TEAMS = (
    Team(1, "engineering", "Platform"),
    Team(2, "engineering", "Developer Experience"),
    Team(7, "engineering", "Infrastructure"),
    Team(8, "engineering", "Security"),
    Team(3, "design", "Product Design"),
    Team(4, "design", "Research"),
    Team(5, "operations", "Customer Operations"),
)

_INITIAL_CONTACTS = (
    Contact(1, "Ada Lovelace", "ada@example.test", 1),
    Contact(2, "Grace Hopper", "grace@example.test", 2),
    Contact(3, "Margaret Hamilton", "margaret@example.test", 3),
    Contact(4, "Edsger Dijkstra", "edsger@example.test", 1),
    Contact(5, "Annie Easley", "annie@example.test", 5),
    Contact(6, "Radia Perlman", "radia@example.test", 2),
)

_lock = RLock()
_contacts = {contact.id: contact for contact in _INITIAL_CONTACTS}


def reset_contacts() -> None:
    with _lock:
        _contacts.clear()
        _contacts.update((contact.id, contact) for contact in _INITIAL_CONTACTS)


def list_teams(department: str | None = None) -> tuple[Team, ...]:
    if department is None:
        return TEAMS
    return tuple(team for team in TEAMS if team.department == department)


def get_team(team_id: int) -> Team:
    for team in TEAMS:
        if team.id == team_id:
            return team
    raise KeyError(team_id)


def _as_view(contact: Contact) -> ContactView:
    team = get_team(contact.team_id)
    return ContactView(
        id=contact.id,
        name=contact.name,
        email=contact.email,
        team_id=contact.team_id,
        team_name=team.name,
        detail_url=f"/fragments/contacts/{contact.id}",
        edit_url=f"/fragments/contacts/{contact.id}/edit",
    )


def get_contact(contact_id: int) -> ContactView:
    with _lock:
        try:
            contact = _contacts[contact_id]
        except KeyError as error:
            raise KeyError(contact_id) from error
        return _as_view(contact)


def search_contacts(query: str = "") -> tuple[ContactView, ...]:
    needle = query.strip().casefold()
    with _lock:
        contacts = tuple(_contacts.values())

    views = tuple(_as_view(contact) for contact in contacts)
    if not needle:
        return views
    return tuple(
        contact for contact in views if needle in " ".join((contact.name, contact.email, contact.team_name)).casefold()
    )


def update_contact(contact_id: int, *, name: str, email: str, team_id: int) -> ContactView:
    get_team(team_id)
    with _lock:
        try:
            current = _contacts[contact_id]
        except KeyError as error:
            raise KeyError(contact_id) from error
        updated = replace(current, name=name, email=email, team_id=team_id)
        _contacts[contact_id] = updated
        return _as_view(updated)
