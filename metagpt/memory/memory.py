#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 12:15
@Author  : alexanderwu
@File    : memory.py
"""
import copy
from collections import defaultdict
from typing import Iterable, Type, Union, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import json

from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.utils.utils import read_json_file, write_json_file
from metagpt.utils.utils import import_class


class Memory(BaseModel):
    """The most basic memory: super-memory"""

    storage: list[Message] = Field(default=[])
    index: dict[Type[Action], list[Message]] = Field(default_factory=defaultdict(list))

    def __init__(self, **kwargs):
        index = kwargs.get("index", {})
        new_index = defaultdict(list)
        for action_str, value in index.items():
            action_dict = json.loads(action_str)
            action_class = import_class("Action", "metagpt.actions.action")
            action_obj = action_class.deser_class(action_dict)
            new_index[action_obj] = [Message(**item_dict) for item_dict in value]
        kwargs["index"] = new_index
        super(Memory, self).__init__(**kwargs)
        self.index = new_index

    def dict(self,
             *,
             include: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
             exclude: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
             by_alias: bool = False,
             skip_defaults: Optional[bool] = None,
             exclude_unset: bool = False,
             exclude_defaults: bool = False,
             exclude_none: bool = False) -> "DictStrAny":
        """ overwrite the `dict` to dump dynamic pydantic model"""
        obj_dict = super(Memory, self).dict(include=include,
                                            exclude=exclude,
                                            by_alias=by_alias,
                                            skip_defaults=skip_defaults,
                                            exclude_unset=exclude_unset,
                                            exclude_defaults=exclude_defaults,
                                            exclude_none=exclude_none)
        new_obj_dict = copy.deepcopy(obj_dict)
        new_obj_dict["index"] = {}
        for action, value in obj_dict["index"].items():
            action_ser = json.dumps(action.ser_class())
            new_obj_dict["index"][action_ser] = value
        return new_obj_dict

    def serialize(self, stg_path: Path):
        """ stg_path = ./storage/team/environment/ or ./storage/team/environment/roles/{role_class}_{role_name}/ """
        memory_path = stg_path.joinpath("memory.json")
        storage = self.dict()
        write_json_file(memory_path, storage)

    @classmethod
    def deserialize(cls, stg_path: Path) -> "Memory":
        """ stg_path = ./storage/team/environment/ or ./storage/team/environment/roles/{role_class}_{role_name}/"""
        memory_path = stg_path.joinpath("memory.json")

        memory_dict = read_json_file(memory_path)
        memory = Memory(**memory_dict)

        return memory

    def add(self, message: Message):
        """Add a new message to storage, while updating the index"""
        if message in self.storage:
            return
        self.storage.append(message)
        if message.cause_by:
            self.index[message.cause_by].append(message)

    def add_batch(self, messages: Iterable[Message]):
        for message in messages:
            self.add(message)

    def get_by_role(self, role: str) -> list[Message]:
        """Return all messages of a specified role"""
        return [message for message in self.storage if message.role == role]

    def get_by_content(self, content: str) -> list[Message]:
        """Return all messages containing a specified content"""
        return [message for message in self.storage if content in message.content]

    def delete_newest(self) -> "Message":
        """ delete the newest message from the storage"""
        if len(self.storage) > 0:
            newest_msg = self.storage.pop()
            if newest_msg.cause_by and newest_msg in self.index[newest_msg.cause_by]:
                self.index[newest_msg.cause_by].remove(newest_msg)
        else:
            newest_msg = None
        return newest_msg

    def delete(self, message: Message):
        """Delete the specified message from storage, while updating the index"""
        self.storage.remove(message)
        if message.cause_by and message in self.index[message.cause_by]:
            self.index[message.cause_by].remove(message)

    def clear(self):
        """Clear storage and index"""
        self.storage = []
        self.index = defaultdict(list)

    def count(self) -> int:
        """Return the number of messages in storage"""
        return len(self.storage)

    def try_remember(self, keyword: str) -> list[Message]:
        """Try to recall all messages containing a specified keyword"""
        return [message for message in self.storage if keyword in message.content]

    def get(self, k=0) -> list[Message]:
        """Return the most recent k memories, return all when k=0"""
        return self.storage[-k:]

    def find_news(self, observed: list[Message], k=0) -> list[Message]:
        """find news (previously unseen messages) from the the most recent k memories, from all memories when k=0"""
        already_observed = self.get(k)
        news: list[Message] = []
        for i in observed:
            if i in already_observed:
                continue
            news.append(i)
        return news

    def get_by_action(self, action: Type[Action]) -> list[Message]:
        """Return all messages triggered by a specified Action"""
        return self.index[action]

    def get_by_actions(self, actions: Iterable[Type[Action]]) -> list[Message]:
        """Return all messages triggered by specified Actions"""
        rsp = []
        for action in actions:
            if action not in self.index:
                continue
            rsp += self.index[action]
        return rsp
