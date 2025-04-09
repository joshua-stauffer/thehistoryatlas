from collections import deque
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)
log.setLevel("DEBUG")


@dataclass(frozen=True)
class TrieResult:
    """The result of a trie search"""

    name: str
    guids: frozenset[str]


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
    def __init__(self):

        self.root = Node("")

    def build(self, entity_tuples):
        """Initializes the data structure"""

        for name, guid in entity_tuples:
            sub_strings = self.phrase_parts(name)
            for sub_string in sub_strings:
                self.insert(sub_string, guid)

    def phrase_parts(self, phrase: str) -> list[str]:
        # individual words
        result = []
        parts = phrase.split(" ")
        result.extend(parts)
        # sub phrases
        for i, _ in enumerate(parts):
            result.append(" ".join(parts[i:]))
        return result

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
        res = set()
        queue = deque([node])
        while len(queue) and len(res) < res_count:
            current_node = queue.popleft()
            queue.extend(current_node.children.values())
            if current_node.name:
                res.add(
                    TrieResult(
                        name=current_node.name, guids=frozenset(current_node.ids)
                    )
                )
        log.debug(f"result is {res}")
        return list(res)
