
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Mandiri RK to Excel (Keterangan + Regex)", layout="wide")
st.title("📄 Konversi Rekening Koran Mandiri ke Excel (Lengkap)")

def extract_data(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        full_text = "\n".join([page.extract_text() for page in pdf.pages])

    # Header extraction
    nomor_rek = re.findall(r"Account No\.\n?(\d+)", full_text)
    currency = re.findall(r"Currency\n?(\w+)", full_text)
    opening_balance = re.findall(r"Opening Balance\n?([\d.,]+)", full_text)

    header_blocks = re.split(r"(?=\d{2}/\d{2}/\d{4})", full_text)
    results = []

    current_norek = nomor_rek[0] if nomor_rek else ""
    curr = currency[0] if currency else ""
    saldo_awal = opening_balance[0].replace(",", "") if opening_balance else ""

    for block in header_blocks:
        tanggal_match = re.match(r"(\d{2}/\d{2}/\d{4})", block)
        if not tanggal_match:
            continue
        tanggal = "/".join(reversed(tanggal_match.group(1).split("/")))

        angka_match = re.findall(r"([-]?[\d.,]+)\s+([-]?[\d.,]+)\s+([-]?[\d.,]+)", block)
        if not angka_match:
            continue
        debit, kredit, saldo = angka_match[-1]
        debit = debit.replace(",", ".")
        kredit = kredit.replace(",", ".")
        saldo = saldo.replace(",", ".")

        # Ambil semua baris di antara tanggal dan baris angka sebagai keterangan
        baris = block.strip().split("\n")[1:]
        ket_bersih = []
        for b in baris:
            if len(re.findall(r"[-]?[\d.,]+", b)) >= 3:
                break
            ket_bersih.append(b.strip())
        keterangan = " ".join(ket_bersih)

        results.append([
            current_norek, tanggal, keterangan.strip(),
            debit, kredit, saldo, curr, saldo_awal
        ])

    df = pd.DataFrame(results, columns=[
        "Nomor Rekening", "Tanggal (dd/mm/yyyy)", "Keterangan",
        "Debit", "Kredit", "Saldo", "currency", "Saldo awal"
    ])

    # Format angka pakai koma
    for col in ["Debit", "Kredit", "Saldo", "Saldo awal"]:
        df[col] = df[col].str.replace(".", ",", regex=False)

    return df

uploaded_file = st.file_uploader("Unggah File PDF Rekening Koran Mandiri", type="pdf")

if uploaded_file:
    try:
        df = extract_data(uploaded_file)
        if df.empty:
            st.warning("❗ Tidak ada transaksi terbaca.")
        else:
            st.success("✅ Data berhasil diekstrak:")
            st.dataframe(df, use_container_width=True)

            output = BytesIO()
            df.to_excel(output, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), file_name="Mandiri_RekeningKoran_Lengkap.xlsx")
    except Exception as e:
        st.error(f"❌ Gagal parsing: {e}")
