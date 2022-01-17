# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe

class FileLockedError(Exception):
	pass

class DistributedLock(object):
	def __init__(self, path, ttl=60):
		self.path = path
		self.ttl = ttl
		self.lock_id = f'{frappe.session.user}{frappe.utils.now_datetime().timestamp()}'
		self.acquired = False


	def acquire(self):
		if frappe.cache().get_value(self.path, expires=True) is not None:
			raise FileLockedError()
		frappe.cache().set_value(self.path, self.lock_id, expires_in_sec=self.ttl)
		self.acquired = True


	def release(self):
		lock = frappe.cache().get_value(self.path, expires=True)
		if lock and lock == self.lock_id:
			frappe.cache().delete_value(self.path)
		self.acquired = False


	def __enter__(self):
		if not self.acquired:
			self.acquire()
		return self


	def __exit__(self, exc_type, exc_value, traceback):
		if self.acquired:
			self.release()


