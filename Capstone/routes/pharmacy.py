from flask import Blueprint, render_template

pharmacy_bp = Blueprint('pharmacy', __name__)

@pharmacy_bp.route('/pharmacy')
def pharmacy():
    return render_template('pharmacy.html')
