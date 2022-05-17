from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
from clld.db.models import common


# -----------------------------------------------------------------------------
# specialized common mapper classes
# -----------------------------------------------------------------------------


@implementer(interfaces.IContribution)
class Inventory(CustomModelMixin, common.Contribution):
    pk = Column(Integer, ForeignKey("contribution.pk"), primary_key=True)
    language_pk = Column(String(32), ForeignKey("language.id"))
    language = relationship(common.Language, backref=backref("inventories"))
    inventory_type = Column(String(32))
    source = Column(String(256))
    bibtex = Column(String(256))
    comments = Column(String(1024))


@implementer(interfaces.ILanguage)
class Variety(CustomModelMixin, common.Language):
    id = Column(String(32), ForeignKey("language.id"), primary_key=True)
    family_id = Column(String(32), ForeignKey("variety.id"))
    family = relationship("Variety", foreign_keys=[family_id], remote_side=[id])
    parent_id = Column(String(32), ForeignKey("variety.id"))
    parent = relationship("Variety", foreign_keys=[parent_id], remote_side=[id])
    level = Column(String(32))
    macroarea = Column(String(64))
