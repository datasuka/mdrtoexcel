
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Mandiri RK to Excel", layout="wide")
st.title("📄 Konversi Rekening Koran Mandiri ke Excel (Regex Version)")

def extract_data(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        full_text = "\n".join([page.extract_text() for page in pdf.pages])

    # Header extraction
    nomor_rek = re.search(r"Account No\.\n?(\d+)", full_text)
    mata_uang = re.search(r"Currency\n?(\w+)", full_text)
    saldo_awal = re.search(r"Opening Balance\n?([\d.,]+)", full_text)

    norek = nomor_rek.group(1) if nomor_rek else ""
    curr = mata_uang.group(1) if mata_uang else ""
    opening = saldo_awal.group(1).replace(",", "") if saldo_awal else ""

    # Ambil blok transaksi
    regex_blok = re.findall(
        r"(\d{2}/\d{2}/\d{4}).+?(?:(?:\n|\r).+?)*?(-?[\d.,]+)\s+(-?[\d.,]+)\s+(-?[\d.,]+)",
        full_text, re.DOTALL
    )

    hasil = []
    for tanggal, debit, kredit, saldo in regex_blok:
        tanggal_fmt = "/".join(reversed(tanggal.split("/")))
        hasil.append([
            norek, tanggal_fmt, "",  # keterangan dikosongkan karena regex blok
            debit.replace(",", ""), kredit.replace(",", ""),
            saldo.replace(",", ""), curr, opening
        ])

    df = pd.DataFrame(hasil, columns=[
        "Nomor Rekening", "Tanggal (dd/mm/yyyy)", "Keterangan",
        "Debit", "Kredit", "Saldo", "currency", "Saldo awal"
    ])
    return df

uploaded_file = st.file_uploader("Upload PDF Rekening Koran Mandiri", type="pdf")

if uploaded_file:
    try:
        df = extract_data(uploaded_file)
        if df.empty:
            st.warning("❗ Tidak ada data transaksi yang terdeteksi.")
        else:
            st.success("✅ Data berhasil diekstrak:")
            st.dataframe(df, use_container_width=True)

            output = BytesIO()
            df.to_excel(output, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), file_name="Mandiri_RekeningKoran_Regex.xlsx")
    except Exception as e:
        st.error(f"❌ Gagal parsing: {e}")
