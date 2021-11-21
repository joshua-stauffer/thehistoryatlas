"""
An in memory Trie for finding entity GUIDs by name.

Saturday, November 13th 2021
"""

from collections import deque
from logging import log
from typing import TypedDict

class TrieResult(TypedDict):
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
        print(indent, f"{self.name}: ({len(self.children)}")
        for child in self.children.values():
            child.print(depth=depth+1)


class Trie:

    def __init__(self, entity_tuples):
        
        self.root = Node('')
        self.build(entity_tuples)

    def build(self, entity_tuples):
        """Initializes the data structure"""

        for name, guid in entity_tuples:
            self.insert(name, guid)

    def insert(self, string: str, guid: str):
        processed_string = string.lower()
        node = self.root
        for char in processed_string:
            char = char.lower()
            if char in node.children:
                node = node.children[char]
            else:
                new_node = Node(char)
                node.children[char] = new_node
                node = new_node
        # this node is now a leaf
        node.ids.add(guid)
        node.name = string
        self.root.print()

    def delete(self, string: str, guid: str):
        processed_string = string.lower()
        node = self.root
        path = [node]
        for char in processed_string:
            node = node.children[char]
            path.append(node)
        # remove any orphaned nodes
        for n in path:
            print(n)
        node.ids.remove(guid)
        while not len(node.children) and not len(node.ids) and len(path):
            print('starting at node ', node.name)
            val = node.value
            node = path.pop()
            print('now at node ', node.name)
            del node.children[val]



    def find(self, string: str, res_count=1) -> list[TrieResult]:
        processed_string = string.lower()
        node = self.root
        for char in processed_string:
            if char not in node.children:
                break
            node = node.children[char]
        res = list()
        queue = deque([node])
        while len(queue) and res_count > 0:
            current_node = queue.popleft()
            queue.extend(current_node.children.values())
            if current_node.name:
                res.append({
                    'name': current_node.name,
                    'guids': list(current_node.ids)
                })
                res_count -= 1
        return res

