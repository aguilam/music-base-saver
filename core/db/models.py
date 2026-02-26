from sqlmodel import (
    SQLModel,
    Field,
    create_engine,
    Session,
    select,
    Relationship,
    literal,
    delete,
)
from typing import List, Optional
from sqlalchemy import Column, JSON, Integer, ForeignKey, tuple_
from sqlalchemy.orm import selectinload


class Track(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    artist: List[str] = Field(default=[], sa_column=Column(JSON))
    length: int
    links: List["TrackLink"] = Relationship(
        back_populates="track", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class TrackLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    track_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("track.id", ondelete="CASCADE")),
    )
    link_type: str
    link_provider: str
    link: str
    track: Optional[Track] = Relationship(back_populates="links")


class DBManager:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///database.db")
        SQLModel.metadata.create_all(self.engine)

    def add_track(self, track: Track):
        with Session(self.engine) as session:
            session.add(track)
            session.commit()
            session.refresh(track)
            return track

    def delete_track(self, id: int):
        with Session(self.engine) as session:
            statement = select(Track).where(Track.id == id)
            track = session.exec(statement).first()
            session.delete(track)
            return track

    def bulk_delete_by_links(self, provider_link: list[tuple[str, str]]):
        with Session(self.engine) as session:
            select_ids = select(TrackLink.id, TrackLink.track_id).where(
                tuple_(TrackLink.link_provider, TrackLink.link).in_(provider_link)
            )
            ids_statement = session.exec(select_ids).all()
            links_ids = [r[0] for r in ids_statement]
            track_ids = [r[1] for r in ids_statement]
            delete_links_statement = delete(TrackLink).where(
                TrackLink.id.in_(links_ids)
            )
            session.exec(delete_links_statement)
            delete_tracks_statement = delete(Track).where(Track.id.in_(track_ids))
            tracks = session.exec(delete_tracks_statement)
            session.commit()
            return tracks.rowcount

    def get_all_tracks(self):
        with Session(self.engine) as session:
            statement = select(Track).options(selectinload(Track.links))
            tracks = session.exec(statement).all()
            return tracks

    def get_all_tracks_storage_links(self):
        with Session(self.engine) as session:
            combined = (
                TrackLink.link_provider + literal("///") + TrackLink.link
            ).label("combined")
            statement = select(combined).where(TrackLink.link_type == "storage")
            return set(session.exec(statement).all())

    def get_by_title(self, title: str):
        with Session(self.engine) as session:
            statement = select(Track).where(Track.title == title)
            track = session.exec(statement).first()
            return track

    def get_by_id(self, id: int):
        with Session(self.engine) as session:
            statement = (
                select(Track).where(Track.id == id).options(selectinload(Track.links))
            )
            track = session.exec(statement).first()
            return track
