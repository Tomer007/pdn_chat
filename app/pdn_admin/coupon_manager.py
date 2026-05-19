"""CouponManager - JSON file-backed coupon management with in-memory caching."""

import json
import logging
import random
import string
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pdn_admin")


def generate_coupon_code(existing_codes: set) -> str:
    """Generate a unique 8-character alphanumeric code [A-Z0-9].

    Checks against existing_codes to ensure uniqueness.
    """
    charset = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(charset, k=8))
        if code not in existing_codes:
            return code


def validate_custom_code(code: str) -> tuple:
    """Validate a custom code: 4-20 alphanumeric characters.

    Returns (is_valid, error_message).
    """
    if not isinstance(code, str):
        return False, "Code must be a string"
    if len(code) < 4 or len(code) > 20:
        return False, "Code must be 4-20 alphanumeric characters"
    if not code.isalnum():
        return False, "Code must be 4-20 alphanumeric characters"
    return True, ""


class CouponManager:
    """Manages coupon data with JSON file persistence and in-memory caching."""

    def __init__(self, json_path: Optional[Path] = None):
        self._json_path = json_path or (Path(__file__).parent.parent / "data" / "coupons.json")
        self._coupons: dict = {}
        self._lock = threading.Lock()
        self._load_coupons()

    # --- Core data operations ---

    def _load_coupons(self) -> None:
        """Load coupons from JSON file. Initializes empty dict if file missing or corrupt."""
        with self._lock:
            if self._json_path.exists():
                try:
                    data = json.loads(self._json_path.read_text(encoding='utf-8'))
                    if isinstance(data, dict):
                        self._coupons = data
                        return
                except (json.JSONDecodeError, OSError):
                    pass
            # Initialize with empty data
            self._coupons = {}
            self._save_to_file()

    def _save_to_file(self) -> None:
        """Persist current in-memory coupons to JSON file atomically."""
        tmp_path = self._json_path.with_suffix('.tmp')
        self._json_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(
            json.dumps(self._coupons, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        tmp_path.replace(self._json_path)

    def get_status(self, coupon: dict) -> str:
        """Derive status from usage_count and max_usage.

        Returns 'active' if usage_count < max_usage, 'full' otherwise.
        """
        usage_count = coupon.get("usage_count", 0)
        max_usage = coupon.get("max_usage", 0)
        if usage_count < max_usage:
            return "active"
        return "full"

    # --- CRUD operations ---

    def create_coupon(self, name: str, max_usage: int, code: Optional[str] = None) -> dict:
        """Create a new coupon. Auto-generates code if not provided.

        Returns the created coupon dict.
        Raises ValueError if code is duplicate or invalid.
        """
        with self._lock:
            if code is not None:
                is_valid, error_msg = validate_custom_code(code)
                if not is_valid:
                    raise ValueError(error_msg)
                if code in self._coupons:
                    raise ValueError("Coupon code already exists")
            else:
                code = generate_coupon_code(set(self._coupons.keys()))

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            coupon = {
                "name": name,
                "code": code,
                "max_usage": max_usage,
                "usage_count": 0,
                "used_by": [],
                "created_at": now,
                "updated_at": now,
            }
            self._coupons[code] = coupon
            self._save_to_file()
            return coupon

    def get_coupon(self, code: str) -> Optional[dict]:
        """Get a single coupon by code. Returns None if not found."""
        with self._lock:
            return self._coupons.get(code)

    def get_all_coupons(self) -> list:
        """Return all coupons as a list of dicts with status added."""
        with self._lock:
            result = []
            for coupon in self._coupons.values():
                coupon_with_status = dict(coupon)
                coupon_with_status["status"] = self.get_status(coupon)
                result.append(coupon_with_status)
            return result

    def update_coupon(self, coupon_code: str, **updates) -> dict:
        """Update coupon fields (name, max_usage). Code is immutable.

        Raises KeyError if not found, ValueError if invalid updates.
        """
        with self._lock:
            if coupon_code not in self._coupons:
                raise KeyError(f"Coupon not found: {coupon_code}")

            # Code is immutable - reject any attempt to change it
            if "code" in updates:
                raise ValueError("Coupon code cannot be modified")

            allowed_fields = {"name", "max_usage"}
            for key in updates:
                if key not in allowed_fields:
                    raise ValueError(f"Cannot update field: {key}")

            coupon = self._coupons[coupon_code]
            for key, value in updates.items():
                coupon[key] = value

            coupon["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._save_to_file()
            return coupon

    def delete_coupon(self, code: str) -> None:
        """Delete a coupon by code. Raises KeyError if not found."""
        with self._lock:
            if code not in self._coupons:
                raise KeyError(f"Coupon not found: {code}")
            del self._coupons[code]
            self._save_to_file()

    def redeem_coupon(self, code: str, email: str) -> dict:
        """Record a coupon redemption. Increments usage_count, adds email to used_by.

        Raises ValueError if coupon is full or not found.
        """
        with self._lock:
            if code not in self._coupons:
                raise ValueError(f"Coupon not found: {code}")

            coupon = self._coupons[code]
            if coupon["usage_count"] >= coupon["max_usage"]:
                raise ValueError("Coupon has reached its usage limit")

            coupon["usage_count"] += 1
            coupon["used_by"].append(email)
            coupon["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._save_to_file()
            return coupon

    def validate_coupon(self, code: str) -> tuple:
        """Check if a coupon code is valid and has remaining uses.

        Returns (is_valid, message).
        """
        with self._lock:
            if code not in self._coupons:
                return False, "Invalid coupon code"

            coupon = self._coupons[code]
            if coupon["usage_count"] >= coupon["max_usage"]:
                return False, "Coupon has reached its usage limit"

            return True, "Valid"


# Module-level singleton
_coupon_manager: Optional[CouponManager] = None


def get_coupon_manager() -> CouponManager:
    """Get or create the singleton CouponManager instance."""
    global _coupon_manager
    if _coupon_manager is None:
        _coupon_manager = CouponManager()
    return _coupon_manager
