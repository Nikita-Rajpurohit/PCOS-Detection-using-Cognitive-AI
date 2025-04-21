from flask import Blueprint, render_template

gynecologist_bp = Blueprint('gynecologist', __name__)

@gynecologist_bp.route('/gynecologist')
def gynecologist():
    return render_template('gynecologist.html')