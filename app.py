import streamlit as st
import pandas as pd
from io import BytesIO

def parse_transactions():
    # Data transaksi rekening Mandiri (hardcoded sebagai contoh)
    data = [
        ["04/01/2025", "MCM InhouseTrf KE F AGUNG KRISTIANTO Transfer Fee 20250104085954275399102", 7000000.00, 0.00, 183975.35],
        ["04/01/2025", "20250104BNINIDJA010O0139235111 BNINIDJA/INCA NUSA AQUACULTURE 688131313299102", 0.00, 77215600.00, 77399575.35],
        ["04/01/2025", "MCM InhouseTrf KE F AGUNG KRISTIANTO Transfer Fee 20250104134771648099102", 25000000.00, 0.00, 52399575.35],
        # Tambahkan baris lainnya sesuai kebutuhan...
    ]
    df = pd.DataFrame(data, columns=["Tanggal", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], format="%d/%m/%Y")
    return df

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaksi')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.title("Konversi Rekening Mandiri ke Excel")

    st.write("Aplikasi ini mengonversi data rekening Mandiri menjadi file Excel.")

    df = parse_transactions()
    st.dataframe(df)

    excel_data = convert_df_to_excel(df)

    st.download_button(
        label="Unduh Excel",
        data=excel_data,
        file_name="Rekening_Mandiri.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    main()
