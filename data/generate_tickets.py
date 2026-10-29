"""Generate a synthetic, anonymised dataset of electricity-market support tickets.

Real market-participant tickets are confidential, so we synthesise tickets that
mirror the structure and vocabulary of an ISO/RTO market-operations help desk.
Each category has several templates. Two templates per category are held out
entirely for the test split, so the test set measures generalisation to unseen
phrasings rather than memorisation of templates.

Usage:  python data/generate_tickets.py  ->  data/tickets_{train,val,test}.csv
"""
import csv
import random
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent

PARTICIPANTS = [
    "Blue Ridge Power LLC", "Keystone Renewables Inc", "Allegheny Peak Energy",
    "Tri-State Wind Partners", "Chesapeake Storage Co", "Ohio Valley Generation",
    "Lakeshore Municipal Utility", "Piedmont Solar Holdings", "Great Lakes Trading LP",
    "Susquehanna Hydro LLC", "Northern Neck Electric Coop", "Delmarva Demand Response",
]
NODES = ["BRIDGEPORT 138KV", "WESTFALL 230KV GEN1", "MILLCREEK 69KV LOAD",
         "AEP ZONE", "DOM ZONE", "PECO ZONE", "COMED HUB", "WESTERN HUB",
         "EASTERN HUB", "SUNBURY 500KV", "HARMONY SOLAR 34KV"]
UNITS = ["Unit 1", "Unit 2", "CT-3", "Battery Block A", "Wind Farm Ph II", "Solar Array 4"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October"]
NAMES = ["J. Patel", "M. Alvarez", "S. Okafor", "R. Chen", "L. Novak", "D. Brooks"]

OPENERS = ["", "Hello Market Ops team, ", "Hi, ", "Good morning, ", "Team, ",
           "To whom it may concern, ", "Urgent: ", "Following up on our call, "]
CLOSERS = ["", " Please advise.", " Thanks.", " Appreciate a quick response.",
           " Let us know if you need more data.", " Kind regards.",
           " This is impacting our month-end close."]


def rnd_date():
    return f"2026-{random.randint(1, 9):02d}-{random.randint(1, 28):02d}"


def fill(t):
    return t.format(
        p=random.choice(PARTICIPANTS), node=random.choice(NODES), unit=random.choice(UNITS),
        date=rnd_date(), he=random.randint(1, 24), he2=random.randint(1, 24),
        amt=f"{random.randint(1, 950):,}{random.choice(['', ',000'])}.{random.randint(0, 99):02d}",
        mw=random.randint(5, 650), mwh=random.randint(10, 9000),
        month=random.choice(MONTHS), inv=f"INV-{random.randint(100000, 999999)}",
        tk=f"MO-{random.randint(10000, 99999)}", name=random.choice(NAMES),
        pct=random.randint(2, 40), price=f"{random.randint(15, 1800)}.{random.randint(0, 99):02d}",
    )


# category -> list of templates; the LAST TWO of each list are held out for test.
TEMPLATES = {
    "settlement_dispute": [
        "We are disputing the real-time energy settlement for {p} at {node} on {date} HE{he}. Our shadow settlement shows a variance of ${amt} versus the posted charge.",
        "The balancing operating reserve credit for {unit} on {date} looks wrong; we expected roughly ${amt} but received nothing. Requesting a settlement review.",
        "Formal dispute: day-ahead congestion charges for {p} on {date} were calculated using the wrong LMP at {node}. Impact is ${amt}.",
        "Our make-whole payment for {unit} for operating day {date} was not credited. The unit was dispatched by PJM above its economic minimum from HE{he} to HE{he2}.",
        "Please reopen settlement for {date}. The real-time deviation charge of ${amt} assessed to {p} does not match our metered values at {node}.",
        "The lost opportunity cost credit for {unit} on {date} appears understated by about ${amt}; we were manually curtailed by {mw} MW in HE{he}.",
        "We believe the {month} reconciliation statement over-allocated uplift to {p}. Our calculation differs by ${amt} and we want to file a dispute.",
        "Settlement for {node} on {date} used an incorrect price of ${price}/MWh in HE{he}; the posted LMP was different. Kindly correct and rebill.",
    ],
    "meter_data_correction": [
        "We need to correct meter data for {unit} at {node} for {date}. Revenue meter reported {mwh} MWh for HE{he} but the backup meter shows a {pct}% difference.",
        "Submitting corrected interval meter values for {p}; the original upload on {date} had HE{he} through HE{he2} zeroed out due to an RTU communication failure.",
        "Our Power Meter submission for {month} contains a CT ratio error at {node}. Please allow a resubmission of hourly MWh values.",
        "The meter correction window for {date} is closing. {p} needs to replace estimated load values with actuals ({mwh} MWh total).",
        "The tie-line meter between our zone and {node} drifted on {date}; telemetry is off by {mw} MW. How do we submit adjusted values?",
        "Load reconciliation for {month} shows {mwh} MWh unaccounted for at {node}; we suspect a duplicated meter channel in the data submission.",
        "Our generator's net output was double counted on {date} HE{he} because the auxiliary load meter and the gross meter were both mapped to {unit}.",
        "Requesting to revise the eMTR values for {unit} for {month}; scaling factor was applied twice so reported energy is inflated by {pct}%.",
    ],
    "bid_offer_submission": [
        "Our day-ahead offer for {unit} was rejected at the {date} market close with a validation error on the cost-based schedule. We could not resubmit before the deadline.",
        "Markets Gateway did not accept our virtual bids at {node} for {date}; the upload file with {mw} MW of INCs returned a schema error.",
        "{p} accidentally submitted an offer curve with a ${price}/MWh price cap for {unit}. Can the offer be corrected before the day-ahead market clears?",
        "The real-time offer update for {unit} for HE{he} on {date} did not take effect; the unit was still dispatched on the old curve.",
        "We need to update the economic maximum for {unit} to {mw} MW starting {date}, but the parameter-limited schedule will not save.",
        "Our demand bid at {node} for {date} cleared at {mwh} MWh, far above what we entered; we suspect the bid segments were parsed incorrectly.",
        "Our battery storage offer for {unit} on {date} keeps failing because the state-of-charge parameters are flagged as out of range.",
        "The no-load and startup costs on our offer for {unit} were zeroed after the template upload on {date}; we need the cost-based offer restored.",
    ],
    "billing_invoice": [
        "Invoice {inv} for {month} for {p} shows a total of ${amt}, which does not match the sum of the billing line items. Please send a corrected invoice.",
        "We have not received the weekly billing statement for the week ending {date}. Our AP team needs invoice {inv} to process payment.",
        "Can you explain line item 1250 on invoice {inv}? {p} was charged ${amt} for transmission enhancement and we cannot trace it.",
        "Payment for invoice {inv} was wired on {date} but our account still shows ${amt} outstanding.",
        "The monthly invoice for {month} lists {p} under the wrong billing entity; please reissue {inv} with the correct legal name.",
        "Our finance team needs a breakdown of the ${amt} in administrative charges on invoice {inv}; the total increased {pct}% month over month.",
        "We received two invoices ({inv} and a duplicate) for {month} with the same charges of ${amt}. Please void the duplicate.",
        "The billing line for regulation market credits is missing from invoice {inv}; {p} provided {mw} MW of regulation during {month}.",
    ],
    "credit_collateral": [
        "We received a collateral call for {p} of ${amt} on {date}. Please explain how the credit requirement was calculated.",
        "{p} would like to increase its unsecured credit allowance; attached are our latest audited financials.",
        "Our letter of credit for ${amt} expires on {date}. What is the process to submit a replacement without breaching the credit limit?",
        "The FTR credit requirement for {p} jumped by {pct}% after the auction; we need clarity before posting additional collateral.",
        "We were notified that {p} is approaching its credit limit of ${amt}. Can virtual bidding screening be relaxed while we post cash?",
        "Please confirm receipt of the ${amt} cash collateral wire sent on {date} and update our available credit.",
        "Our peak market activity credit requirement for {month} seems to include exposure from a terminated position; it is overstated by ${amt}.",
        "The guaranty from our parent company for {p} needs to be amended to ${amt}; which credit form should we use?",
    ],
    "capacity_market": [
        "{p} needs to confirm the capacity performance commitment of {unit} for the {month} delivery period; our installed capacity value appears reduced by {mw} MW.",
        "We want to submit a sell offer for {unit} in the upcoming Base Residual Auction but the unforced capacity value is not available in the capacity system.",
        "A capacity performance penalty of ${amt} was assessed to {p} for the event on {date}; we believe {unit} was on an approved outage.",
        "Requesting a capacity transfer of {mw} MW from {unit} to a replacement resource for the remainder of the delivery year.",
        "Our ELCC class rating for {unit} changed and reduced our accredited capacity by {pct}%. Where is the methodology documented?",
        "{p} wants to cover a capacity shortfall of {mw} MW through a bilateral transaction; how do we register it before the deadline on {date}?",
        "The non-performance charge for {unit} during the performance assessment interval on {date} HE{he} looks inconsistent with our telemetry.",
        "We need to request a must-offer exception for {unit} for the next auction because of a planned deactivation.",
    ],
    "system_access": [
        "User {name} at {p} cannot log in to Markets Gateway; the account was locked after the password reset on {date}.",
        "Our API client certificate for the settlements data feed expired on {date} and all automated downloads are failing with 401 errors.",
        "Please grant {name} read access to the billing and settlement reports for {p}; the access request has been pending since {date}.",
        "The account manager role for {p} needs to be transferred to {name}; the previous CAM has left the company.",
        "We are seeing HTTP 503 errors from the data miner API when pulling LMP data for {node}; is there an outage?",
        "{name} received a multi-factor authentication error on {date} and cannot access the outage reporting tool.",
        "Our SFTP job for downloading settlement statements started failing on {date} with a host key mismatch.",
        "New employee {name} at {p} needs a token and role assignment for the capacity system before {date}.",
    ],
    "outage_reporting": [
        "{unit} tripped at HE{he} on {date} due to a transformer fault at {node}; we have submitted a forced outage ticket for {mw} MW.",
        "We need to extend the planned outage for {unit} from {date} by five days because of turbine inspection findings.",
        "Our maintenance outage request for {unit} on {date} was denied for reliability reasons; can we reschedule?",
        "{p} reports a partial derate of {mw} MW on {unit} starting HE{he} on {date} due to high ambient temperature.",
        "The outage ticket for {unit} still shows as active although the unit returned to service at HE{he} on {date}.",
        "Please reclassify the {date} event on {unit} from forced outage to an outside-management-control event; the cause was a transmission line failure at {node}.",
        "Fuel supply interruption caused {unit} to be unavailable for {mw} MW from HE{he} on {date}; how should we log this?",
        "We are planning a {mw} MW deactivation of {unit} next year and need to know the notice requirements for outage scheduling.",
    ],
}


def make(n_per_template, templates):
    rows = []
    for label, tpl_list in templates.items():
        for t in tpl_list:
            for _ in range(n_per_template):
                text = random.choice(OPENERS) + fill(t) + random.choice(CLOSERS)
                rows.append({"text": text, "label": label})
    random.shuffle(rows)
    return rows


def write(rows, name):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label"])
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


if __name__ == "__main__":
    seen = {k: v[:-2] for k, v in TEMPLATES.items()}
    held_out = {k: v[-2:] for k, v in TEMPLATES.items()}
    pool = make(45, seen)
    split = int(len(pool) * 0.85)
    write(pool[:split], "tickets_train.csv")
    write(pool[split:], "tickets_val.csv")
    write(make(25, held_out), "tickets_test.csv")
