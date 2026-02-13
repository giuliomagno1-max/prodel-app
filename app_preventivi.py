import streamlit as st
from fpdf import FPDF
import pandas as pd
import requests
import os
from datetime import datetime

# --- DATI AZIENDALI ---
NOME_AZIENDA = "PRODEL SISTEMI srls"
INDIRIZZO_AZIENDA = "Via Padre Teodoro Valle, Priverno(LT)"
TEL_AZIENDA = "Tel. 380 7523630"
LOGO_FILE = "logo.png"

# --- CONFIGURAZIONE CLOUD (CONTROLLA QUESTI LINK) ---
# Link per LEGGERE (CSV)
URL_LETTURA = "https://docs.google.com/spreadsheets/d/1eFQ16WnoyboZCA6M0MtmLdoGdjuVnnI5BDWupgWcAhk/gviz/tq?tqx=out:csv&sheet=Preventivi"
# Link per SCRIVERE (Apps Script) - ASSICURATI CHE SIA L'URL /exec
URL_SCRITTURA = "https://script.google.com/macros/s/AKfycbzysEHWi811ETCf1skxp4N4IPGuCABFJvuUVudIWh-vW9vkmwlxdugFCUnoUN5P3sFQ/exec"

st.set_page_config(page_title="PRODEL Cloud", layout="centered")

# --- FUNZIONE CARICAMENTO DATI ---
def carica_dati():
    try:
        # Il parametro cache_token serve a forzare Streamlit a scaricare i dati nuovi ogni volta
        return pd.read_csv(f"{URL_LETTURA}&nocache={datetime.now().timestamp()}")
    except Exception:
        return pd.DataFrame(columns=["Data", "Nome", "Cognome", "Indirizzo", "Telefono", "Descrizione", "Imponibile", "IVA_Perc", "Totale_Ivato"])

# --- FUNZIONE GENERAZIONE PDF ---
def genera_pdf(dati):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Gestione Logo
        if os.path.exists(LOGO_FILE):
            pdf.image(LOGO_FILE, 10, 8, 33)
        
        # Intestazione Azienda
        pdf.set_font("Arial", 'B', 12)
        pdf.set_x(50)
        pdf.cell(0, 5, NOME_AZIENDA, ln=True)
        pdf.set_font("Arial", size=10)
        pdf.set_x(50)
        pdf.cell(0, 5, INDIRIZZO_AZIENDA, ln=True)
        pdf.set_x(50)
        pdf.cell(0, 5, TEL_AZIENDA, ln=True)
        
        # Titolo
        pdf.ln(20)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "PREVENTIVO", ln=True, align='C')
        
        # Dati Cliente
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 7, "SPETT.LE CLIENTE:", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 6, f"{dati.get('Nome', '')} {dati.get('Cognome', '')}", ln=True)
        pdf.cell(0, 6, f"{dati.get('Indirizzo', '')}", ln=True)
        pdf.cell(0, 6, f"Tel: {dati.get('Telefono', '')}", ln=True)
        
        # Oggetto/Descrizione
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 7, "OGGETTO:", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, str(dati.get('Descrizione', '')))
        
        # Tabella Costi
        pdf.ln(10)
        imp = float(dati.get('Imponibile', 0))
        iva_p = float(dati.get('IVA_Perc', 22))
        val_iva = imp * (iva_p / 100)
        tot = imp + val_iva
        
        pdf.set_draw_color(200, 200, 200)
        pdf.cell(140, 10, "TOTALE IMPONIBILE", border=1)
        pdf.cell(0, 10, f"{imp:.2f} euro", border=1, ln=True, align='R')
        pdf.cell(140, 10, f"IVA {iva_p:.0f}%", border=1)
        pdf.cell(0, 10, f"{val_iva:.2f} euro", border=1, ln=True, align='R')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(140, 12, "TOTALE GENERALE", border=1)
        pdf.cell(0, 12, f"{tot:.2f} euro", border=1, ln=True, align='R')
        
        return pdf.output(dest='S').encode('latin-1', 'replace')
    except Exception as e:
        st.error(f"Errore generazione PDF: {e}")
        return None

# --- NAVIGAZIONE SIDEBAR ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Nuovo"

st.sidebar.image(LOGO_FILE) if os.path.exists(LOGO_FILE) else st.sidebar.title("PRODEL")
st.sidebar.divider()

if st.sidebar.button("➕ NUOVO PREVENTIVO", use_container_width=True):
    st.session_state.pagina = "Nuovo"
    st.rerun()

if st.sidebar.button("🗄️ ARCHIVIO CLOUD", use_container_width=True):
    st.session_state.pagina = "Archivio"
    st.rerun()

# --- PAGINA: NUOVO PREVENTIVO ---
if st.session_state.pagina == "Nuovo":
    st.title("Nuovo Preventivo")
    
    with st.form("form_preventivo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome")
        cognome = c2.text_input("Cognome")
        indirizzo = st.text_input("Indirizzo")
        telefono = st.text_input("Telefono")
        descrizione = st.text_area("Descrizione Lavori")
        
        c3, c4 = st.columns(2)
        imponibile = c3.number_input("Imponibile (€)", min_value=0.0, step=0.01, format="%.2f")
        iva_perc = c4.number_input("IVA (%)", min_value=0, max_value=100, value=22)
        
        totale_ivato = imponibile * (1 + iva_perc/100)
        st.subheader(f"Totale Stimato: {totale_ivato:.2f} €")
        
        submit = st.form_submit_button("💾 SALVA E ARCHIVIA", use_container_width=True)
        
        if submit:
            if not nome or not cognome:
                st.error("Inserisci almeno Nome e Cognome!")
            else:
                payload = {
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Nome": nome,
                    "Cognome": cognome,
                    "Indirizzo": indirizzo,
                    "Telefono": telefono,
                    "Descrizione": descrizione,
                    "Imponibile": imponibile,
                    "IVA_Perc": iva_perc,
                    "Totale_Ivato": totale_ivato
                }
                
                try:
                    with st.spinner("Salvataggio in corso..."):
                        res = requests.post(URL_SCRITTURA, json=payload, timeout=15)
                        if res.status_code == 200:
                            st.success("✅ Salvataggio completato con successo!")
                            st.balloons()
                        else:
                            st.error(f"Errore del server Google: {res.status_code}")
                except Exception as e:
                    st.error(f"Impossibile collegarsi al Cloud: {e}")

# --- PAGINA: ARCHIVIO ---
elif st.session_state.pagina == "Archivio":
    st.title("Archivio Preventivi")
    df = carica_dati()
    
    if df.empty:
        st.warning("L'archivio è vuoto. Crea il tuo primo preventivo!")
    else:
        # Invertiamo l'ordine per vedere i più recenti in alto
        for i, row in df.iloc[::-1].iterrows():
            # Controllo per evitare errori se mancano dati nella riga
            titolo = f"{row.get('Data', 'N.D.')} - {row.get('Cognome', 'Senza Nome')} {row.get('Nome', '')}"
            with st.expander(titolo):
                st.write(f"**Indirizzo:** {row.get('Indirizzo', '-')}")
                st.write(f"**Oggetto:** {row.get('Descrizione', '-')}")
                st.write(f"**Totale:** {row.get('Totale_Ivato', 0)} €")
                
                pdf_data = genera_pdf(row)
                if pdf_data:
                    st.download_button(
                        label="📄 Scarica PDF",
                        data=pdf_data,
                        file_name=f"Preventivo_{row.get('Cognome', 'PRODEL')}.pdf",
                        mime="application/pdf",
                        key=f"btn_{i}"
                    )







