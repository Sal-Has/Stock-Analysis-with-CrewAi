from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, HiddenField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired,Optional,Email
from flask_wtf.file import FileAllowed
from wtforms import FloatField

class UploadForm(FlaskForm):
    photo = FileField('Profile Picture', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    x = FloatField('X', default=0)
    y = FloatField('Y', default=0)
    width = FloatField('Width', default=256)
    height = FloatField('Height', default=256)
    submit = SubmitField('Upload')

class UpdateProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    street = StringField('Street', validators=[Optional()])
    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])
    zip_code = StringField('Zip Code', validators=[Optional()])
    submit = SubmitField('Update')