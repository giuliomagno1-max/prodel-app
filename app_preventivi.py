import streamlit as st
from fpdf import FPDF
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# --- DATI FISSI ---
NOME_AZIENDA = "PRODEL SISTEMI srls"
INDIRIZZO_AZIENDA = "Via Padre Teodoro Valle, Priverno(LT)"
TEL_AZIENDA = "Tel. 380 7523630"
LOGO_FILE = "logo.png"
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1eFQ16WnoyboZCA6M0MtmLdoGdjuVnnI5BDWupgWcAhk/edit?gid=0#gid=0" # <--- METTI IL TUO LINK QUI

st.set_page_config(page_title=f"PRODEL - Cloud", layout="centered")

# --- CONNESSIONE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_dati():
    return conn.read(spreadsheet=URL_FOGLIO, worksheet="Preventivi")

# --- FUNZIONE PDF (Invariata) ---
def genera_pdf(dati):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists(LOGO_FILE): pdf.image(LOGO_FILE, 10, 8, 30)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_x(50); pdf.cell(0, 5, NOME_AZIENDA, ln=True)
    pdf.set_font("Arial", size=10)
    pdf.set_x(50); pdf.cell(0, 5, INDIRIZZO_AZIENDA, ln=True)
    pdf.set_x(50); pdf.cell(0, 5, TEL_AZIENDA, ln=True)
    pdf.ln(20); pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "PREVENTIVO", ln=True, align='C')
    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 7, "SPETT.LE CLIENTE:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 6, f"{dati['Nome']} {dati['Cognome']}", ln=True)
    pdf.cell(0, 6, f"{dati['Indirizzo']}", ln=True)
    pdf.cell(0, 6, f"Tel: {dati['Telefono']}", ln=True)
    pdf.ln(10); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 7, "OGGETTO:", ln=True)
    pdf.set_font("Arial", size=11); pdf.multi_cell(0, 7, str(dati['Descrizione']))
    pdf.ln(10)
    imp, iva_p = float(dati['Imponibile']), float(dati['IVA_Perc'])
    iva_c = imp * (iva_p / 100)
    pdf.set_draw_color(200, 200, 200)
    pdf.cell(140, 10, "TOTALE IMPONIBILE", border=1)
    pdf.cell(0, 10, f"{imp:.2f} euro", border=1, ln=True, align='R')
    pdf.cell(140, 10, f"IVA {iva_p:.0f}%", border=1)
    pdf.cell(0, 10, f"{iva_c:.2f} euro", border=1, ln=True, align='R')
    pdf.set_font("Arial", 'B', 12); pdf.cell(140, 12, "TOTALE GENERALE", border=1)
    pdf.cell(0, 12, f"{(imp + iva_c):.2f} euro", border=1, ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- LOGICA NAVIGAZIONE ---
if 'edit_index' not in st.session_state: st.session_state.edit_index = None
if 'pagina' not in st.session_state: st.session_state.pagina = "Nuovo"

st.sidebar.title("PRODEL Cloud")
if st.sidebar.button("➕ Nuovo Preventivo"):
    st.session_state.edit_index = None
    st.session_state.pagina = "Nuovo"
    st.rerun()
if st.sidebar.button("🗄️ Archivio Cloud"):
    st.session_state.pagina = "Archivio"
    st.rerun()

# --- PAGINA NUOVO ---
if st.session_state.pagina == "Nuovo":
    st.header("Compilazione")
    df = carica_dati()
    vals = {"Nome": "", "Cognome": "", "Indirizzo": "", "Telefono": "", "Descrizione": "", "Imponibile": 0.0, "IVA_Perc": 22}
    
    if st.session_state.edit_index is not None:
        vals = df.iloc[st.session_state.edit_index].to_dict()
        st.warning(f"Modifica: {vals['Nome']}")

    with st.form("main_form"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome", value=vals["Nome"])
        cognome = c2.text_input("Cognome", value=vals["Cognome"])
        indirizzo = st.text_input("Indirizzo", value=vals["Indirizzo"])
        desc = st.text_area("Descrizione", value=vals["Descrizione"])
        imp = st.number_input("Imponibile (€)", value=float(vals["Imponibile"]))
        iva_p = st.number_input("IVA (%)", value=int(vals["IVA_Perc"]))
        
        if st.form_submit_button("💾 SALVA SU GOOGLE SHEETS"):
            nuovo = pd.DataFrame([{
                "Data": pd.Timestamp.now().strftime("%d/%m/%Y"),
                "Nome": nome, "Cognome": cognome, "Indirizzo": indirizzo,
                "Telefono": vals["Telefono"], "Descrizione": desc, 
                "Imponibile": imp, "IVA_Perc": iva_p, "Totale_Ivato": imp*(1+iva_p/100)
            }])
            # Se modifica, aggiorna la riga, altrimenti aggiungi
            if st.session_state.edit_index is not None:
                df.iloc[st.session_state.edit_index] = nuovo.iloc[0]
                conn.update(spreadsheet=URL_FOGLIO, worksheet="Preventivi", data=df)
            else:
                conn.create(spreadsheet=URL_FOGLIO, worksheet="Preventivi", data=pd.concat([df, nuovo]))
            
            st.session_state.edit_index = None
            st.session_state.pagina = "Archivio"
            st.rerun()

# --- PAGINA ARCHIVIO ---
elif st.session_state.pagina == "Archivio":
    st.header("Archivio su Google Sheets")
    df = carica_dati()
    for i, row in df.iloc[::-1].iterrows():
        with st.expander(f"{row['Nome']} {row['Cognome']} - {row['Totale_Ivato']:.2f}€"):
            c1, c2 = st.columns(2)
            if c1.button("📝 Modifica", key=f"e_{i}"):
                st.session_state.edit_index = i
                st.session_state.pagina = "Nuovo"
                st.rerun()
            pdf_b = genera_pdf(row)

            c2.download_button("📄 PDF", data=pdf_b, file_name="Prev.pdf", key=f"p_{i}")




