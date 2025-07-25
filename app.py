import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def parse_amount(val):
    try:
        return float(val.replace('.', '').replace(',', '.').replace('−', '-'))
    except:
        return 0.0

def extract_transactions(file):
    results = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                if re.match(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', line):
                    waktu = line
                    deskripsi = []
                    angka_line = None

                    # Ambil 3 baris deskripsi berikutnya
                    for j in range(1, 6):
                        if i + j < len(lines):
                            next_line = lines[i + j].strip()
                            # Deteksi baris angka
                            if len(re.findall(r'-?[\d.,]+', next_line)) >= 3:
                                angka_line = next_line
                                i += j  # lompat ke angka_line
                                break
                            else:
                                deskripsi.append(next_line)

                    if angka_line:
                        angka = re.findall(r'-?[\d.,]+', angka_line)
                        if len(angka) >= 3:
                            debit = parse_amount(angka[-3])
                            kredit = parse_amount(angka[-2])
                            saldo = parse_amount(angka[-1])

                            deskripsi_joined = ' '.join(deskripsi).strip()
                            results.append([waktu, deskripsi_joined, debit, kredit, saldo])
                i += 1

    df = pd.DataFrame(results, columns=["Waktu Transaksi", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna()

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    return output.getvalue()

def main():
    st.set_page_config(page_title="Ekstraksi PDF Rekening Mandiri", layout="centered")
    st.title("📄 Ekstraksi PDF Rekening Mandiri ke Excel")

    uploaded = st.file_uploader("Unggah file PDF", type=["pdf"])

    if uploaded:
        df = extract_transactions(uploaded)

        if df.empty:
            st.warning("⚠️ Tidak ada transaksi berhasil diekstrak.")
        else:
            st.success(f"✅ {len(df)} transaksi berhasil diekstrak.")
            st.dataframe(df)

            excel_file = convert_df_to_excel(df)
            st.download_button(
                label="📥 Unduh Excel",
                data=excel_file,
                file_name="Rekening_Mandiri.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
