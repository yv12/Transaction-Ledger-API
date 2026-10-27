import sys
import os
import json
import uuid
import requests
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure UTF-8 output encoding on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://localhost:8000"
session = requests.Session()

results = []

def log(msg):
    print(msg, flush=True)

def record(area, name, method, path, payload, headers, expected_status, expected_summary, actual_status, actual_body, passed, notes=""):
    req_display = f"{method} {path}"
    if payload is not None:
        if isinstance(payload, (dict, list)):
            p_str = json.dumps(payload)
        else:
            p_str = str(payload)
        if len(p_str) > 120:
            p_str = p_str[:120] + "... (truncated)"
        req_display += f" | Body: {p_str}"
        
    act_display = f"HTTP {actual_status}"
    if isinstance(actual_body, dict):
        act_display += f": {json.dumps(actual_body)}"
    elif actual_body is not None:
        act_display += f": {str(actual_body)}"
    if len(act_display) > 200:
        act_display = act_display[:200] + "... (truncated)"

    entry = {
        "area": area,
        "name": name,
        "request": req_display,
        "expected": f"Status {expected_status}: {expected_summary}",
        "actual": act_display,
        "actual_status": actual_status,
        "status": "PASS" if passed else "FAIL",
        "notes": notes,
        "raw_response": actual_body
    }
    results.append(entry)
    status_str = "✅ PASS" if passed else "❌ FAIL"
    log(f"[{status_str}] {area} - {name}")

def create_account(name="QA Test Account"):
    r = session.post(f"{BASE_URL}/accounts", json={"name": name})
    assert r.status_code == 201, f"Failed to create account: {r.text}"
    return r.json()["id"]

def get_balance(acc_id):
    r = session.get(f"{BASE_URL}/accounts/{acc_id}/balance")
    assert r.status_code == 200
    return r.json()["balance"]

def is_error_shape_valid(body):
    if not isinstance(body, dict):
        return False
    err = body.get("error")
    if not isinstance(err, dict):
        return False
    if "code" not in err or "message" not in err or "details" not in err:
        return False
    body_str = json.dumps(body)
    trace_indicators = ["Traceback (most recent call last)", "File \"", "line ", "OperationalError", "InternalServerError"]
    for ind in trace_indicators:
        if ind in body_str:
            return False
    return True

log("==================================================")
log("  TRANSACTION LEDGER API - COMPREHENSIVE QA SUITE ")
log("  Target: " + BASE_URL)
log("==================================================")

# ==========================================
# 1. Duplicates
# ==========================================
log("\n--- Category 1: Duplicates ---")
acc1 = create_account("Dup Test 1")

# 1.1 Same reference_id twice
ref1 = f"dup-ref-{uuid.uuid4().hex[:6]}"
p1 = {"type": "credit", "amount": 100.0, "reference_id": ref1, "description": "initial credit"}
r1 = session.post(f"{BASE_URL}/accounts/{acc1}/transactions", json=p1)
p2 = {"type": "credit", "amount": 100.0, "reference_id": ref1, "description": "duplicate credit"}
r2 = session.post(f"{BASE_URL}/accounts/{acc1}/transactions", json=p2)
bal1 = get_balance(acc1)
passed1 = (r1.status_code == 201 and r2.status_code == 409 and 
           r2.json().get("error", {}).get("code") == "DUPLICATE_TRANSACTION" and bal1 == 100.0)
record(
    "1. Duplicates", "Same reference_id twice on same account",
    "POST", f"/accounts/{acc1}/transactions", p2, None,
    409, "Rejected with 409 DUPLICATE_TRANSACTION, balance remains 100.0",
    r2.status_code, r2.json(), passed1, f"Balance: {bal1}"
)

# 1.2 10 parallel requests with the same reference_id
acc_p = create_account("Parallel Duplicates Test")
ref_p = f"par-ref-{uuid.uuid4().hex[:6]}"
payload_p = {"type": "credit", "amount": 50.0, "reference_id": ref_p, "description": "parallel test"}

def fire_parallel_tx(acc, p):
    s = requests.Session()
    return s.post(f"{BASE_URL}/accounts/{acc}/transactions", json=p)

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fire_parallel_tx, acc_p, payload_p) for _ in range(10)]
    responses_p = [f.result() for f in as_completed(futures)]

codes_p = [r.status_code for r in responses_p]
bal_p = get_balance(acc_p)
passed_p = (codes_p.count(201) == 1 and codes_p.count(409) == 9 and bal_p == 50.0)
record(
    "1. Duplicates", "10 parallel requests with same reference_id",
    "POST", f"/accounts/{acc_p}/transactions", payload_p, None,
    "201 x1, 409 x9", "Exactly 1 request succeeds (201), 9 rejected with 409, balance = 50.0",
    f"201: {codes_p.count(201)}, 409: {codes_p.count(409)}", {"status_codes": codes_p, "final_balance": bal_p},
    passed_p, f"201 count: {codes_p.count(201)}, 409 count: {codes_p.count(409)}, balance: {bal_p}"
)

# 1.3 Same reference_id with a different amount
acc_diff = create_account("Diff Amount Duplicate")
ref_diff = f"diff-ref-{uuid.uuid4().hex[:6]}"
session.post(f"{BASE_URL}/accounts/{acc_diff}/transactions", json={"type": "credit", "amount": 100.0, "reference_id": ref_diff})
p_diff2 = {"type": "credit", "amount": 200.0, "reference_id": ref_diff, "description": "tampered amount"}
r_diff = session.post(f"{BASE_URL}/accounts/{acc_diff}/transactions", json=p_diff2)
bal_diff = get_balance(acc_diff)
passed_diff = (r_diff.status_code == 409 and r_diff.json().get("error", {}).get("code") == "DUPLICATE_TRANSACTION" and bal_diff == 100.0)
record(
    "1. Duplicates", "Same reference_id with a different amount (tampered)",
    "POST", f"/accounts/{acc_diff}/transactions", p_diff2, None,
    409, "Rejected with 409 DUPLICATE_TRANSACTION, balance stays 100.0",
    r_diff.status_code, r_diff.json(), passed_diff, f"Balance: {bal_diff}"
)


# ==========================================
# 2. Overdraw
# ==========================================
log("\n--- Category 2: Overdraw ---")
# 2.1 Parallel debits that together exceed balance
acc_od = create_account("Overdraw Concurrency Test")
session.post(f"{BASE_URL}/accounts/{acc_od}/transactions", json={"type": "credit", "amount": 100.0, "reference_id": f"seed-{uuid.uuid4().hex[:6]}"})

def fire_debit(acc, i):
    s = requests.Session()
    p = {"type": "debit", "amount": 30.0, "reference_id": f"debit-par-{i}-{uuid.uuid4().hex[:6]}", "description": f"concurrent debit {i}"}
    return s.post(f"{BASE_URL}/accounts/{acc}/transactions", json=p)

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fire_debit, acc_od, i) for i in range(5)]
    responses_od = [f.result() for f in as_completed(futures)]

codes_od = [r.status_code for r in responses_od]
bal_od = get_balance(acc_od)
passed_od = (codes_od.count(201) == 3 and codes_od.count(422) == 2 and bal_od == 10.0)
record(
    "2. Overdraw", "Parallel debits exceeding balance (5x30 against 100 balance)",
    "POST", f"/accounts/{acc_od}/transactions", "5 parallel debits of 30.0 each", None,
    "201 x3, 422 x2", "Exactly 3 debits succeed (201), 2 fail (422 INSUFFICIENT_BALANCE), balance = 10.0, never negative",
    f"201: {codes_od.count(201)}, 422: {codes_od.count(422)}", {"codes": codes_od, "final_balance": bal_od},
    passed_od, f"Final balance: {bal_od} (never < 0)"
)

# 2.2 Debit exactly equal to the balance
acc_exact = create_account("Debit Exactly Equal")
session.post(f"{BASE_URL}/accounts/{acc_exact}/transactions", json={"type": "credit", "amount": 50.0, "reference_id": f"seed-{uuid.uuid4().hex[:6]}"})
p_exact = {"type": "debit", "amount": 50.0, "reference_id": f"exact-{uuid.uuid4().hex[:6]}"}
r_exact = session.post(f"{BASE_URL}/accounts/{acc_exact}/transactions", json=p_exact)
bal_exact = get_balance(acc_exact)
passed_exact = (r_exact.status_code == 201 and bal_exact == 0.0)
record(
    "2. Overdraw", "Debit exactly equal to balance (50.0 on 50.0)",
    "POST", f"/accounts/{acc_exact}/transactions", p_exact, None,
    201, "Succeeds (201), final balance reaches exactly 0.0",
    r_exact.status_code, r_exact.json(), passed_exact, f"Balance: {bal_exact}"
)

# 2.3 Debit 0.01 above the balance
acc_above = create_account("Debit 0.01 Above")
session.post(f"{BASE_URL}/accounts/{acc_above}/transactions", json={"type": "credit", "amount": 50.0, "reference_id": f"seed-{uuid.uuid4().hex[:6]}"})
p_above = {"type": "debit", "amount": 50.01, "reference_id": f"above-{uuid.uuid4().hex[:6]}"}
r_above = session.post(f"{BASE_URL}/accounts/{acc_above}/transactions", json=p_above)
bal_above = get_balance(acc_above)
passed_above = (r_above.status_code == 422 and r_above.json().get("error", {}).get("code") == "INSUFFICIENT_BALANCE" and bal_above == 50.0)
record(
    "2. Overdraw", "Debit 0.01 above balance (50.01 on 50.0 balance)",
    "POST", f"/accounts/{acc_above}/transactions", p_above, None,
    422, "Rejected with 422 INSUFFICIENT_BALANCE, balance unchanged at 50.0",
    r_above.status_code, r_above.json(), passed_above, f"Balance: {bal_above}"
)


# ==========================================
# 3. Amounts
# ==========================================
log("\n--- Category 3: Amounts ---")
acc_amt = create_account("Amounts Validation Test")

# 3.1 Amount = 0
p_0 = {"type": "credit", "amount": 0, "reference_id": f"amt-0-{uuid.uuid4().hex[:6]}"}
r_0 = session.post(f"{BASE_URL}/accounts/{acc_amt}/transactions", json=p_0)
passed_0 = (r_0.status_code == 422 and r_0.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("3. Amounts", "Amount: 0", "POST", f"/accounts/{acc_amt}/transactions", p_0, None, 422, "422 VALIDATION_ERROR (gt=0)", r_0.status_code, r_0.json(), passed_0)

# 3.2 Amount = negative
p_neg = {"type": "credit", "amount": -10.5, "reference_id": f"amt-neg-{uuid.uuid4().hex[:6]}"}
r_neg = session.post(f"{BASE_URL}/accounts/{acc_amt}/transactions", json=p_neg)
passed_neg = (r_neg.status_code == 422 and r_neg.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("3. Amounts", "Amount: negative (-10.5)", "POST", f"/accounts/{acc_amt}/transactions", p_neg, None, 422, "422 VALIDATION_ERROR (gt=0)", r_neg.status_code, r_neg.json(), passed_neg)

# 3.3 Amount = 0.001 (sub-cent decimal)
p_sub = {"type": "credit", "amount": 0.001, "reference_id": f"amt-sub-{uuid.uuid4().hex[:6]}"}
r_sub = session.post(f"{BASE_URL}/accounts/{acc_amt}/transactions", json=p_sub)
passed_sub = (r_sub.status_code == 422 and r_sub.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("3. Amounts", "Amount: 0.001 (sub-cent fractional)", "POST", f"/accounts/{acc_amt}/transactions", p_sub, None, 422, "422 VALIDATION_ERROR (max 2 decimal places)", r_sub.status_code, r_sub.json(), passed_sub)

# 3.4 Amount = 1e2
p_1e2 = {"type": "credit", "amount": 1e2, "reference_id": f"amt-1e2-{uuid.uuid4().hex[:6]}"}
r_1e2 = session.post(f"{BASE_URL}/accounts/{acc_amt}/transactions", json=p_1e2)
passed_1e2 = (r_1e2.status_code == 201 and r_1e2.json().get("amount") == 100.0)
record("3. Amounts", "Amount: 1e2 (scientific notation in JSON number)", "POST", f"/accounts/{acc_amt}/transactions", p_1e2, None, 201, "Parses as valid 100.0", r_1e2.status_code, r_1e2.json(), passed_1e2)

# 3.5 Amount = "10" (string)
p_str = {"type": "credit", "amount": "10", "reference_id": f"amt-str-{uuid.uuid4().hex[:6]}"}
r_str = session.post(f"{BASE_URL}/accounts/{acc_amt}/transactions", json=p_str)
passed_str = (r_str.status_code == 201 and r_str.json().get("amount") == 10.0)
record("3. Amounts", "Amount: \"10\" (string encoded number)", "POST", f"/accounts/{acc_amt}/transactions", p_str, None, 201, "Coerces decimal string \"10\" to 10.0", r_str.status_code, r_str.json(), passed_str)

# 3.6 Amount = null
p_null = {"type": "credit", "amount": None, "reference_id": f"amt-null-{uuid.uuid4().hex[:6]}"}
r_null = session.post(f"{BASE_URL}/accounts/{acc_amt}/transactions", json=p_null)
passed_null = (r_null.status_code == 422 and r_null.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("3. Amounts", "Amount: null", "POST", f"/accounts/{acc_amt}/transactions", p_null, None, 422, "422 VALIDATION_ERROR", r_null.status_code, r_null.json(), passed_null)

# 3.7 Amount = huge numbers (exceeding max_digits=15)
p_huge = {"type": "credit", "amount": 99999999999999999999, "reference_id": f"amt-huge-{uuid.uuid4().hex[:6]}"}
r_huge = session.post(f"{BASE_URL}/accounts/{acc_amt}/transactions", json=p_huge)
passed_huge = (r_huge.status_code == 422 and r_huge.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("3. Amounts", "Amount: huge number (> 15 digits)", "POST", f"/accounts/{acc_amt}/transactions", p_huge, None, 422, "422 VALIDATION_ERROR (max_digits=15)", r_huge.status_code, r_huge.json(), passed_huge)

# 3.8 0.1 added 10 times (precision / drift check)
acc_drift = create_account("Precision 0.1 Test")
for i in range(10):
    session.post(f"{BASE_URL}/accounts/{acc_drift}/transactions", json={"type": "credit", "amount": 0.1, "reference_id": f"drift-{i}-{uuid.uuid4().hex[:6]}"})
bal_drift = get_balance(acc_drift)
passed_drift = (bal_drift == 1.0)
record(
    "3. Amounts", "0.1 added 10 times (floating point precision check)",
    "POST", f"/accounts/{acc_drift}/transactions", "10x 0.1 credit", None,
    200, "Balance is exactly 1.0 without binary float drift",
    200, f"Balance: {bal_drift}", passed_drift, f"Final balance: {bal_drift}"
)


# ==========================================
# 4. Bad Input
# ==========================================
log("\n--- Category 4: Bad Input ---")
acc_bad = create_account("Bad Input Test")

# 4.1 Missing fields (type, amount, reference_id, name)
bad_cases = [
    ("Missing type", {"amount": 50.0, "reference_id": "ref-m1"}, f"/accounts/{acc_bad}/transactions"),
    ("Missing amount", {"type": "credit", "reference_id": "ref-m2"}, f"/accounts/{acc_bad}/transactions"),
    ("Missing reference_id", {"type": "credit", "amount": 50.0}, f"/accounts/{acc_bad}/transactions"),
    ("Account creation missing name", {}, "/accounts"),
]
for desc, b_payload, endpoint in bad_cases:
    rb = session.post(f"{BASE_URL}{endpoint}", json=b_payload)
    p_b = (rb.status_code == 422 and rb.json().get("error", {}).get("code") == "VALIDATION_ERROR")
    record("4. Bad input", desc, "POST", endpoint, b_payload, None, 422, "422 VALIDATION_ERROR", rb.status_code, rb.json(), p_b)

# 4.2 Extra fields (extra="forbid")
extra_p = {"name": "Charlie", "balance": 1000.0, "is_admin": True}
rb_extra = session.post(f"{BASE_URL}/accounts", json=extra_p)
p_extra = (rb_extra.status_code == 422 and rb_extra.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("4. Bad input", "Extra fields on account creation (client trying to set balance)", "POST", "/accounts", extra_p, None, 422, "422 VALIDATION_ERROR (extra forbidden)", rb_extra.status_code, rb_extra.json(), p_extra)

extra_tx = {"type": "credit", "amount": 10.0, "reference_id": f"ref-extra-{uuid.uuid4().hex[:6]}", "status": "approved"}
rb_extra_tx = session.post(f"{BASE_URL}/accounts/{acc_bad}/transactions", json=extra_tx)
p_extra_tx = (rb_extra_tx.status_code == 422 and rb_extra_tx.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("4. Bad input", "Extra fields on transaction creation", "POST", f"/accounts/{acc_bad}/transactions", extra_tx, None, 422, "422 VALIDATION_ERROR", rb_extra_tx.status_code, rb_extra_tx.json(), p_extra_tx)

# 4.3 Wrong types (amount as boolean, name as integer)
rb_type1 = session.post(f"{BASE_URL}/accounts/{acc_bad}/transactions", json={"type": "credit", "amount": True, "reference_id": f"ref-w1-{uuid.uuid4().hex[:6]}"})
p_type1 = (rb_type1.status_code == 422 and rb_type1.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("4. Bad input", "Wrong type: amount as boolean True", "POST", f"/accounts/{acc_bad}/transactions", {"amount": True}, None, 422, "422 VALIDATION_ERROR", rb_type1.status_code, rb_type1.json(), p_type1)

rb_type2 = session.post(f"{BASE_URL}/accounts", json={"name": 12345})
# Pydantic StringConstraints with int: does it reject or coerce?
p_type2 = (rb_type2.status_code in (422, 201))
record("4. Bad input", "Wrong type: name as integer 12345", "POST", "/accounts", {"name": 12345}, None, "422 or coerced string", "Type handled without 500 error", rb_type2.status_code, rb_type2.json(), p_type2)

# 4.4 Empty or whitespace strings
rb_ws1 = session.post(f"{BASE_URL}/accounts", json={"name": "   "})
p_ws1 = (rb_ws1.status_code == 422 and rb_ws1.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("4. Bad input", "Whitespace string: name='   '", "POST", "/accounts", {"name": "   "}, None, 422, "422 VALIDATION_ERROR (min_length=1 after strip)", rb_ws1.status_code, rb_ws1.json(), p_ws1)

rb_ws2 = session.post(f"{BASE_URL}/accounts/{acc_bad}/transactions", json={"type": "credit", "amount": 10.0, "reference_id": "   "})
p_ws2 = (rb_ws2.status_code == 422 and rb_ws2.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("4. Bad input", "Whitespace string: reference_id='   '", "POST", f"/accounts/{acc_bad}/transactions", {"reference_id": "   "}, None, 422, "422 VALIDATION_ERROR (min_length=1 after strip)", rb_ws2.status_code, rb_ws2.json(), p_ws2)

# 4.5 10,000 character strings
long_str = "A" * 10000
rb_long = session.post(f"{BASE_URL}/accounts", json={"name": long_str})
p_long = (rb_long.status_code == 422 and rb_long.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("4. Bad input", "10,000 character string for account name", "POST", "/accounts", {"name": "A*10000"}, None, 422, "422 VALIDATION_ERROR (max_length=100)", rb_long.status_code, rb_long.json(), p_long)

rb_long_ref = session.post(f"{BASE_URL}/accounts/{acc_bad}/transactions", json={"type": "credit", "amount": 10.0, "reference_id": long_str})
p_long_ref = (rb_long_ref.status_code == 422 and rb_long_ref.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("4. Bad input", "10,000 character string for reference_id", "POST", f"/accounts/{acc_bad}/transactions", {"reference_id": "A*10000"}, None, 422, "422 VALIDATION_ERROR (max_length=100)", rb_long_ref.status_code, rb_long_ref.json(), p_long_ref)

# 4.6 SQL injection payload
sql_name = "Robert'); DROP TABLE accounts;--"
rb_sql = session.post(f"{BASE_URL}/accounts", json={"name": sql_name})
p_sql = (rb_sql.status_code == 201 and rb_sql.json().get("name") == sql_name)
rb_check = session.get(f"{BASE_URL}/accounts")
p_sql = p_sql and (rb_check.status_code == 200)
record("4. Bad input", "SQL injection string in name", "POST", "/accounts", {"name": sql_name}, None, 201, "Account created safely; parameterized query prevents SQL injection", rb_sql.status_code, rb_sql.json(), p_sql)

# 4.7 Emoji in text fields
emoji_name = "Alice 🚀💎✨"
rb_emoji = session.post(f"{BASE_URL}/accounts", json={"name": emoji_name})
p_emoji = (rb_emoji.status_code == 201 and rb_emoji.json().get("name") == emoji_name)
record("4. Bad input", "Unicode / Emoji in account name", "POST", "/accounts", {"name": emoji_name}, None, 201, "Preserves unicode / emoji correctly", rb_emoji.status_code, rb_emoji.json(), p_emoji)

# 4.8 Invalid JSON body
headers_json = {"Content-Type": "application/json"}
rb_inv_json = session.post(f"{BASE_URL}/accounts", data="{not valid json: 'yes'", headers=headers_json)
p_inv_json = (rb_inv_json.status_code == 422 and rb_inv_json.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("4. Bad input", "Malformed JSON body syntax", "POST", "/accounts", "{not valid json: 'yes'", headers_json, 422, "422 VALIDATION_ERROR (not 500 or raw exception)", rb_inv_json.status_code, rb_inv_json.json() if rb_inv_json.headers.get("content-type") == "application/json" else rb_inv_json.text, p_inv_json)


# ==========================================
# 5. Partial Failure
# ==========================================
log("\n--- Category 5: Partial Failure ---")
acc_pf_a = create_account("Partial Failure Source A")
acc_pf_b = create_account("Partial Failure Dest B")
session.post(f"{BASE_URL}/accounts/{acc_pf_a}/transactions", json={"type": "credit", "amount": 100.0, "reference_id": f"seed-a-{uuid.uuid4().hex[:6]}"})
session.post(f"{BASE_URL}/accounts/{acc_pf_b}/transactions", json={"type": "credit", "amount": 50.0, "reference_id": "collision-ref-123"})

# Transfer 40.0 from A to B with reference_id "collision-ref-123"
# The debit on A will succeed in memory/query, but credit on B will fail with 409 DUPLICATE_TRANSACTION.
# SQLite transaction rollback must undo A's debit completely.
p_pf = {"from_account_id": acc_pf_a, "to_account_id": acc_pf_b, "amount": 40.0, "reference_id": "collision-ref-123"}
r_pf = session.post(f"{BASE_URL}/transfers", json=p_pf)
bal_pf_a = get_balance(acc_pf_a)
bal_pf_b = get_balance(acc_pf_b)
txs_pf_a = session.get(f"{BASE_URL}/accounts/{acc_pf_a}/transactions").json()["data"]
passed_pf = (r_pf.status_code == 409 and bal_pf_a == 100.0 and bal_pf_b == 50.0 and len(txs_pf_a) == 1)
record(
    "5. Partial failure", "Mid-transfer failure (destination collision rolls back source debit)",
    "POST", "/transfers", p_pf, None,
    409, "Transfer fails with 409; atomic rollback leaves source balance at 100.0 with 0 debits recorded",
    r_pf.status_code, r_pf.json(), passed_pf,
    f"Source balance: {bal_pf_a}, Dest balance: {bal_pf_b}, Source tx count: {len(txs_pf_a)}"
)


# ==========================================
# 6. Transfers
# ==========================================
log("\n--- Category 6: Transfers ---")
acc_t1 = create_account("Transfer Account 1")
acc_t2 = create_account("Transfer Account 2")
session.post(f"{BASE_URL}/accounts/{acc_t1}/transactions", json={"type": "credit", "amount": 200.0, "reference_id": f"seed-t1-{uuid.uuid4().hex[:6]}"})
session.post(f"{BASE_URL}/accounts/{acc_t2}/transactions", json={"type": "credit", "amount": 100.0, "reference_id": f"seed-t2-{uuid.uuid4().hex[:6]}"})

# 6.1 Transfer to self
p_self = {"from_account_id": acc_t1, "to_account_id": acc_t1, "amount": 20.0, "reference_id": f"self-{uuid.uuid4().hex[:6]}"}
r_self = session.post(f"{BASE_URL}/transfers", json=p_self)
p_self_pass = (r_self.status_code == 422 and r_self.json().get("error", {}).get("code") == "INVALID_TRANSFER")
record("6. Transfers", "Transfer to self (source == destination)", "POST", "/transfers", p_self, None, 422, "422 INVALID_TRANSFER", r_self.status_code, r_self.json(), p_self_pass)

# 6.2 Missing account
p_miss = {"from_account_id": acc_t1, "to_account_id": "non-existent-ghost-account", "amount": 20.0, "reference_id": f"miss-{uuid.uuid4().hex[:6]}"}
r_miss = session.post(f"{BASE_URL}/transfers", json=p_miss)
p_miss_pass = (r_miss.status_code == 404 and r_miss.json().get("error", {}).get("code") == "ACCOUNT_NOT_FOUND")
record("6. Transfers", "Transfer with missing destination account", "POST", "/transfers", p_miss, None, 404, "404 ACCOUNT_NOT_FOUND", r_miss.status_code, r_miss.json(), p_miss_pass)

# 6.3 Insufficient funds
p_insuf = {"from_account_id": acc_t2, "to_account_id": acc_t1, "amount": 500.0, "reference_id": f"insuf-{uuid.uuid4().hex[:6]}"}
r_insuf = session.post(f"{BASE_URL}/transfers", json=p_insuf)
p_insuf_pass = (r_insuf.status_code == 422 and r_insuf.json().get("error", {}).get("code") == "INSUFFICIENT_BALANCE")
record("6. Transfers", "Transfer exceeding balance (insufficient funds)", "POST", "/transfers", p_insuf, None, 422, "422 INSUFFICIENT_BALANCE", r_insuf.status_code, r_insuf.json(), p_insuf_pass)

# 6.4 Duplicate reference
ref_t_dup = f"tr-dup-{uuid.uuid4().hex[:6]}"
p_t_dup = {"from_account_id": acc_t1, "to_account_id": acc_t2, "amount": 10.0, "reference_id": ref_t_dup}
session.post(f"{BASE_URL}/transfers", json=p_t_dup)
r_t_dup2 = session.post(f"{BASE_URL}/transfers", json=p_t_dup)
p_t_dup_pass = (r_t_dup2.status_code == 409 and r_t_dup2.json().get("error", {}).get("code") == "DUPLICATE_TRANSACTION")
record("6. Transfers", "Duplicate reference on transfer", "POST", "/transfers", p_t_dup, None, 409, "409 DUPLICATE_TRANSACTION", r_t_dup2.status_code, r_t_dup2.json(), p_t_dup_pass)

# 6.5 A to B and B to A at the same time (no deadlock + conservation of money)
acc_dl_a = create_account("Deadlock A")
acc_dl_b = create_account("Deadlock B")
session.post(f"{BASE_URL}/accounts/{acc_dl_a}/transactions", json={"type": "credit", "amount": 500.0, "reference_id": f"seed-dla-{uuid.uuid4().hex[:6]}"})
session.post(f"{BASE_URL}/accounts/{acc_dl_b}/transactions", json={"type": "credit", "amount": 500.0, "reference_id": f"seed-dlb-{uuid.uuid4().hex[:6]}"})
initial_total = get_balance(acc_dl_a) + get_balance(acc_dl_b)

def transfer_a_to_b(i):
    s = requests.Session()
    return s.post(f"{BASE_URL}/transfers", json={
        "from_account_id": acc_dl_a, "to_account_id": acc_dl_b, "amount": 25.0, "reference_id": f"tr-ab-{i}-{uuid.uuid4().hex[:6]}"
    })

def transfer_b_to_a(i):
    s = requests.Session()
    return s.post(f"{BASE_URL}/transfers", json={
        "from_account_id": acc_dl_b, "to_account_id": acc_dl_a, "amount": 15.0, "reference_id": f"tr-ba-{i}-{uuid.uuid4().hex[:6]}"
    })

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = []
    for i in range(4):
        futures.append(executor.submit(transfer_a_to_b, i))
        futures.append(executor.submit(transfer_b_to_a, i))
    res_dl = [f.result() for f in as_completed(futures)]

dl_statuses = [r.status_code for r in res_dl]
final_a = get_balance(acc_dl_a)
final_b = get_balance(acc_dl_b)
final_total = final_a + final_b

passed_dl = (all(s == 201 for s in dl_statuses) and abs(final_total - initial_total) < 1e-6)
record(
    "6. Transfers", "Concurrent A->B and B->A transfers (deadlock avoidance & conservation of money)",
    "POST", "/transfers", "4x A->B (25.0) and 4x B->A (15.0) concurrent", None,
    "All 201, Total money conserved", "No deadlock, all transfers succeed (201), total system money preserved (1000.0)",
    f"Statuses: {set(dl_statuses)}, Total money: {final_total}",
    {"statuses": dl_statuses, "initial_total": initial_total, "final_total": final_total, "final_a": final_a, "final_b": final_b},
    passed_dl, f"Initial total: {initial_total}, Final total: {final_total}"
)


# ==========================================
# 7. Immutability
# ==========================================
log("\n--- Category 7: Immutability ---")
acc_imm = create_account("Immutability Test")
r_imm_tx = session.post(f"{BASE_URL}/accounts/{acc_imm}/transactions", json={"type": "credit", "amount": 100.0, "reference_id": f"imm-{uuid.uuid4().hex[:6]}"})
tx_id = r_imm_tx.json()["id"]

# 7.1 PUT
r_put = session.put(f"{BASE_URL}/accounts/{acc_imm}/transactions/{tx_id}", json={"amount": 999.0})
p_put = (r_put.status_code == 405 and r_put.json().get("error", {}).get("code") == "TRANSACTION_IMMUTABLE")
record("7. Immutability", "PUT /accounts/{id}/transactions/{tx_id}", "PUT", f"/accounts/{acc_imm}/transactions/{tx_id}", {"amount": 999.0}, None, 405, "405 Method Not Allowed / TRANSACTION_IMMUTABLE", r_put.status_code, r_put.json() if r_put.headers.get("content-type") == "application/json" else r_put.text, p_put)

# 7.2 PATCH
r_patch = session.patch(f"{BASE_URL}/accounts/{acc_imm}/transactions/{tx_id}", json={"amount": 999.0})
p_patch = (r_patch.status_code == 405 and r_patch.json().get("error", {}).get("code") == "TRANSACTION_IMMUTABLE")
record("7. Immutability", "PATCH /accounts/{id}/transactions/{tx_id}", "PATCH", f"/accounts/{acc_imm}/transactions/{tx_id}", {"amount": 999.0}, None, 405, "405 Method Not Allowed / TRANSACTION_IMMUTABLE", r_patch.status_code, r_patch.json() if r_patch.headers.get("content-type") == "application/json" else r_patch.text, p_patch)

# 7.3 DELETE
r_del = session.delete(f"{BASE_URL}/accounts/{acc_imm}/transactions/{tx_id}")
p_del = (r_del.status_code == 405 and r_del.json().get("error", {}).get("code") == "TRANSACTION_IMMUTABLE")
record("7. Immutability", "DELETE /accounts/{id}/transactions/{tx_id}", "DELETE", f"/accounts/{acc_imm}/transactions/{tx_id}", None, None, 405, "405 Method Not Allowed / TRANSACTION_IMMUTABLE", r_del.status_code, r_del.json() if r_del.headers.get("content-type") == "application/json" else r_del.text, p_del)


# ==========================================
# 9. History
# ==========================================
log("\n--- Category 9: History ---")
acc_hist = create_account("History Test")
for i in range(5):
    session.post(f"{BASE_URL}/accounts/{acc_hist}/transactions", json={"type": "credit", "amount": 10.0 * (i + 1), "reference_id": f"hist-{i}-{uuid.uuid4().hex[:6]}"})

# 9.1 page 0
r_p0 = session.get(f"{BASE_URL}/accounts/{acc_hist}/transactions?page=0")
p_p0 = (r_p0.status_code == 422 and r_p0.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("9. History", "History query with page=0", "GET", f"/accounts/{acc_hist}/transactions?page=0", None, None, 422, "422 VALIDATION_ERROR (page >= 1)", r_p0.status_code, r_p0.json(), p_p0)

# 9.2 page past the end
r_past = session.get(f"{BASE_URL}/accounts/{acc_hist}/transactions?page=999&limit=10")
body_past = r_past.json()
p_past = (r_past.status_code == 200 and body_past.get("data") == [] and body_past.get("pagination", {}).get("total_records") == 5)
record("9. History", "History query with page past the end (page=999)", "GET", f"/accounts/{acc_hist}/transactions?page=999&limit=10", None, None, 200, "200 with data=[] and total_records=5", r_past.status_code, body_past, p_past)

# 9.3 limit 0
r_lim0 = session.get(f"{BASE_URL}/accounts/{acc_hist}/transactions?limit=0")
p_lim0 = (r_lim0.status_code == 422 and r_lim0.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("9. History", "History query with limit=0", "GET", f"/accounts/{acc_hist}/transactions?limit=0", None, None, 422, "422 VALIDATION_ERROR (limit >= 1)", r_lim0.status_code, r_lim0.json(), p_lim0)

# 9.4 limit 101
r_lim101 = session.get(f"{BASE_URL}/accounts/{acc_hist}/transactions?limit=101")
p_lim101 = (r_lim101.status_code == 422 and r_lim101.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("9. History", "History query with limit=101", "GET", f"/accounts/{acc_hist}/transactions?limit=101", None, None, 422, "422 VALIDATION_ERROR (limit <= 100)", r_lim101.status_code, r_lim101.json(), p_lim101)

# 9.5 invalid type
r_inv_type = session.get(f"{BASE_URL}/accounts/{acc_hist}/transactions?type=invalid_type")
p_inv_type = (r_inv_type.status_code == 422 and r_inv_type.json().get("error", {}).get("code") == "VALIDATION_ERROR")
record("9. History", "History query with invalid type parameter (?type=invalid_type)", "GET", f"/accounts/{acc_hist}/transactions?type=invalid_type", None, None, 422, "422 VALIDATION_ERROR", r_inv_type.status_code, r_inv_type.json(), p_inv_type)

# 9.6 Ordering with same-time transactions
acc_time = create_account("Same Time Order Test")
refs_time = []
for i in range(4):
    ref_t = f"time-{i}-{uuid.uuid4().hex[:6]}"
    refs_time.append(ref_t)
    session.post(f"{BASE_URL}/accounts/{acc_time}/transactions", json={"type": "credit", "amount": 10.0, "reference_id": ref_t})

r_order = session.get(f"{BASE_URL}/accounts/{acc_time}/transactions?limit=10")
data_order = r_order.json().get("data", [])
returned_refs = [t["reference_id"] for t in data_order]
expected_order = list(reversed(refs_time))
p_order = (r_order.status_code == 200 and returned_refs == expected_order)
record(
    "9. History", "Ordering with rapidly added same-time transactions",
    "GET", f"/accounts/{acc_time}/transactions?limit=10", None, None,
    200, f"Deterministic newest-first order: {expected_order}",
    r_order.status_code, returned_refs, p_order, f"Returned: {returned_refs}"
)


# ==========================================
# 10. Error format
# ==========================================
log("\n--- Category 10: Error Format ---")
error_cases = [
    ("404 Account Not Found", session.get(f"{BASE_URL}/accounts/non-existent-acc-123/balance")),
    ("422 Validation Error", session.post(f"{BASE_URL}/accounts", json={})),
    ("409 Duplicate Transaction", session.post(f"{BASE_URL}/accounts/{acc1}/transactions", json=p2)),
    ("405 Immutability Error", session.delete(f"{BASE_URL}/accounts/{acc_imm}/transactions/{tx_id}")),
]

for err_label, resp in error_cases:
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    shape_ok = is_error_shape_valid(body)
    record(
        "10. Error format", f"Error shape verification: {err_label}",
        "VARIOUS", "VARIOUS", None, None,
        resp.status_code, "Standard shape {'error': {'code': str, 'message': str, 'details': ...}}, no stack traces",
        resp.status_code, body, shape_ok,
        "Consistent error format verified" if shape_ok else "Invalid error format or trace leaked"
    )


# ==========================================
# 8. Reconciliation
# ==========================================
log("\n--- Category 8: Reconciliation ---")
r_all_acc = session.get(f"{BASE_URL}/accounts")
assert r_all_acc.status_code == 200, "Failed to list accounts"
accounts_list = r_all_acc.json()

reconciliation_failures = []
total_reconciled = 0

for a in accounts_list:
    acc_id = a["id"]
    acc_name = a["name"]
    bal_api = get_balance(acc_id)
    
    # fetch transactions
    rh = session.get(f"{BASE_URL}/accounts/{acc_id}/transactions?limit=100")
    if rh.status_code != 200:
        continue
    h_data = rh.json()
    tx_list = h_data.get("data", [])
    
    cred = sum(Decimal(str(t["amount"])) for t in tx_list if t["type"] == "credit")
    deb = sum(Decimal(str(t["amount"])) for t in tx_list if t["type"] == "debit")
    computed_balance = float(cred - deb)
    
    diff = abs(computed_balance - bal_api)
    total_reconciled += 1
    if diff > 1e-4:
        reconciliation_failures.append({
            "account_id": acc_id,
            "name": acc_name,
            "api_balance": bal_api,
            "computed_balance": computed_balance,
            "credits_sum": float(cred),
            "debits_sum": float(deb),
            "diff": diff
        })

recon_passed = (len(reconciliation_failures) == 0)
record(
    "8. Reconciliation", f"Full ledger reconciliation across all {total_reconciled} accounts",
    "GET", "/accounts, /accounts/{id}/balance, /accounts/{id}/transactions", None, None,
    200, f"balance == sum(credits) - sum(debits) with 0 mismatches across all accounts",
    200, f"Reconciled {total_reconciled} accounts, mismatches: {len(reconciliation_failures)}",
    recon_passed,
    f"Mismatches: {reconciliation_failures}" if reconciliation_failures else f"All {total_reconciled} accounts reconciled with 0 mismatches."
)

log("\n==================================================")
log("  TEST SUITE COMPLETED")
log("==================================================")
summary = {
    "total": len(results),
    "passed": sum(1 for r in results if r["status"] == "PASS"),
    "failed": sum(1 for r in results if r["status"] == "FAIL"),
    "results": results,
    "reconciliation_failures": reconciliation_failures
}

with open("qa_results_final.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

log(f"Total: {summary['total']} | Passed: {summary['passed']} | Failed: {summary['failed']}")
