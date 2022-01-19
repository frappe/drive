# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

from frappe.utils.nestedset import get_ancestors_of
from drive.utils.files import get_entity_path
from drive.locks.distributed_lock import DistributedLock

class DriveEntityLock(DistributedLock):
	def __init__(self, entity_name, exclusive, ttl=60):
		self.entity_name = entity_name
		self.path = get_entity_path(entity_name)
		super().__init__(self.path, exclusive, ttl)
		parents = get_ancestors_of('Drive Entity', entity_name, 'lft asc')
		self.parent_locks = [DriveEntityLock(parent, exclusive=False) for parent in parents]


	def __enter__(self):
		if not self.acquired:
			for lock in self.parent_locks:
				lock.acquire_read_lock()
			self.acquire_write_lock() if self.exclusive else self.acquire_read_lock()
		return self


	def __exit__(self, exc_type, exc_value, traceback):
		if self.acquired:
			for lock in self.parent_locks:
				lock.release_read_lock()
			self.release_write_lock() if self.exclusive else self.release_read_lock()