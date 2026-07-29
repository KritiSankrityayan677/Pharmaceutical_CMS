"""
Generate realistic sample pharmaceutical complaints for the demo.

Run once:
    python generate_samples.py

Writes PDFs and one .eml into ./sample_complaints/.
Sample #1 matches the reference video's "Zenith Life Sciences / Metformin
API drum foreign matter" scenario so your demo mirrors theirs closely.
"""
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


OUT_DIR = Path(__file__).parent / "sample_complaints"
OUT_DIR.mkdir(exist_ok=True)


COMPLAINTS = [
    {
        "filename": "Fictional_Pharma_Customer_Complaint_01.pdf",
        "title": "Customer Complaint Report - CC-2026-00154",
        "body": [
            "<b>Complaint Reference:</b> CC-2026-00154",
            "<b>To:</b> Quality Assurance, Zenith Life Sciences Ltd.",
            "<b>From:</b> ABC Formulations Ltd., Ahmedabad, Gujarat, India",
            "<b>Contact:</b> quality@abcformulations.co.in",
            "<b>Complaint Source:</b> Email",
            "<b>Complaint Date:</b> 22 July 2026",
            "",
            "<b>Product:</b> Metformin Hydrochloride API",
            "<b>Product Strength / Grade:</b> USP grade, 99.5% assay",
            "<b>Batch / LOT Number:</b> BMX240602",
            "<b>Manufacturing date:</b> June 2024",
            "<b>Expiry date:</b> May 2027",
            "<b>Quantity affected:</b> 48 capsules (samples drawn from the affected HDPE drum)",
            "",
            "<b>Complaint Type:</b> Product Quality",
            "<b>Complaint Category:</b> Foreign Matter Contamination",
            "",
            "<b>Detailed complaint description:</b>",
            "ABC Formulations Ltd. reports multiple dark foreign particles inside one sealed "
            "HDPE drum during incoming quality inspection. The drum had no visible external damage. "
            "Particles are approximately 1-3 mm in size, distributed through the top 5 cm of the powder bed. "
            "Sampling from the drum was performed per SOP QC-SAM-014 and 48 capsules were filled from the "
            "affected sub-sample for verification testing. Material has been quarantined at receiving. "
            "No downstream formulation batch has yet been produced from this drum. "
            "Requesting urgent investigation, retention-sample analysis, and confirmation of "
            "whether the same lot may have been shipped to other customers.",
        ],
    },
    {
        "filename": "complaint_02_broken_tablets.pdf",
        "title": "Customer Complaint - Broken Tablets in Blister",
        "body": [
            "<b>To:</b> QA Complaints Team",
            "<b>From:</b> Wellness Pharmacy, Mumbai, India",
            "<b>Contact:</b> Mr. Rakesh Iyer, Pharmacist-in-charge, +91-98200-11234",
            "<b>Complaint Source:</b> Distributor Report",
            "<b>Complaint Date:</b> 21 July 2026",
            "",
            "<b>Product:</b> Metformin Hydrochloride Tablets IP",
            "<b>Product Strength / Grade:</b> 500 mg",
            "<b>Batch / LOT Number:</b> MET50-25A0301",
            "<b>Manufacturing:</b> March 2025",
            "<b>Expiry:</b> February 2027",
            "<b>Quantity affected:</b> Approximately 12 tablets across 2 blister strips of a 10 x 10 pack",
            "",
            "<b>Complaint Type:</b> Product Quality",
            "<b>Complaint Category:</b> Physical Defect",
            "",
            "<b>Detailed complaint description:</b>",
            "A regular customer returned two blister strips of Metformin 500 mg tablets purchased on "
            "18 July 2026. Multiple tablets in the strips were found broken into halves and small "
            "fragments. The blister cavities and foil appeared intact on inspection - no sign of transit "
            "damage or tampering. The patient is a diabetic on daily therapy and expressed concern about "
            "receiving an incorrect dose. No adverse event was reported by the patient. The affected "
            "strips have been retained at our pharmacy for QA inspection.",
        ],
    },
    {
        "filename": "complaint_03_efficacy.pdf",
        "title": "Customer Complaint - Loss of Efficacy Report",
        "body": [
            "<b>To:</b> Pharmacovigilance / Quality Complaints",
            "<b>From:</b> Dr. Amit Verma, Cardiology Consultant, Fortis Hospital, Gurgaon",
            "<b>Contact:</b> amit.verma.md@fortishealthcare.in",
            "<b>Complaint Source:</b> Phone (followed by email)",
            "<b>Complaint Date:</b> 18 July 2026",
            "",
            "<b>Product:</b> Atorvastatin Tablets",
            "<b>Product Strength / Grade:</b> 20 mg",
            "<b>Batch / LOT Number:</b> ATV20-24C1122",
            "",
            "<b>Complaint Type:</b> Efficacy",
            "<b>Complaint Category:</b> Suspected Sub-potency",
            "",
            "<b>Detailed complaint description:</b>",
            "I have five patients on long-term statin therapy who were switched from an older batch to "
            "batch ATV20-24C1122 approximately 6 weeks ago. All five had well-controlled LDL cholesterol "
            "levels prior to the switch. At their latest follow-up, four out of five show a rise in LDL "
            "of 20-35 percent despite reported full compliance. Diet, weight and concomitant medication "
            "are unchanged. No patients report gastrointestinal or muscular adverse effects. This raises "
            "concern about a possible sub-potency issue with this specific batch. Requesting the "
            "manufacturer to perform assay verification on retention samples and confirm the results.",
        ],
    },
    {
        "filename": "complaint_04_labeling.pdf",
        "title": "Customer Complaint - Wrong Strength on Carton",
        "body": [
            "<b>To:</b> Quality Assurance",
            "<b>From:</b> MediPlus Distributors, Hyderabad",
            "<b>Contact:</b> operations@mediplus.co.in",
            "<b>Complaint Source:</b> Distributor Report",
            "<b>Complaint Date:</b> 26 July 2026",
            "",
            "<b>Product:</b> Amoxicillin + Clavulanic Acid Oral Suspension",
            "<b>Product Strength / Grade:</b> Mismatch - see description",
            "<b>Batch / LOT Number:</b> AMC-25E0918",
            "<b>Quantity affected:</b> 1 shipping carton (approximately 50 bottles)",
            "",
            "<b>Complaint Type:</b> Labeling",
            "<b>Complaint Category:</b> Wrong Strength Label",
            "",
            "<b>Detailed complaint description:</b>",
            "During routine stock check at our warehouse we discovered that the outer shipping carton "
            "of one unit is labelled 228.5 mg/5 mL (Amoxicillin 200 mg + Clavulanic Acid 28.5 mg), "
            "while the individual bottle labels inside are printed as 457 mg/5 mL (Amoxicillin 400 mg + "
            "Clavulanic Acid 57 mg). Both strengths are marketed by your company. This carton/primary-pack "
            "mismatch could lead to serious dosing errors in paediatric patients if dispensed. All 50 "
            "bottles have been quarantined pending your investigation. Immediate response requested "
            "given the paediatric safety implications.",
        ],
    },
    {
        "filename": "complaint_05_packaging_minor.pdf",
        "title": "Customer Complaint - Faded Print on Carton",
        "body": [
            "<b>To:</b> Customer Care",
            "<b>From:</b> Ms. Ananya Rao, Retail customer, Bengaluru",
            "<b>Contact:</b> ananya.rao.blr@gmail.com",
            "<b>Complaint Source:</b> Portal",
            "<b>Complaint Date:</b> 20 July 2026",
            "",
            "<b>Product:</b> Paracetamol Tablets",
            "<b>Product Strength / Grade:</b> 650 mg",
            "<b>Batch / LOT Number:</b> PAR65-25B0810",
            "",
            "<b>Complaint Type:</b> Packaging",
            "<b>Complaint Category:</b> Print Quality",
            "",
            "<b>Detailed complaint description:</b>",
            "I bought a strip of paracetamol yesterday and noticed the printed batch number and expiry "
            "date on the outer carton are quite faded - I had to hold it under bright light to read it. "
            "The blister foil itself is fine and clearly printed. The tablets look normal. Not sure if "
            "this is a big issue but wanted to raise it. No health impact.",
        ],
    },
]


def make_pdf(filename: str, title: str, body_lines: list[str]) -> Path:
    path = OUT_DIR / filename
    doc = SimpleDocTemplate(str(path), pagesize=LETTER, title=title)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"<b>{title}</b>", styles["Title"]), Spacer(1, 12)]
    for line in body_lines:
        if line.strip() == "":
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(line, styles["BodyText"]))
    doc.build(story)
    return path


def make_email(filename: str, subject: str, body_lines: list[str]) -> Path:
    path = OUT_DIR / filename
    now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    plain = "\n".join(l.replace("<b>", "").replace("</b>", "") for l in body_lines)
    eml = (
        f"From: quality@abcformulations.co.in\n"
        f"To: qa@zenithlifesciences.example\n"
        f"Subject: {subject}\n"
        f"Date: {now}\n"
        f"Content-Type: text/plain; charset=utf-8\n"
        f"\n"
        f"{plain}\n"
    )
    path.write_text(eml, encoding="utf-8")
    return path


if __name__ == "__main__":
    made = [make_pdf(c["filename"], c["title"], c["body"]) for c in COMPLAINTS]
    first = COMPLAINTS[0]
    made.append(make_email("Fictional_Pharma_Customer_Complaint_01.eml", first["title"], first["body"]))
    print("Wrote:")
    for p in made:
        print(" -", p)
