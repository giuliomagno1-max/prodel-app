import streamlit as st
from fpdf import FPDF
import pandas as pd
import requests
import os
from datetime import datetime

# --- CONFIGURAZIONE ---
NOME_AZIENDA = "PRODEL SISTEMI srls"
URL_LETTURA = "https://docs.google.com/spreadsheets/d/1eFQ16WnoyboZCA6M0MtmLdoGdjuVnnI5BDWupgWcAhk/gviz/tq?tqx=out:csv&sheet=Preventivi"
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbzMQu35tgzjEdyUjQ_3O8Jd-zWmdffqko4qT8mv3OIm-F0no5uhh6Aqa68NDjZgr4Pv/exec"

st.set_page_config(page_title="PRODEL", layout="centered")

# --- FUNZIONI ---
def carica_dati():
    try:
        return pd.read_csv(f"{URL_LETTURA}&nocache={datetime.now().timestamp()}")
    except:
        return pd.DataFrame(columns=["Data", "Nome", "Cognome", "Indirizzo", "Telefono", "Descrizione", "Imponibile", "IVA_Perc", "Totale_Ivato"])

def genera_pdf(dati):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, NOME_AZIENDA, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 7, f"Cliente: {dati['Nome']} {dati['Cognome']}", ln=True)
    pdf.cell(0, 7, f"Oggetto: {dati['Descrizione']}", ln=True)
    pdf.ln(10)
    pdf.cell(0, 10, f"TOTALE: {dati['Totale_Ivato']} euro", border=1, ln=True)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFACCIA ---
st.title("PRODEL SISTEMI - Gestione")

tab1, tab2 = st.tabs(["➕ Nuovo Preventivo", "🗄️ Archivio"])

with tab1:
    with st.form("my_form"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome")
        cognome = c2.text_input("Cognome")
        desc = st.text_area("Descrizione lavori")
        imp = st.number_input("Imponibile (€)", value=0.0)
        iva = st.number_input("IVA (%)", value=22)
        
        tot = imp * (1 + iva/100)
        st.write(f"### Totale Ivato: {tot:.2f} €")
        
        if st.form_submit_button("SALVA PREVENTIVO"):
            payload = {
                "Data": datetime.now().strftime("%d/%m/%Y"),
                "Nome": nome, "Cognome": cognome, "Indirizzo": "",
                "Telefono": "", "Descrizione": desc, "Imponibile": imp,
                "IVA_Perc": iva, "Totale_Ivato": tot
            }
            res = requests.post(URL_SCRITTURA, json=payload)
            if res.status_code == 200:
                st.success("Salvato!")
                st.balloons()
            else:
                st.error("Errore salvataggio")

with tab2:
    df = carica_dati()
    for i, row in df.iloc[::-1].iterrows():
        with st.expander(f"{row['Data']} - {row['Cognome']}"):
            st.write(f"Importo: {row['Totale_Ivato']} €")
            st.download_button("Scarica PDF", data=genera_pdf(row), file_name="Prev.pdf", key=f"d_{i}")
