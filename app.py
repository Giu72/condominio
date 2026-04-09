#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import subprocess
import json
from datetime import date, timedelta, datetime
import os

app = Flask(__name__)
app.secret_key = 'cambia_questa_chiave_in_produzione'

CSV_FILE = 'scadenze.csv'
CONFIG_FILE = 'config.json'

# ------------------------------
# FUNZIONI DI LETTURA/SCRITTURA CSV
# ------------------------------
def leggi_scadenze():
    try:
        df = pd.read_csv(CSV_FILE)
        # converti la data in stringa YYYY-MM-DD
        df['data_scadenza'] = pd.to_datetime(df['data_scadenza']).dt.strftime('%Y-%m-%d')
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Errore lettura CSV: {e}")
        return []

def scrivi_scadenze(records):
    df = pd.DataFrame(records)
    df.to_csv(CSV_FILE, index=False)

# ------------------------------
# ROTTA PRINCIPALE (con classi CSS precalcolate)
# ------------------------------
@app.route('/')
def index():
    scadenze = leggi_scadenze()
    oggi = date.today()
    
    for s in scadenze:
        data_scad = datetime.strptime(s['data_scadenza'], '%Y-%m-%d').date()
        if s['stato'] == 'pagato':
            s['row_class'] = 'table-success'
        elif data_scad < oggi:
            s['row_class'] = 'table-danger'
        elif data_scad <= oggi + timedelta(days=5):
            s['row_class'] = 'table-warning'
        else:
            s['row_class'] = ''
    
    return render_template('index.html', scadenze=scadenze)

# ------------------------------
# AGGIUNGI NUOVA SCADENZA
# ------------------------------
@app.route('/aggiungi', methods=['POST'])
def aggiungi():
    nuova = {
        'condomino_email': request.form['email'],
        'condomino_nome': request.form['nome'],
        'descrizione': request.form['descrizione'],
        'importo': float(request.form['importo']),
        'data_scadenza': request.form['data_scadenza'],
        'stato': request.form['stato']
    }
    scadenze = leggi_scadenze()
    scadenze.append(nuova)
    scrivi_scadenze(scadenze)
    flash('Scadenza aggiunta con successo!', 'success')
    return redirect(url_for('index'))

# ------------------------------
# MODIFICA SCADENZA
# ------------------------------
@app.route('/modifica/<int:idx>', methods=['GET', 'POST'])
def modifica(idx):
    scadenze = leggi_scadenze()
    if request.method == 'POST':
        scadenze[idx] = {
            'condomino_email': request.form['email'],
            'condomino_nome': request.form['nome'],
            'descrizione': request.form['descrizione'],
            'importo': float(request.form['importo']),
            'data_scadenza': request.form['data_scadenza'],
            'stato': request.form['stato']
        }
        scrivi_scadenze(scadenze)
        flash('Scadenza modificata!', 'success')
        return redirect(url_for('index'))
    else:
        return render_template('modifica.html', scadenza=scadenze[idx], idx=idx)

# ------------------------------
# ELIMINA SCADENZA
# ------------------------------
@app.route('/elimina/<int:idx>')
def elimina(idx):
    scadenze = leggi_scadenze()
    scadenze.pop(idx)
    scrivi_scadenze(scadenze)
    flash('Scadenza eliminata', 'warning')
    return redirect(url_for('index'))

# ------------------------------
# INVIO PROMEMORIA (usa lo script esistente)
# ------------------------------
@app.route('/invia_promemoria')
def invia_promemoria():
    try:
        risultato = subprocess.run(
            ['python', 'promemoria_scadenze.py'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if risultato.returncode == 0:
            flash(f'Promemoria inviati con successo. Output: {risultato.stdout}', 'success')
        else:
            flash(f'Errore nell\'invio: {risultato.stderr}', 'danger')
    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
    return redirect(url_for('index'))

# ------------------------------
# AVVIO SERVER
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)