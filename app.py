
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Mandiri RK to Excel (Bersih)", layout="wide")
st.title("📄 Konversi Rekening Koran Mandiri ke Excel (Final, Bersih)")

def extract_data(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        full_text = "\n".join([page.extract_text() for page in pdf.pages])

    # Header info
    rekening_list = re.findall(r"Account No\.\n?(\d+)", full_text)
    currency_list = re.findall(r"Currency\n?(\w+)", full_text)
    opening_list = re.findall(r"Opening Balance\n?([\d.,]+)", full_text)

    current_norek = rekening_list[0] if rekening_list else ""
    curr = currency_list[0] if currency_list else ""
    saldo_awal = opening_list[0].replace(",", ".") if opening_list else ""

    # Blok transaksi
    blocks = re.split(r"(?=\d{2}/\d{2}/\d{4})", full_text)
    rows = []

    for block in blocks:
        tanggal_match = re.match(r"(\d{2}/\d{2}/\d{4})", block)
        if not tanggal_match:
            continue
        tanggal = "/".join(reversed(tanggal_match.group(1).split("/")))

        angka_match = re.findall(r"([-]?[\d.,]+)\s+([-]?[\d.,]+)\s+([-]?[\d.,]+)", block)
        if not angka_match:
            continue
        debit, kredit, saldo = angka_match[-1]

        # Format angka: hilangkan pemisah ribuan, ubah titik jadi koma untuk desimal
        def clean_number(n):
            return n.replace(",", "").replace(".", ",") if "." in n else n.replace(",", "")

        debit = clean_number(debit)
        kredit = clean_number(kredit)
        saldo = clean_number(saldo)
        saldo_awal_clean = clean_number(saldo_awal)

        # Keterangan: semua baris sebelum angka 3 kolom terakhir
        baris = block.strip().split("\n")[1:]
        keterangan = []
        for b in baris:
            if len(re.findall(r"[-]?[\d.,]+", b)) >= 3:
                break
            keterangan.append(b.strip())
        ket_full = " ".join(keterangan)

        rows.append([
            current_norek, tanggal, ket_full, debit, kredit, saldo, curr, saldo_awal_clean
        ])

    df = pd.DataFrame(rows, columns=[
        "Nomor Rekening", "Tanggal (dd/mm/yyyy)", "Keterangan",
        "Debit", "Kredit", "Saldo", "currency", "Saldo awal"
    ])
    return df

uploaded_file = st.file_uploader("Unggah File PDF Rekening Koran Mandiri", type="pdf")

if uploaded_file:
    try:
        df = extract_data(uploaded_file)
        if df.empty:
            st.warning("❗ Tidak ada data transaksi yang terbaca.")
        else:
            st.success("✅ Data berhasil diekstrak:")
            st.dataframe(df, use_container_width=True)

            output = BytesIO()
            df.to_excel(output, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), file_name="Mandiri_RekeningKoran_Bersih.xlsx")
    except Exception as e:
        st.error(f"❌ Gagal parsing: {e}")
