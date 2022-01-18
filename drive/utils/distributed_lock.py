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
		key = frappe.cache().make_key(self.path)
		if not self._add(key, self.lock_id, self.ttl):
			raise FileLockedError()
		self.acquired = True


	def release(self):
		key = frappe.cache().make_key(self.path)
		self._check_and_delete(key, self.lock_id)
		self.acquired = False


	def __enter__(self):
		if not self.acquired:
			self.acquire()
		return self


	def __exit__(self, exc_type, exc_value, traceback):
		if self.acquired:
			self.release()


	def _add(self, key, value, ttl):
		'''Returns true if key does not already exist and value is set'''
		return frappe.cache().set(key, value, ex=ttl, nx=True)


	def _check_and_set(self, key, expected_val, new_val, ttl):
		'''Atomic transaction to set value if current value matches the expected value'''
		with frappe.cache().pipeline() as pipe:
			while True:
				try:
					pipe.watch(key)
					current_val = pipe.get(key)
					if current_val and current_val.decode() != expected_val:
						return False
					pipe.multi()
					pipe.set(key, new_val, ex=ttl)
					return pipe.execute()[0]
				except WatchError:
					continue


	def _check_and_delete(self, key, expected_val):
		'''Atomic transaction to delete the key if current value matches the expected value'''
		with frappe.cache().pipeline() as pipe:
			while True:
				try:
					pipe.watch(key)
					current_val = pipe.get(key)
					if current_val and current_val.decode() != expected_val:
						return False
					pipe.multi()
					pipe.delete(key)
					return pipe.execute()[0]
				except WatchError:
					continue