from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class ImeiForm(FlaskForm):
    """Form for collecting IMEI input."""
    imei = StringField('IMEI', validators=[DataRequired(), Length(min=15, max=15, message='IMEI must be exactly 15 digits')])
    submit = SubmitField('Submit')