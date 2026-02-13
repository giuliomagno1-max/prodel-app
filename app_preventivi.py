import streamlit as st
from fpdf import FPDF
import pandas as pd
import requests # Serve per inviare i dati al portinaio
import os

# --- DATI FISSI ---
NOME_AZIENDA = "PRODEL SISTEMI srls"
INDIRIZZO_AZIENDA = "Via Padre Teodoro Valle, Priverno(LT)"
TEL_AZIENDA = "Tel. 380 7523630"
LOGO_FILE = "logo.png"

# --- CONFIGURAZIONE CLOUD ---
URL_LETTURA = "https://docs.google.com/spreadsheets/d/1eFQ16WnoyboZCA6M0MtmLdoGdjuVnnI5BDWupgWcAhk/gviz/tq?tqx=out:csv&sheet=Preventivi"
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbzysEHWi811ETCf1skxp4N4IPGuCABFJvuUVudIWh-vW9vkmwlxdugFCUnoUN5P3sFQ/exec" # <--- Incolla qui il link di Apps Script

st.set_page_config(page_title="PRODEL Cloud Free", layout="centered")

def carica_dati():
    try: return pd.read_csv(URL_LETTURA)
    except: return pd.DataFrame(columns=["Data", "Nome", "Cognome", "Indirizzo", "Telefono", "Descrizione", "Imponibile", "IVA_Perc", "Totale_Ivato"])

# --- FUNZIONE PDF (Sempre la stessa) ---
def genera_pdf(dati):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists(LOGO_FILE): pdf.image(LOGO_FILE, 10, 8, 30)
    pdf.set_font("Arial", 'B', 12); pdf.set_x(50); pdf.cell(0, 5, NOME_AZIENDA, ln=True)
    pdf.set_font("Arial", size=10); pdf.set_x(50); pdf.cell(0, 5, INDIRIZZO_AZIENDA, ln=True)
    pdf.set_x(50); pdf.cell(0, 5, TEL_AZIENDA, ln=True)
    pdf.ln(20); pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "PREVENTIVO", ln=True, align='C')
    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 7, "SPETT.LE CLIENTE:", ln=True)
    pdf.set_font("Arial", size=11); pdf.cell(0, 6, f"{dati['Nome']} {dati['Cognome']}", ln=True)
    pdf.cell(0, 6, f"{dati['Indirizzo']}", ln=True); pdf.cell(0, 6, f"Tel: {dati['Telefono']}", ln=True); pdf.ln(10)
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 7, "OGGETTO:", ln=True); pdf.set_font("Arial", size=11); pdf.multi_cell(0, 7, str(dati['Descrizione'])); pdf.ln(10)
    imp, iva_p = float(dati['Imponibile']), float(dati['IVA_Perc'])
    iva_c = imp * (iva_p / 100)
    pdf.set_draw_color(200, 200, 200); pdf.cell(140, 10, "TOTALE IMPONIBILE", border=1); pdf.cell(0, 10, f"{imp:.2f} euro", border=1, ln=True, align='R')
    pdf.cell(140, 10, f"IVA {iva_p:.0f}%", border=1); pdf.cell(0, 10, f"{iva_c:.2f} euro", border=1, ln=True, align='R')
    pdf.set_font("Arial", 'B', 12); pdf.cell(140, 12, "TOTALE GENERALE", border=1); pdf.cell(0, 12, f"{(imp + iva_c):.2f} euro", border=1, ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- NAVIGAZIONE ---
if 'pagina' not in st.session_state: st.session_state.pagina = "Nuovo"

st.sidebar.title("Menù")
if st.sidebar.button("➕ Nuovo"): st.session_state.pagina = "Nuovo"; st.rerun()
if st.sidebar.button("🗄️ Archivio"): st.session_state.pagina = "Archivio"; st.rerun()

if st.session_state.pagina == "Nuovo":
    st.header("Compilazione")
    with st.form("main_form"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome")
        cognome = c2.text_input("Cognome")
        indirizzo = st.text_input("Indirizzo")
        tel = st.text_input("Telefono")
        desc = st.text_area("Descrizione")
        imp = st.number_input("Imponibile (€)", value=0.0)
        iva_p = st.number_input("IVA (%)", value=22)
        tot_ivato = imp * (1 + iva_p/100)
        st.info(f"### TOTALE: {tot_ivato:.2f} €")
        
        if st.form_submit_button("💾 SALVA SU GOOGLE"):
            payload = {
                "Data": pd.Timestamp.now().strftime("%d/%m/%Y"),
                "Nome": nome, "Cognome": cognome, "Indirizzo": indirizzo,
                "Telefono": tel, "Descrizione": desc, "Imponibile": imp, 
                "IVA_Perc": iva_p, "Totale_Ivato": tot_ivato
            }
            # INVIA I DATI AL PORTINAIO (APPS SCRIPT)
            response = requests.post(URL_SCRITTURA, json=payload)
            if response.status_code == 200:
                st.success("Salvato correttamente!")
                st.session_state.pagina = "Archivio"
                st.rerun()
            else: st.error("Errore nel salvataggio.")

elif st.session_state.pagina == "Archivio":
    st.header("Archivio")
    df = carica_dati()
    for i, row in df.iloc[::-1].iterrows():
        with st.expander(f"{row['Nome']} {row['Cognome']} - {row['Totale_Ivato']:.2f}€"):
            pdf_b = genera_pdf(row)
            st.download_button("📄 PDF", data=pdf_b, file_name=f"Prev_{row['Cognome']}.pdf", key=f"p_{i}")





