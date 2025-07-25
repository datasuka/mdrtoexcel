import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Ekstraksi PDF Rekening Mandiri ke Excel", layout="wide")

def extract_transactions_from_pdf(file):
    results = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')

            for i, line in enumerate(lines):
                # Cari pola tanggal dan waktu transaksi
                match = re.match(r"(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})", line)
                if match:
                    tanggal = match.group(1)
                    waktu = match.group(2)

                    deskripsi_lines = []
                    angka_line = None

                    # Kumpulkan deskripsi dan nilai
                    for j in range(i + 1, min(i + 6, len(lines))):
                        if re.search(r"-?\d{1,3}(\.\d{3})*,\d{2}", lines[j]):
                            angka_line = lines[j]
                            break
                        deskripsi_lines.append(lines[j])

                    if angka_line:
                        # Parsing angka
                        angka_str = angka_line.replace('.', '').replace(',', '.')
                        angka_values = [float(s) for s in angka_str.split() if re.match(r"-?\d+(\.\d+)?", s)]

                        if len(angka_values) >= 1:
                            saldo = angka_values[-1]
                            kredit = angka_values[-2] if len(angka_values) >= 2 else 0.0
                            debit = angka_values[-3] if len(angka_values) >= 3 else 0.0

                            deskripsi = ' '.join(deskripsi_lines).strip()
                            results.append([tanggal, waktu, deskripsi, debit, kredit, saldo])

    df = pd.DataFrame(results, columns=["Waktu Transaksi", "Jam", "Deskripsi", "Debit", "Kredit", "Saldo"])

    # Gabungkan tanggal dan waktu jadi 1 kolom datetime
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"] + ' ' + df["Jam"], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    df.drop(columns=["Jam"], inplace=True)
    return df.dropna()

def convert_df_to_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaksi')
    return buffer.getvalue()

# -----------------------------------
# UI Streamlit
# -----------------------------------
st.title("📄 Ekstraksi PDF Rekening Mandiri ke Excel")
st.markdown("Unggah file rekening Mandiri dalam format PDF untuk dikonversi menjadi file Excel.")

uploaded_file = st.file_uploader("📎 Unggah file PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("🔍 Memproses file..."):
        df = extract_transactions_from_pdf(uploaded_file)

        if not df.empty:
            st.success(f"✅ Berhasil mengekstrak {len(df)} transaksi.")
            st.dataframe(df, use_container_width=True)

            excel_data = convert_df_to_excel(df)
            st.download_button(
                label="📥 Unduh Excel",
                data=excel_data,
                file_name="rekening_mandiri.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("⚠️ Tidak ada transaksi berhasil diekstrak.")
