
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Mandiri RK to Excel", layout="wide")
st.title("📄 Konversi Rekening Koran Mandiri ke Excel")

def extract_data(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        all_text = [page.extract_text() for page in pdf.pages]
        full_text = "\n".join(all_text)

    # Ambil info header
    rekening = re.search(r"Account No\.\n?(\d+)", full_text)
    currency = re.search(r"Currency\n?(\w+)", full_text)
    opening_balance = re.search(r"Opening Balance\n?([\d.,]+)", full_text)

    nomor_rekening = rekening.group(1) if rekening else ""
    curr = currency.group(1) if currency else ""
    saldo_awal = opening_balance.group(1).replace(",", "") if opening_balance else ""

    # Mulai parsing transaksi
    lines = full_text.split("\n")
    tanggal_regex = re.compile(r"^\d{2}/\d{2}/\d{4}")

    data_rows = []
    i = 0
    while i < len(lines):
        if tanggal_regex.match(lines[i]):
            tanggal = lines[i].strip()[:10]
            tanggal_fmt = "/".join(reversed(tanggal.split("/")))

            i += 1
            keterangan = []
            angka_found = False
            debit = kredit = saldo = ""

            while i < len(lines) and not tanggal_regex.match(lines[i]):
                nums = re.findall(r"[-]?[\d.,]+", lines[i])
                if len(nums) == 3 and not angka_found:
                    debit, kredit, saldo = [n.replace(",", "") for n in nums]
                    angka_found = True
                else:
                    keterangan.append(lines[i].strip())
                i += 1

            if angka_found:
                data_rows.append([
                    nomor_rekening, tanggal_fmt, " ".join(keterangan),
                    debit, kredit, saldo, curr, saldo_awal
                ])
        else:
            i += 1

    df = pd.DataFrame(data_rows, columns=[
        "Nomor Rekening", "Tanggal (dd/mm/yyyy)", "Keterangan",
        "Debit", "Kredit", "Saldo", "currency", "Saldo awal"
    ])
    return df

uploaded_file = st.file_uploader("Unggah File PDF Rekening Koran Mandiri", type="pdf")

if uploaded_file:
    try:
        df = extract_data(uploaded_file)
        if df.empty:
            st.warning("Data tidak ditemukan atau format tidak cocok.")
        else:
            st.success("✅ Data berhasil diekstrak:")
            st.dataframe(df, use_container_width=True)

            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            st.download_button("📥 Download Excel", buffer.getvalue(), file_name="Mandiri_RekeningKoran.xlsx")
    except Exception as e:
        st.error(f"Gagal mengekstrak data: {e}")
