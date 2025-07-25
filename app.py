import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def parse_amount(text):
    """Ubah format angka lokal ke float"""
    text = text.replace('.', '').replace(',', '.')
    try:
        return float(text)
    except:
        return 0.0

def extract_transactions(file):
    rows = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            st.text_area("DEBUG - Halaman PDF", text[:3000], height=300)

            i = 0
            while i < len(lines):
                line = lines[i]

                # Cari baris yang mengandung tanggal dan jumlah angka
                if re.search(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', line) and re.search(r'\d+,\d{2}', line):
                    tanggal_waktu_match = re.search(r'(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})', line)
                    if tanggal_waktu_match:
                        tanggal = tanggal_waktu_match.group(1)
                        waktu = tanggal_waktu_match.group(2)

                        # Coba ambil 2 baris sebelumnya sebagai deskripsi
                        deskripsi = lines[i-1].strip() if i > 0 else ''
                        if i > 1 and not re.search(r'\d', lines[i-2]):
                            deskripsi = lines[i-2].strip() + ' ' + deskripsi

                        # Ambil angka dari baris ini
                        angka_parts = line.replace('-', ' -').split()
                        angka_floats = [parse_amount(p) for p in angka_parts if re.search(r'\d', p)]
                        if len(angka_floats) >= 3:
                            debit, kredit, saldo = angka_floats[-3:]
                            rows.append([tanggal, waktu, deskripsi, debit, kredit, saldo])
                i += 1

    df = pd.DataFrame(rows, columns=["Tanggal", "Waktu", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], format="%d/%m/%Y", errors="coerce")
    return df.dropna(subset=["Tanggal"])

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    return output.getvalue()

def main():
    st.set_page_config(page_title="Ekstraksi Rekening Mandiri", layout="centered")
    st.title("Ekstraksi PDF Rekening Mandiri ke Excel")

    uploaded = st.file_uploader("Unggah file PDF", type="pdf")

    if uploaded:
        df = extract_transactions(uploaded)
        if df.empty:
            st.warning("Tidak ada transaksi berhasil diekstrak.")
        else:
            st.success(f"{len(df)} transaksi berhasil diekstrak.")
            st.dataframe(df)

            excel = convert_df_to_excel(df)
            st.download_button("Unduh Excel", data=excel, file_name="Rekening_Mandiri.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
