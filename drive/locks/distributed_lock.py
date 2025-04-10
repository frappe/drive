import frappe
import redis


class FileLockedError(Exception):
    pass


class DistributedLock(object):
    def __init__(self, path, exclusive, ttl=60):
        self.path = path
        self.exclusive = exclusive
        self.ttl = ttl
        self.key = frappe.cache().make_key(path)
        self.lock_id = f"{frappe.session.user}{frappe.utils.now_datetime().timestamp()}"
        self.acquired = False

    def acquire_write_lock(self):
        if not self._add(self.key, self.lock_id, self.ttl):
            raise FileLockedError()
        self.acquired = True

    def release_write_lock(self):
        self._check_and_delete(self.key, self.lock_id)
        self.acquired = False

    def acquire_read_lock(self):
        if not self._increment(self.key, self.ttl):
            raise FileLockedError()
        self.acquired = True

    def release_read_lock(self):
        if not self._check_and_delete(self.key, "1"):
            self._decrement(self.key)
        self.acquired = False

    def __enter__(self):
        if not self.acquired:
            self.acquire_write_lock() if self.exclusive else self.acquire_read_lock()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.acquired:
            self.release_write_lock() if self.exclusive else self.release_read_lock()

    def _add(self, key, value, ttl):
        """Returns true if key does not already exist and value is set"""
        return frappe.cache().set(key, value, ex=ttl, nx=True)

    def _increment(self, key, ttl):
        """Atomic transaction to increment value. Returns False if current value cannot be incremented.
        If the key does not exist, value is set to 1"""
        with frappe.cache().pipeline() as pipe:
            try:
                res = pipe.incr(key).expire(key, ttl).execute()
                return True
            except redis.ResponseError:
                return False

    def _decrement(self, key):
        """Atomic transaction to decrement value. Returns False if current value cannot be decremented
        or if the key does not exist"""
        try:
            if not frappe.cache().exists(key):
                return False
            frappe.cache().decr(key)
            return True
        except redis.ResponseError:
            return False

    def _check_and_set(self, key, expected_val, new_val, ttl):
        """Atomic transaction to set value if current value matches the expected value"""
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
                except redis.WatchError:
                    continue

    def _check_and_delete(self, key, expected_val):
        """Atomic transaction to delete the key if current value matches the expected value"""
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
                except redis.WatchError:
                    continue
