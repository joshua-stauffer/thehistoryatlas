"""
An in memory Trie for finding entity GUIDs by name.

Saturday, November 13th 2021
"""

from collections import deque
import logging
from dataclasses import dataclass
from typing import TypedDict

log = logging.getLogger(__name__)
log.setLevel("DEBUG")


@dataclass(frozen=True)
class TrieResult:
    """The result of a trie search"""

    name: str
    guids: list[str]


class Node:
    def __init__(self, value: str):
        self.value: str = value
        self.children: dict[str, Node] = {}
        self.ids: set[str] = set()
        self.name = None

    def __repr__(self):
        return f"""
            Node(
                name: {self.name}
                children: {self.children}
                guids: {self.ids}
            )
            """

    def print(self, depth=0):
        indent = "-" * depth + "  "
        print(indent, f"<{self.value}> {self.name}: ({len(self.children)} children)")
        for child in self.children.values():
            child.print(depth=depth + 1)


class Trie:
    def __init__(self, entity_tuples):

        self.root = Node("")
        self.build(entity_tuples)

    def build(self, entity_tuples):
        """Initializes the data structure"""

        for name, guid in entity_tuples:
            self.insert(name, guid)

    def insert(self, string: str, guid: str):
        log.debug(f"trie: add string {string}")
        processed_string = string.lower()
        node = self.root
        for char in processed_string:
            if char in node.children:
                node = node.children[char]
            else:
                new_node = Node(char)
                node.children[char] = new_node
                node = new_node
        # this node is now a leaf
        node.ids.add(guid)
        node.name = string
        log.debug(f"created leaf: {node.name}")
        # debug only: self.root.print()

    def delete(self, string: str, guid: str) -> bool:
        processed_string = string.lower()
        node = self.root
        path = [node]
        for char in processed_string:
            node = node.children.get(char, None)
            if node:
                path.append(node)
            else:
                return False
        node.ids.remove(guid)
        # remove any orphaned nodes
        path.pop()  # node points to this already
        while not len(node.children) and not len(node.ids) and len(path):
            val = node.value
            node = path.pop()
            del node.children[val]
        return True

    def find(self, string: str, res_count=1) -> list[TrieResult]:
        log.debug(f"searching for term {string}")
        processed_string = string.lower()
        node = self.root
        for char in processed_string:
            if char not in node.children:
                break
            node = node.children[char]
        log.debug(f"closest neighbor found is {node.name}, {node.value}")
        res = list()
        queue = deque([node])
        while len(queue) and res_count > 0:
            current_node = queue.popleft()
            queue.extend(current_node.children.values())
            if current_node.name:
                res.append(
                    TrieResult(name=current_node.name, guids=list(current_node.ids))
                )
                res_count -= 1
        log.debug(f"result is {res}")
        return res
