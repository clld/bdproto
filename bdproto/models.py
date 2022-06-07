from zope.interface import implementer
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy import func, select
from sqlalchemy.orm import relationship
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
    language_pk = Column(String(32), ForeignKey("variety.id"))
    language = relationship("Variety", back_populates="inventories")
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
    inventories = relationship("Inventory", back_populates="language")
    inventories_count = Column(Integer())


@implementer(interfaces.IParameter)
class Segment(CustomModelMixin, common.Parameter):
    id = Column(String(128), ForeignKey("parameter.id"), primary_key=True)
    in_inventories = Column(Integer, default=0)
    total_inventories = Column(Integer)

    @hybrid_property
    def inv_representation(self):
        return self.in_inventories / self.total_inventories
