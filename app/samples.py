"""Representative (synthetic, anonymised) inputs used in the UI and the evaluation."""

THREAD_SETTLEMENT = """From: J. Patel, Settlements Analyst, Blue Ridge Power LLC
To: Market Operations Support
Subject: Dispute - real-time balancing operating reserve credit, ticket MO-48213

Hello Market Ops team,
We are formally disputing the balancing operating reserve credit for our Westfall combustion turbine (Unit 2) for operating day 2026-08-14. The unit was dispatched by PJM above its economic minimum from HE15 to HE19 during the hot-weather alert and ran at 210 MW, but the operating reserve credit on the settlement statement is zero. Our shadow settlement calculates a credit of approximately $48,350.00 based on our cost-based offer and the real-time LMP at WESTFALL 230KV GEN1.
We already checked that our real-time offer was submitted before the deadline and that the meter data for those hours was accepted (1,050 MWh total). Our finance team is closing the August books and invoice INV-604118 is due next week.
Could you confirm whether the unit was flagged as self-scheduled for those hours, and what the deadline is to submit a billing line item dispute? Please also tell us what supporting documentation you need.
Thanks,
J. Patel"""

THREAD_METER = """From: R. Chen, Metering Lead, Susquehanna Hydro LLC
Subject: Meter correction needed for SUNBURY 500KV tie-line, July

Team, following up on our call. During July our RTU at the SUNBURY 500KV interconnection lost communication for several days. The revenue meter kept recording, but the hourly values uploaded to Power Meter for 2026-07-09 through 2026-07-12 were estimated by our system and are low by roughly 12%. We now have the actual interval data from the revenue meter (4,320 MWh for the period). We would like to replace the estimated values before the meter correction window closes and want to understand how the resubmission will flow into the 60-day reconciliation and whether our July invoice will be rebilled. Please advise on the correct procedure and any form required."""

SHORT_TICKETS = [
    "Our letter of credit for $2,500,000.00 expires on 2026-11-15. What is the process to submit a replacement without breaching our credit limit?",
    "Markets Gateway rejected our day-ahead offer for Battery Block A at the 2026-09-03 market close with a validation error on the state-of-charge parameter.",
    "Invoice INV-551902 for September shows administrative charges 18% higher than August; please provide a breakdown.",
    "CT-3 tripped at HE14 on 2026-09-21 due to a transformer fault at BRIDGEPORT 138KV; we submitted a forced outage ticket for 180 MW.",
]

RAG_QUESTIONS = [
    "How is balancing operating reserve credit calculated for a generator dispatched in real time?",
    "What is the deadline for submitting a billing dispute?",
    "How are meter data corrections handled in the reconciliation process?",
    "What happens if a capacity resource does not perform during a performance assessment interval?",
    "When is the day-ahead energy market offer submission deadline?",
]
