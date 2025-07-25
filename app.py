import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def extract_mandiri_transactions(file):
    results = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')

            current_transaction = []
            for line in lines:
                if re.match(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', line):
                    if current_transaction:
                        results.append(current_transaction)
                    current_transaction = [line]
                else:
                    current_transaction.append(line)
            if current_transaction:
                results.append(current_transaction)

    data = []
    for trx in results:
        try:
            tanggal_waktu = trx[0].strip()
            tanggal, waktu = tanggal_waktu.split(' ')
            deskripsi_lines = trx[1:-1]
            deskripsi = ' '.join([line.strip() for line in deskripsi_lines if line.strip()])
            angka_line = trx[-1]

            angka = [a.replace('.', '').replace(',', '.') for a in angka_line.split() if re.search(r'\d', a)]
            angka_float = [float(a) for a in angka[-3:]]  # Ambil 3 angka terakhir

            if len(angka_float) == 3:
                debit, kredit, saldo = angka_float
                data.append([tanggal, waktu, deskripsi, debit, kredit, saldo])
        except Exception as e:
            continue  # Lewati jika format tidak cocok

    df = pd.DataFrame(data, columns=['Tanggal', 'Waktu', 'Deskripsi', 'Debit', 'Kredit', 'Saldo'])
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], format='%d/%m/%Y', errors='coerce')
    return df

def convert_df_to_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Rekening Mandiri')
    return buffer.getvalue()

def main():
    st.title("Ekstraksi Rekening Mandiri ke Excel")
    uploaded = st.file_uploader("Unggah PDF Rekening Mandiri", type="pdf")
    if uploaded:
        df = extract_mandiri_transactions(uploaded)
        st.success(f"Berhasil mengekstrak {len(df)} transaksi.")
        st.dataframe(df)

        excel_data = convert_df_to_excel(df)
        st.download_button("Unduh Excel", data=excel_data, file_name="Rekening_Mandiri.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == '__main__':
    main()
