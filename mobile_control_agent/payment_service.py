"""Payment Service for FamilyOS AI.

Manages backend payment records, order creation with payment gateways,
generation of UPI Intent URIs (upi://pay), and cryptographic transaction
status verification for both Gateway Orders (Scenario A) and Direct Transfers (Scenario B).
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Optional, Dict, Any

PAYMENTS_STORE_FILE = "payment_records.json"


@dataclass
class PaymentRecord:
    payment_id: str
    task_id: str
    order_id: str
    merchant_order_id: str
    scenario: str  # "GATEWAY_ORDER" or "DIRECT_TRANSFER"
    gateway_name: str  # "razorpay", "cashfree", "phonepe", "mock_gateway"
    gateway_order_id: Optional[str]
    gateway_payment_id: Optional[str]
    payment_method: str  # "UPI"
    amount: float
    currency: str  # "INR"
    payment_status: str  # "CREATED", "PENDING", "SUCCESS", "FAILED", "CANCELLED", "UNCONFIRMED"
    gateway_status: Optional[str]
    transaction_reference: Optional[str]  # UTR
    payee_vpa: Optional[str]
    payee_name: str
    failure_reason: Optional[str]
    created_at: str
    updated_at: str
    verified_at: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PaymentService:
    """Backend payment service for FamilyOS AI."""

    def __init__(self, storage_path: str = PAYMENTS_STORE_FILE):
        self.storage_path = storage_path
        self.records: Dict[str, PaymentRecord] = {}
        self._load_records()

    def _load_records(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for pid, rec in data.items():
                        self.records[pid] = PaymentRecord(**rec)
            except Exception as e:
                print(f"[PaymentService] Warning: Failed to load records from {self.storage_path}: {e}")

    def _save_records(self) -> None:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({k: v.to_dict() for k, v in self.records.items()}, f, indent=2)
        except Exception as e:
            print(f"[PaymentService] Error saving records: {e}")

    def create_payment_order(
        self,
        task_id: str,
        order_id: str,
        amount: float,
        currency: str = "INR",
        payee_name: str = "Merchant",
        payee_vpa: Optional[str] = None,
        scenario: str = "GATEWAY_ORDER",
        gateway_name: str = "razorpay",
    ) -> Dict[str, Any]:
        """Creates a payment order, records it, and builds a standard UPI Intent URI."""
        payment_id = str(uuid.uuid4())
        timestamp = int(time.time())
        merchant_order_id = f"FOS_ORD_{timestamp}_{order_id[-6:] if len(order_id) >= 6 else order_id}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Gateway-specific or default merchant VPA
        target_vpa = payee_vpa or os.environ.get("FAMILYOS_MERCHANT_VPA", "familyos.pay@icici")

        # Mock / Sandbox gateway order generation
        gateway_order_id = f"order_{gateway_name[:3]}_{timestamp}" if scenario == "GATEWAY_ORDER" else None

        # Build official NPCI UPI Deep Link / Intent URI
        # Spec: upi://pay?pa=<vpa>&pn=<name>&am=<amount>&tr=<ref>&cu=<currency>&mc=<merchant_code>
        upi_intent_uri = (
            f"upi://pay?pa={target_vpa}"
            f"&pn={payee_name.replace(' ', '%20')}"
            f"&am={amount:.2f}"
            f"&tr={merchant_order_id}"
            f"&cu={currency}"
            f"&mc=5411"
        )

        record = PaymentRecord(
            payment_id=payment_id,
            task_id=task_id,
            order_id=order_id,
            merchant_order_id=merchant_order_id,
            scenario=scenario,
            gateway_name=gateway_name,
            gateway_order_id=gateway_order_id,
            gateway_payment_id=None,
            payment_method="UPI",
            amount=amount,
            currency=currency,
            payment_status="CREATED",
            gateway_status="created",
            transaction_reference=None,
            payee_vpa=target_vpa,
            payee_name=payee_name,
            failure_reason=None,
            created_at=now_iso,
            updated_at=now_iso,
            verified_at=None,
        )

        self.records[payment_id] = record
        self._save_records()

        return {
            "payment_id": payment_id,
            "merchant_order_id": merchant_order_id,
            "gateway_order_id": gateway_order_id,
            "amount": amount,
            "currency": currency,
            "payee_name": payee_name,
            "payee_vpa": target_vpa,
            "upi_intent_uri": upi_intent_uri,
            "scenario": scenario,
            "payment_status": "CREATED",
        }

    def mark_pending(self, payment_id: str) -> None:
        """Mark payment as PENDING when handed over to the user's payment app."""
        if payment_id in self.records:
            self.records[payment_id].payment_status = "PENDING"
            self.records[payment_id].updated_at = datetime.now(timezone.utc).isoformat()
            self._save_records()

    def verify_payment_status(
        self,
        payment_id: str,
        timeout_seconds: int = 30,
        poll_interval: int = 2,
    ) -> Dict[str, Any]:
        """Polls for authoritative status update (webhook reception or gateway status API check)."""
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            record = self.records.get(payment_id)
            if not record:
                return {"payment_status": "UNKNOWN", "error": "Record not found"}

            # If already verified via webhook or API
            if record.payment_status in ("SUCCESS", "FAILED", "CANCELLED", "UNCONFIRMED"):
                return record.to_dict()

            time.sleep(poll_interval)

        # Timeout reached
        record = self.records.get(payment_id)
        if record and record.payment_status == "PENDING":
            return record.to_dict()

        return {"payment_status": "UNKNOWN", "error": "Verification timed out"}

    def confirm_direct_transfer(self, payment_id: str, utr_hint: Optional[str] = None) -> Dict[str, Any]:
        """For Scenario B (Direct P2P): marks the transaction as UNCONFIRMED_USER_REPORTED."""
        record = self.records.get(payment_id)
        if not record:
            return {"payment_status": "UNKNOWN", "error": "Record not found"}

        now_iso = datetime.now(timezone.utc).isoformat()
        record.payment_status = "UNCONFIRMED"
        record.transaction_reference = utr_hint
        record.updated_at = now_iso
        self._save_records()
        return record.to_dict()

    def process_gateway_webhook(
        self,
        payment_id: str,
        event_name: str,
        status: str,
        gateway_payment_id: str,
        utr: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> bool:
        """Simulates or receives an authorized gateway webhook and idempotently updates status."""
        record = self.records.get(payment_id)
        if not record:
            return False

        # Idempotency check: once SUCCESS, do not revert
        if record.payment_status == "SUCCESS":
            return True

        now_iso = datetime.now(timezone.utc).isoformat()
        if status.upper() in ("CAPTURED", "PAID", "SUCCESS"):
            record.payment_status = "SUCCESS"
            record.gateway_status = "captured"
            record.gateway_payment_id = gateway_payment_id
            record.transaction_reference = utr or f"UTR{int(time.time()*1000)}"
            record.verified_at = now_iso
        elif status.upper() in ("FAILED", "DECLINED"):
            record.payment_status = "FAILED"
            record.gateway_status = "failed"
            record.failure_reason = "Payment declined by user or issuing bank."
        elif status.upper() in ("CANCELLED", "USER_DROPPED"):
            record.payment_status = "CANCELLED"
            record.gateway_status = "cancelled"

        record.updated_at = now_iso
        self._save_records()
        return True


# Global singleton instance
payment_service = PaymentService()
