import json
from typing import Self, TypeVar, Generic

T = TypeVar('T')


class ASTNode(Generic[T]):
    """
    The ASTNode class defines a node in an Abstract Syntax Tree. It has a type, which indicates what this node
    represents (e.g. 'function definition'), a value, which indicates the value of a terminal node, and a list of
    children, which are all the nodes required to describe this node.

    A terminal node is a node without children. It is not enforced, but terminal nodes should be the only node with a
    value, and all terminal nodes should have a value, with the token it represents. That is, is value is not None,
    children should be empty.

    The node type can be None. A None node type indicates that this node should not be in the final Abstract Syntax
    Tree. However, all of its children will be included in the tree. If node type is None then when you try to add this
    node as a child to another, it will add all of this node's children, rather than adding the node itself. This is
    useful in removing nodes which are required for parsing, but don't provide any extra information

    If auto_name is set to true, then this node will be named after the string value of the value attribute of the first
    descendant added to this node. Note that the node this ends up being named after may not end up being a child, as it
    may have a None node type. Auto naming will not overwrite a node type unless it is None

    Args:
        node_type: The type of the node. If None, then this node will not be included in the AST (but its children
            will be provided they have a non None type)
        value: The value of the node. This is optional, and should only be included for terminal nodes.
        auto_name: If true, sets the node type automatically based on the value of the first terminal descendant added

    Attributes:
        node_type: See args
        value: See args
        auto_name: See args
        children: A list of ASTNodes which contain the nodes required to describe this node. Should not be directly
            mutated, instead use add_child to add children. This ensures None node types are handled correctly
    """
    def __init__(self, node_type: str, auto_name: bool, value: T | None = None):
        self.children = []
        self.node_type = node_type
        self.value = value
        self.auto_name = auto_name

    def add_child(self, child: Self):
        """
        Adds the given child node to this node. If the node type is not None, then the child node is simply appended to
        the children list. However, if the node type is None, then the child is not added, but all of its children are
        recursively added using this function (i.e. only not None node types will be in the final AST, and they will be
        added to the nearest ancestor that has a not None node type)

        If auto naming is on, then this is determined here. If the node type is None, then the node type is set to the
        value of first terminal descendant of the child, regardless of if the child's type is None or not

        Args:
            child: the node to add
        """
        # Auto naming
        if self.auto_name and self.node_type is None:
            node = child
            while len(node.children) > 0:
                node = node.children[0]
            self.node_type = str(node.value)

        # Add child
        if child.node_type is not None:
            self.children.append(child)
        else:
            for c in child.children:
                self.add_child(c)

    def to_dict(self) -> dict:
        """Converts the node, with all its children to a dict for purposes of generating a string representation"""
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
