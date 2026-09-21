"""Seed constants and configurations for TallyFlow."""
from __future__ import annotations

SEED = 42

CUSTOMERS = [
    {"id": "CUST-1001", "name": "Acme Incorporated", "legal_name": "Acme Incorporated", "industry": "Manufacturing", "country": "USA", "currency": "USD", "customer_tier": "Enterprise", "payment_terms": "NET30", "credit_limit": 75000},
    {"id": "CUST-1002", "name": "Bluepeak Logistics GmbH", "legal_name": "Bluepeak Logistics GmbH", "industry": "Logistics", "country": "DEU", "currency": "USD", "customer_tier": "Enterprise", "payment_terms": "NET15", "credit_limit": 60000},
    {"id": "CUST-1003", "name": "Corvus Analytics LLC", "legal_name": "Corvus Analytics LLC", "industry": "Technology", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 35000},
    {"id": "CUST-1004", "name": "Dunmore Retail Group", "legal_name": "Dunmore Retail Group Ltd", "industry": "Retail", "country": "IRL", "currency": "EUR", "payment_terms": "NET30", "customer_tier": "Enterprise", "credit_limit": 80000},
    {"id": "CUST-1005", "name": "Eastport Marine Services", "legal_name": "Eastport Marine Services Inc", "industry": "Maritime", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 40000},
    {"id": "CUST-1006", "name": "Fenwick & Associates", "legal_name": "Fenwick & Associates LLP", "industry": "Legal", "country": "USA", "currency": "USD", "customer_tier": "Premium", "payment_terms": "NET45", "credit_limit": 50000},
    {"id": "CUST-1007", "name": "Greenfield Agricultural", "legal_name": "Greenfield Agricultural Co", "industry": "Agriculture", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 30000},
    {"id": "CUST-1008", "name": "Horizon Digital Media", "legal_name": "Horizon Digital Media Inc", "industry": "Media", "country": "USA", "currency": "USD", "customer_tier": "Growth", "payment_terms": "NET15", "credit_limit": 25000},
    {"id": "CUST-1009", "name": "Ironclad Security Systems", "legal_name": "Ironclad Security Systems LLC", "industry": "Security", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 45000},
    {"id": "CUST-1010", "name": "Juniper Biotech", "legal_name": "Juniper Biotechnology Corp", "industry": "Biotech", "country": "USA", "currency": "USD", "customer_tier": "Enterprise", "payment_terms": "NET30", "credit_limit": 100000},
    {"id": "CUST-1011", "name": "Kelvin Thermal Solutions", "legal_name": "Kelvin Thermal Solutions Inc", "industry": "Manufacturing", "country": "USA", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 35000},
    {"id": "CUST-1012", "name": "Lumen Cloud Consulting", "legal_name": "Lumen Cloud Consulting LLC", "industry": "Technology", "country": "USA", "currency": "USD", "customer_tier": "Growth", "payment_terms": "NET15", "credit_limit": 20000},
    {"id": "CUST-1013", "name": "Meridian Healthcare", "legal_name": "Meridian Healthcare Partners", "industry": "Healthcare", "country": "USA", "currency": "USD", "customer_tier": "Premium", "payment_terms": "NET45", "credit_limit": 90000},
    {"id": "CUST-1014", "name": "Northwind Shipping Co", "legal_name": "Northwind Shipping Co Ltd", "industry": "Logistics", "country": "GBR", "currency": "USD", "customer_tier": "Standard", "payment_terms": "NET30", "credit_limit": 55000},
    {"id": "CUST-1015", "name": "Oakmont Financial Group", "legal_name": "Oakmont Financial Group Inc", "industry": "Finance", "country": "USA", "currency": "USD", "customer_tier": "Enterprise", "payment_terms": "NET30", "credit_limit": 120000},
]

ACCOUNTS = [
    {"id": "ACCT-1100", "code": "1100", "name": "Cash - Operating USD", "account_type": "Asset", "normal_balance": "debit"},
    {"id": "ACCT-1200", "code": "1200", "name": "Accounts Receivable", "account_type": "Asset", "normal_balance": "debit"},
    {"id": "ACCT-1210", "code": "1210", "name": "Allowance for Doubtful Accounts", "account_type": "Asset", "normal_balance": "credit"},
    {"id": "ACCT-2100", "code": "2100", "name": "Accounts Payable", "account_type": "Liability", "normal_balance": "credit"},
    {"id": "ACCT-4100", "code": "4100", "name": "Revenue - Product Sales", "account_type": "Revenue", "normal_balance": "credit"},
    {"id": "ACCT-4200", "code": "4200", "name": "Revenue - Services", "account_type": "Revenue", "normal_balance": "credit"},
    {"id": "ACCT-5100", "code": "5100", "name": "Discount Expense", "account_type": "Expense", "normal_balance": "debit"},
    {"id": "ACCT-5200", "code": "5200", "name": "Bad Debt Expense", "account_type": "Expense", "normal_balance": "debit"},
    {"id": "ACCT-5300", "code": "5300", "name": "Bank Fees", "account_type": "Expense", "normal_balance": "debit"},
    {"id": "ACCT-3100", "code": "3100", "name": "Retained Earnings", "account_type": "Equity", "normal_balance": "credit"},
]

DISCREPANCY_TYPES = [
    ("UNDOCUMENTED_DISCOUNT", "HIGH", "Accounts Receivable"),
    ("PARTIAL_PAYMENT", "MEDIUM", "Accounts Receivable"),
    ("DUPLICATE_PAYMENT", "CRITICAL", "Cash - Operating USD"),
    ("OVERPAYMENT", "HIGH", "Cash - Operating USD"),
    ("TIMING_DIFFERENCE", "LOW", "Accounts Receivable"),
    ("BANK_FEE", "LOW", "Cash - Operating USD"),
    ("MISSING_PAYMENT", "HIGH", "Accounts Receivable"),
    ("CURRENCY_MISMATCH", "MEDIUM", "Cash - Operating USD"),
]
