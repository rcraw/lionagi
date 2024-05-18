from pydantic import Field, field_validator
from typing import Any
from lionagi.core.collections.abc import Component, get_lion_id, LionIDable, Condition
from lionagi.core.generic.edge_condition import EdgeCondition


class Edge(Component):
    """Represents a directed edge between two nodes in a graph."""

    head: str = Field(
        ...,
        title="Head",
        description="The identifier of the head node of the edge.",
    )

    tail: str = Field(
        ...,
        title="Out",
        description="The identifier of the tail node of the edge.",
    )

    condition: Condition | EdgeCondition | None = Field(
        default=None,
        description="Optional condition that must be met for the edge "
        "to be considered active.",
    )

    label: str | None = Field(
        default=None,
        description="An optional label for the edge.",
    )

    bundle: bool = Field(
        default=False,
        description="A flag indicating if the edge is bundled.",
    )

    async def check_condition(self, obj: Any) -> bool:
        """Check if the edge condition is met for the given object."""
        if not self.condition:
            raise ValueError("The condition for the edge is not set.")
        check = await self.condition.applies(obj)
        return check

    @field_validator("head", "tail", mode="before")
    def _validate_head_tail(cls, value):
        """Validate the head and tail fields."""
        return get_lion_id(value)

    def __len__(self):
        """Return the length of the edge (always 1)."""
        return 1

    def __contains__(self, item: LionIDable) -> bool:
        """Check if the given item is the head or tail of the edge."""
        return get_lion_id(item) in (self.head, self.tail)
