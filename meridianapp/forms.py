from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,TextAreaField
from wtforms.validators import DataRequired,Email,Length,EqualTo
from flask_wtf.file import FileAllowed, FileField, FileRequired

class ContactForm(FlaskForm):
    name = StringField("Your Name: ",validators=[DataRequired(message="Please enter your name")])
    email = StringField("Your Email: ",validators=[Email(message="Invalid email, check and retype."),DataRequired(message="Your email address is important, please enter it")])
    subject = StringField("Subject: ",validators=[DataRequired(message="Please enter a message subject ot title")])
    message = TextAreaField("Message", validators=[DataRequired(),Length(min=10, max=150, message="Keep it consise and presise, message characters cannot exceed 150")])
    submit = SubmitField("Send Message")