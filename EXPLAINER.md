# Playto Payout Engine Explainer

## The Ledger
**Balance Calculation Query:**
```python
result = LedgerEntry.objects.filter(merchant=merchant).aggregate(
    balance=models.Sum('amount')
)
```
**Why this model?**
We use an **Immutable Ledger** pattern. Balance is never a column on the `Merchant` table because that is prone to desync and race conditions. By deriving balance from the sum of credits and debits, we ensure that every paise is accounted for. The ledger entries are linked to `Payout` objects, providing a perfect audit trail. Credits are positive, debits are negative, making the invariant `sum(ledger) == balance` naturally true at the DB level.

## The Lock
**Concurrency Prevention Code:**
```python
with transaction.atomic():
    # Lock the merchant row to prevent concurrent payout requests
    merchant_locked = Merchant.objects.select_for_update().get(id=merchant.id)
    
    # Re-calculate balance inside the locked transaction
    current_balance = PayoutService.get_merchant_balance(merchant_locked)
    
    if current_balance < amount_paise:
        raise ValueError("Insufficient balance")
    
    # ... create payout and ledger entry ...
```
**Database Primitive:**
This relies on **PostgreSQL Row-Level Locking (`SELECT FOR UPDATE`)**. It places an exclusive lock on the specific merchant row. Any other transaction trying to `SELECT FOR UPDATE` that same merchant row will block until the first one commits or rolls back. This prevents the "Check-then-Deduct" race condition where two requests see the same balance before either has deducted from it.

## The Idempotency
**Mechanism:**
The system uses an `IdempotencyKey` table scoped to the merchant. When a request arrives:
1. We check if the `(key, merchant)` tuple exists.
2. If it does and has a `response_body`, we return it immediately.
3. If it exists but `response_body` is null, we check the `locked_at` timestamp. If it's recent, we return `409 Conflict` ("Request in flight").

**In-flight Handling:**
The `locked_at` field acts as a soft lock. In a high-scale production system, I would use **Redis SETNX** for the in-flight lock to avoid DB overhead, but for this engine, the `locked_at` column in Postgres (within a transaction) ensures we don't process the same key twice simultaneously.

## The State Machine
**Blocked Transition Check:**
```python
# In payouts/tasks.py
with transaction.atomic():
    payout = Payout.objects.select_for_update().get(id=payout_id)
    
    # State machine check: must be PENDING or PROCESSING (if retrying)
    if payout.status not in ['PENDING', 'PROCESSING']:
        return f"Payout {payout_id} in invalid state: {payout.status}"
```
Illegal transitions like `FAILED -> COMPLETED` are blocked because the worker first locks the row and checks if the status is one of the allowed "start" states. If a payout is already `FAILED`, it will never enter the logic to mark it `COMPLETED`.

## The AI Audit
**Wrong Code Example (Race Condition):**
AI initially suggested calculating the balance in Python by fetching all ledger entries and summing them:
```python
# Subtle Bug: Fetching all then summing in Python
entries = LedgerEntry.objects.filter(merchant=merchant)
balance = sum(e.amount for e in entries) # WRONG
```
**The Catch:**
This is dangerous because:
1. It's inefficient (fetching 10k rows to sum them).
2. More importantly, it's not atomic. If a new ledger entry is added *between* the fetch and the deduction, the calculation is stale.

**The Fix:**
I replaced it with a database-level aggregation `Sum('amount')` executed within a `SELECT FOR UPDATE` transaction. This ensures the sum is calculated by the database engine while the merchant row is locked, guaranteeing the balance is current and consistent.
