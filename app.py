
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Mandiri RK to Excel", layout="wide")
st.title("📄 Konversi Rekening Koran Mandiri ke Excel")

def extract_data(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    rekening = re.search(r"Account No\.\s+(\d+)", full_text)
    currency = re.search(r"Currency\s+(\w+)", full_text)
    opening_balance = re.search(r"Opening Balance\n([\d.,]+)", full_text)

    records = []
    lines = full_text.split("\n")
    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}")

    i = 0
    while i < len(lines):
        if date_pattern.match(lines[i]):
            tanggal = lines[i][:10]
            tanggal_fmt = "/".join(reversed(tanggal.split("/")))
            keterangan_lines = []
            i += 1
            while i < len(lines) and not date_pattern.match(lines[i]):
                if re.search(r"\d{2}/\d{2}/\d{4}", lines[i]):
                    break
                keterangan_lines.append(lines[i])
                i += 1
            ketgabung = " ".join(keterangan_lines).strip()

            debit, kredit, saldo = "", "", ""
            angka = re.findall(r"[-]?[\d,.]+", lines[i - 1])
            if len(angka) == 3:
                debit, kredit, saldo = angka
            records.append([tanggal_fmt, ketgabung, debit, kredit, saldo])
        else:
            i += 1

    df = pd.DataFrame(records, columns=["Tanggal (dd/mm/yyyy)", "Keterangan", "Debit", "Kredit", "Saldo"])
    df.insert(0, "Nomor Rekening", rekening.group(1) if rekening else "")
    df["currency"] = currency.group(1) if currency else ""
    df["Saldo awal"] = opening_balance.group(1).replace(",", "") if opening_balance else ""
    return df

uploaded_file = st.file_uploader("Unggah File PDF Rekening Koran Mandiri", type="pdf")

if uploaded_file:
    try:
        df = extract_data(uploaded_file)
        st.success("Berhasil mengekstrak data. Berikut hasilnya:")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("📥 Download Excel", output.getvalue(), file_name="Mandiri_RekeningKoran.xlsx")
    except Exception as e:
        st.error(f"Gagal mengekstrak data: {e}")
