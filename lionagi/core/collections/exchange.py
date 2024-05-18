from typing import TypeVar, Generic
from .abc import Element, Field, Sendable
from .pile import Pile, pile
from .progression import Progression, progression

T = TypeVar("T")


class Exchange(Element, Generic[T]):
    """
    Item exchange system designed to handle incoming and outgoing flows of items
    """

    pile: Pile[T] = Field(
        default_factory=lambda: pile(),
        description="The pile of items in the exchange.",
        title="pending items",
    )

    pending_ins: dict[str, Progression] = Field(
        default_factory=dict,
        description="The pending incoming items to the exchange.",
        title="pending incoming items",
        examples=["{'sender_id': Progression}"],
    )

    pending_outs: Progression = progression()

    def __contains__(self, item):
        return item in self.pile

    def exclude(self, item):
        return (
            self.pile.exclude(item)
            and all([v.exclude(item) for v in self.pending_ins.values()])
            and self.pending_outs.exclude(item)
        )

    def include(self, item, direction):
        if self.pile.include(item):
            item = self.pile[item]
            item = [item] if not isinstance(item, list) else item
            for i in item:
                if not self._include(i, direction):
                    return False
            return True

    def _include(self, item: Sendable, direction):
        if direction == "in":
            if item.sender not in self.pending_ins:
                self.pending_ins[item.sender] = progression()
            return self.pile.include(item) and self.pending_ins[item.sender].include(
                item
            )

        return self.pile.include(item) and self.pending_outs.include(item)

    def to_dict(self):
        return self.model_dump(by_alias=True)