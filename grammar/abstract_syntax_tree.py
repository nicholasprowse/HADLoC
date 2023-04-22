import json
from typing import Self, TypeVar, Generic

T = TypeVar('T')


class ASTNode(Generic[T]):
    def __init__(self, node_type: str, value: T | None = None):
        self.children = []
        self.node_type = node_type
        self.value = value

    def add_child(self, child: Self):
        if child.node_type is not None:
            self.children.append(child)
        else:
            for c in child.children:
                self.add_child(c)

    def to_dict(self) -> dict:
        d = {'type': self.node_type}
        if len(self.children) > 0:
            d['children'] = [x.to_dict() for x in self.children]
        if self.value is not None:
            d['value'] = str(self.value)
        return d

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        return str(self.to_dict())
