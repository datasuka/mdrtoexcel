import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re


def parse_amount(text):
    try:
        return float(text.replace('.', '').replace(',', '.'))
    except:
        return 0.0


def extract_transactions(file):
    rows = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            st.text_area("DEBUG - Isi PDF", text[:3000], height=250)

            lines = text.split('\n')

            for i, line in enumerate(lines):
                # Deteksi baris transaksi lengkap
                match = re.search(
                    r'(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2}) (.+?) (-?\d[\d.,]*) (-?\d[\d.,]*) (-?\d[\d.,]*)$',
                    line
                )
                if match:
                    tanggal = match.group(1)
                    waktu = match.group(2)
                    deskripsi_dari_baris_ini = match.group(3).strip()

                    # Tambahkan baris sebelumnya ke deskripsi jika bukan angka
                    deskripsi_tambahan = lines[i - 1].strip() if i > 0 and not re.search(r'\d{2}/\d{2}/\d{4}', lines[i - 1]) else ''
                    deskripsi = (deskripsi_tambahan + ' ' + deskripsi_dari_baris_ini).strip()

                    debit = parse_amount(match.group(4))
                    kredit = parse_amount(match.group(5))
                    saldo = parse_amount(match.group(6))

                    rows.append([tanggal + ' ' + waktu, deskripsi, debit, kredit, saldo])

    df = pd.DataFrame(rows, columns=["Waktu Transaksi", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna(subset=["Waktu Transaksi"])


def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    return output.getvalue()


def main():
    st.set_page_config(page_title="Ekstraksi Rekening Mandiri", layout="centered")
    st.title("📄 Ekstraksi PDF Rekening Mandiri ke Excel")

    uploaded = st.file_uploader("Unggah file PDF", type="pdf")

    if uploaded:
        df = extract_transactions(uploaded)

        if df.empty:
            st.warning("⚠️ Tidak ada transaksi berhasil diekstrak.")
        else:
            st.success(f"✅ {len(df)} transaksi berhasil diekstrak.")
            st.dataframe(df)

            excel_data = convert_df_to_excel(df)
            st.download_button(
                label="📥 Unduh Excel",
                data=excel_data,
                file_name="Rekening_Mandiri.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


if __name__ == "__main__":
    main()
