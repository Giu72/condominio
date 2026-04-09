#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import smtplib
import json
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_FILE = "config.json"
SCADENZE_FILE = "scadenze.csv"
LOG_FILE = "promemoria_log.txt"
GIORNI_ANTICIPO = 5

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def carica_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def invia_email(config, destinatario, nome, descrizione, importo, data_scadenza):
    oggetto = f"Promemoria scadenza condominiale - {descrizione}"
    corpo = f"""Gentile {nome},

Le ricordiamo che il pagamento di {descrizione} di €{importo:.2f} scade il {data_scadenza}.

La invitiamo a saldare quanto prima.

Cordiali saluti,
Amministratore
"""
    msg = MIMEMultipart()
    msg['From'] = config['mittente_email']
    msg['To'] = destinatario
    msg['Subject'] = oggetto
    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['mittente_email'], config['mittente_password'])
            server.send_message(msg)
        logging.info(f"Inviato a {destinatario} - {descrizione}")
        return True
    except Exception as e:
        logging.error(f"Errore invio a {destinatario}: {e}")
        return False

def main():
    logging.info("=== Avvio script promemoria scadenze ===")
    try:
        config = carica_config()
    except Exception as e:
        logging.error(f"Impossibile caricare config.json: {e}")
        return
    try:
        df = pd.read_csv(SCADENZE_FILE)
        df['data_scadenza'] = pd.to_datetime(df['data_scadenza'])
    except Exception as e:
        logging.error(f"Errore lettura {SCADENZE_FILE}: {e}")
        return
    oggi = datetime.now().date()
    data_limite = oggi + timedelta(days=GIORNI_ANTICIPO)
    mask = (df['stato'].str.lower() == 'non pagato') & \
           (df['data_scadenza'].dt.date >= oggi) & \
           (df['data_scadenza'].dt.date <= data_limite)
    da_inviare = df[mask]
    if da_inviare.empty:
        logging.info("Nessun promemoria da inviare oggi.")
        return
    inviati = 0
    for idx, row in da_inviare.iterrows():
        esito = invia_email(
            config,
            row['condomino_email'],
            row['condomino_nome'],
            row['descrizione'],
            float(row['importo']),
            row['data_scadenza'].strftime('%Y-%m-%d')
        )
        if esito:
            inviati += 1
    logging.info(f"Promemoria inviati: {inviati} su {len(da_inviare)}")
    logging.info("=== Fine script ===\n")

if __name__ == "__main__":
    main()