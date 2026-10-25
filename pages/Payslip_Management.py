import io
import json
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

from src.employee_manager import load_employees

st.set_page_config(
    page_title="Payslip Management | HCM Lite",
    page_icon="🧾",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PAYSLIPS_FILE = DATA_DIR / "payslips.json"


def load_payslips():
    try:
        with open(PAYSLIPS_FILE, "r", encoding="utf-8") as file:
            records = json.load(file)
        return records if isinstance(records, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def save_payslips(records):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = PAYSLIPS_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    temp_file.replace(PAYSLIPS_FILE)


def money(value):
    return f"PKR {value:,.2f}"


def create_pdf(record):
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Brand",
        parent=styles["Title"],
        fontSize=22,
        leading=27,
        textColor=colors.HexColor("#0F766E"),
        alignment=TA_CENTER,
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="SubBrand",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER,
        spaceAfter=18,
    ))

    story = [
        Paragraph("HCM LITE", styles["Brand"]),
        Paragraph("EMPLOYEE PAYSLIP", styles["SubBrand"]),
    ]

    details = [
        ["Payslip ID", record["payslip_id"],
         "Salary Month", record["salary_month"]],
        ["Employee", record["employee_name"],
         "Employee ID", str(record["employee_id"])],
        ["Department", record["department"],
         "Job Title", record["job_title"]],
        ["Email", record["email"],
         "Generated On", record["generated_on"]],
    ]

    details_table = Table(details, colWidths=[27*mm, 52*mm, 27*mm, 45*mm])
    details_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#334155")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#334155")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))

    story += [details_table, Spacer(1, 18)]

    salary_rows = [
        ["EARNINGS", "AMOUNT"],
        ["Basic Salary", money(record["basic_salary"])],
        ["Allowances", money(record["allowances"])],
        ["Bonus", money(record["bonus"])],
        ["Gross Salary", money(record["gross_salary"])],
        ["Deductions", f"- {money(record['deductions'])}"],
        ["NET SALARY", money(record["net_salary"])],
    ]

    salary_table = Table(salary_rows, colWidths=[105*mm, 45*mm])
    salary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#F1F5F9")),
        ("FONTNAME", (0, 6), (-1, 6), "Helvetica-Bold"),
        ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#CCFBF1")),
        ("TEXTCOLOR", (0, 6), (-1, 6), colors.HexColor("#115E59")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    story += [
        salary_table,
        Spacer(1, 22),
        Paragraph(
            "This payslip was generated electronically by HCM Lite. "
            "Please contact HR if any information needs correction.",
            styles["Normal"],
        ),
        Spacer(1, 8),
        Paragraph(
            "Currency: PKR (Pakistani Rupees)",
            styles["SubBrand"],
        ),
    ]

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# Access control
user = st.session_state.get("user")
if not isinstance(user, dict) or str(user.get("role", "")).lower() != "admin":
    st.error("Payslip Management sirf Admin access kar sakta hai.")
    st.stop()


# Page styling
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2.5rem;}
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #102A43, #164E63);
    border: 1px solid #285E70;
    padding: 16px;
    border-radius: 12px;
}
[data-testid="stMetricLabel"] {color: #D9F3F0;}
[data-testid="stMetricValue"] {color: #FFFFFF;}
</style>
""", unsafe_allow_html=True)

st.title("🧾 Payslip Management")
st.caption("Payroll workspace • Salary calculation • PDF generation • Payslip history")

employees = [
    employee for employee in load_employees()
    if str(employee.get("status", "Active")).strip().lower() == "active"
]

payslips = load_payslips()

m1, m2, m3 = st.columns(3)
m1.metric("Active Employees", len(employees))
m2.metric("Generated Payslips", len(payslips))
m3.metric(
    "Current Month",
    date.today().strftime("%B %Y"),
)

st.divider()

if not employees:
    st.warning(
        "Abhi koi active employee nahi hai. Pehle Employee Management page "
        "se employee add ya approve karo."
    )
    st.stop()

st.subheader("Create a Payslip")

employee_options = {
    f"#{employee.get('id')} — {employee.get('name', 'Unknown')} "
    f"({employee.get('department', 'No department')})": employee
    for employee in employees
}

with st.form("payslip_form"):
    selected_label = st.selectbox(
        "Select Employee",
        list(employee_options.keys()),
    )
    selected_employee = employee_options[selected_label]

    c1, c2 = st.columns(2)
    with c1:
        salary_month = st.text_input(
            "Salary Month (e.g. October 2026)",
            value=date.today().strftime("%B %Y"),
        )
        basic_salary = st.number_input(
            "Basic Monthly Salary (PKR)",
            min_value=0.0,
            value=float(selected_employee.get("monthly_salary") or 0),
            step=1000.0,
        )
        allowances = st.number_input(
            "Allowances (PKR)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )
    with c2:
        bonus = st.number_input(
            "Bonus (PKR)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )
        deductions = st.number_input(
            "Deductions (PKR)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )
        notes = st.text_input("Notes (optional)")

    gross_salary = basic_salary + allowances + bonus
    net_salary = gross_salary - deductions

    st.markdown("#### Salary Preview")
    p1, p2, p3 = st.columns(3)
    p1.metric("Gross Salary", money(gross_salary))
    p2.metric("Total Deductions", money(deductions))
    p3.metric("Net Salary", money(net_salary))

    submitted = st.form_submit_button(
        "Generate Payslip",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not salary_month.strip():
        st.error("Salary month required hai.")
    elif basic_salary <= 0:
        st.error("Basic salary zero se zyada honi chahiye.")
    elif deductions > gross_salary:
        st.error("Deductions gross salary se zyada nahi ho sakti.")
    else:
        employee = employee_options[selected_label]

        employee_id = employee.get("id")
        already_exists = any(
            str(record.get("employee_id")) == str(employee_id)
            and record.get("salary_month", "").strip().casefold()
            == salary_month.strip().casefold()
            for record in payslips
        )

        if already_exists:
            st.error(
                "Is employee ki is month ki payslip pehle se hai. "
                "Duplicate payslip create nahi ki gayi."
            )
        else:
            record = {
                "payslip_id": f"PS-{date.today():%Y%m%d}-{len(payslips) + 1:04d}",
                "employee_id": employee_id,
                "employee_name": employee.get("name", ""),
                "email": employee.get("email", ""),
                "department": employee.get("department", ""),
                "job_title": employee.get("job_title", ""),
                "salary_month": salary_month.strip(),
                "basic_salary": round(basic_salary, 2),
                "allowances": round(allowances, 2),
                "bonus": round(bonus, 2),
                "gross_salary": round(gross_salary, 2),
                "deductions": round(deductions, 2),
                "net_salary": round(net_salary, 2),
                "notes": notes.strip(),
                "generated_on": date.today().isoformat(),
                "generated_by": user.get("email", user.get("name", "Admin")),
            }

            payslips.append(record)

            try:
                save_payslips(payslips)
                st.session_state["latest_payslip_id"] = record["payslip_id"]
                st.success("Payslip successfully generate aur save ho gayi.")
                st.rerun()
            except OSError:
                st.error("Payslip save nahi ho saki. Storage permissions check karo.")


# Latest payslip download
st.divider()
st.subheader("Download Payslip")

latest_id = st.session_state.get("latest_payslip_id")
latest_record = next(
    (record for record in load_payslips()
     if record.get("payslip_id") == latest_id),
    None,
)

if latest_record:
    try:
        pdf_bytes = create_pdf(latest_record)
        st.download_button(
            "⬇️ Download PDF Payslip",
            data=pdf_bytes,
            file_name=f"{latest_record['payslip_id']}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"PDF generate nahi ho saki: {type(exc).__name__}")
else:
    st.info("Pehle ek payslip generate karo, phir yahan PDF download kar sakte ho.")


# History
st.divider()
st.subheader("Payslip History")

all_records = load_payslips()

if all_records:
    history = pd.DataFrame([
        {
            "Payslip ID": record.get("payslip_id", ""),
            "Employee": record.get("employee_name", ""),
            "Employee ID": record.get("employee_id", ""),
            "Department": record.get("department", ""),
            "Salary Month": record.get("salary_month", ""),
            "Gross Salary (PKR)": record.get("gross_salary", 0),
            "Deductions (PKR)": record.get("deductions", 0),
            "Net Salary (PKR)": record.get("net_salary", 0),
            "Generated On": record.get("generated_on", ""),
        }
        for record in all_records
    ])

    search = st.text_input(
        "Search history",
        placeholder="Employee name, payslip ID, department or month...",
    )

    if search.strip():
        mask = history.astype(str).apply(
            lambda column: column.str.contains(
                search.strip(), case=False, regex=False, na=False
            )
        ).any(axis=1)
        history = history[mask]

    st.dataframe(
        history.sort_values("Generated On", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    selected_id = st.selectbox(
        "Choose a saved payslip to download",
        [record["payslip_id"] for record in all_records],
        key="history_payslip_select",
    )

    selected_record = next(
        record for record in all_records
        if record["payslip_id"] == selected_id
    )

    st.download_button(
        "Download Selected Payslip PDF",
        data=create_pdf(selected_record),
        file_name=f"{selected_id}.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="history_pdf_download",
    )
else:
    st.info("Abhi koi payslip history available nahi hai.")

st.caption(
    "HCM Lite Payroll • Amounts are entered/approved by Admin. "
    "Review deductions and payroll policy before issuing official payslips."
)
