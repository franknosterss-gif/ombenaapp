from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    resultats = []
    surface_totale = 0
    deperdition_totale = 0
    btu_total = 0
    kw_total = 0
    cout_total = 0
    type_batiment = "residentiel"
    
    if request.method == 'POST':
        type_batiment = request.form.get('type_batiment', 'residentiel')
        
        # Récupération des listes envoyées par le formulaire dynamique
        noms_pieces = request.form.getlist('nom_piece[]')
        surfaces = request.form.getlist('surface[]')
        expositions = request.form.getlist('exposition[]')
        isolants = request.form.getlist('isolant[]')
        
        # Facteur selon la destination globale du bâtiment
        facteur_batiment = 1.0
        if type_batiment == 'bureaux':
            facteur_batiment = 1.20
        elif type_batiment == 'commercial':
            facteur_batiment = 1.35
            
        for i in range(len(noms_pieces)):
            try:
                nom = noms_pieces[i] if noms_pieces[i] else f"Pièce {i+1}"
                surf = float(surfaces[i])
                expo = expositions[i]
                iso = isolants[i]
                
                # Facteur exposition
                f_expo = 1.0
                if expo == 'plein_sud': f_expo = 1.25
                elif expo == 'baie_vitree': f_expo = 1.40
                elif expo == 'ombrage': f_expo = 0.90
                
                # Facteur isolant
                f_iso = 1.0
                if iso == 'beton_plein': f_iso = 1.30
                elif iso == 'brique_terre': f_iso = 1.10
                elif iso == 'isole': f_iso = 0.70
                
                f_total = f_expo * f_iso * facteur_batiment
                
                dep_piece = round(surf * 15 * f_total, 1)
                btu_piece = round(surf * 120 * f_total, 1)
                
                surface_totale += surf
                deperdition_totale += dep_piece
                btu_total += btu_piece
                
                resultats.append({
                    'nom': nom,
                    'surface': surf,
                    'exposition': expo,
                    'isolant': iso,
                    'deperdition': dep_piece,
                    'btu': btu_piece
                })
            except ValueError:
                continue
                
        kw_total = round(btu_total / 3412.14, 2)
        cout_total = round(btu_total * 350, -3)
        deperdition_totale = round(deperdition_totale, 1)
        btu_total = round(btu_total, 1)
        
    return render_template('index.html', 
                           resultats=resultats, 
                           surface_totale=surface_totale, 
                           deperdition_totale=deperdition_totale, 
                           btu_total=btu_total, 
                           kw_total=kw_total, 
                           cout_total=cout_total, 
                           type_batiment=type_batiment)

@app.route('/telecharger_pdf')
def telecharger_pdf():
    surface_totale = request.args.get('surface_totale', '0')
    deperdition_totale = request.args.get('deperdition_totale', '0')
    btu_total = request.args.get('btu_total', '0')
    kw_total = request.args.get('kw_total', '0')
    cout_total = request.args.get('cout_total', '0')
    type_batiment = request.args.get('type_batiment', 'residentiel')

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # En-tête du document
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, "RAPPORT D'EXPERTISE THERMIQUE & CLIMATIQUE")
    p.setFont("Helvetica", 12)
    p.drawString(50, 730, "Commune d'Owendo - Gabon | OmbenaApp v6.0")
    p.drawString(50, 710, "Expert : Ombena Amoro Frank (Ingénieur en Énergétique)")
    p.line(50, 700, 550, 700)
    
    # Contenu global
    p.drawString(50, 640, f"Destination du bâtiment : {type_batiment}")
    p.drawString(50, 610, f"Surface totale analysée : {surface_totale} m²")
    p.drawString(50, 580, f"Déperditions thermiques totales : {deperdition_totale} W")
    p.drawString(50, 550, f"Puissance Climatisation globale : {btu_total} BTU ({kw_total} kW)")
    p.drawString(50, 520, f"Estimation budgétaire Fourniture & Pose : {cout_total} XAF")
    p.drawString(50, 490, "Statut du document : Rapport officiel validé (Version Pièce par Pièce)")
    
    # Pied de page
    p.line(50, 100, 550, 100)
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 80, "Document officiel généré par OmbenaApp - Conçu par Ombena Amoro Frank")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Rapport_Global_OmbenaApp.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
