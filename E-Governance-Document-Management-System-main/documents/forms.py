from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FileField, RadioField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileRequired, FileAllowed

class UploadDocumentForm(FlaskForm):
    document_name = StringField('Document Name', validators=[DataRequired()])
    
    document_type = SelectField(
        'Document Type', 
        choices=[
            ('', 'Select document type...'),
            ('Educational Certificate', 'Educational Certificate'),
            ('Identity Document', 'Identity Document'),
            ('Financial Document', 'Financial Document'),
            ('Legal Document', 'Legal Document'),
            ('Medical Record', 'Medical Record'),
            ('Property Document', 'Property Document'),
            ('Other', 'Other')
        ],
        validators=[DataRequired()]
    )
    
    file = FileField(
        'Document File', 
        validators=[
            FileRequired(),
            FileAllowed(
                ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'], 
                'Invalid file type'
            )
        ]
    )
    
    selected_user = SelectField(
        'Select User', 
        choices=[], 
        validators=[Optional()]
    )
    
    validity_type = RadioField(
        'Document Validity',
        choices=[
            ('permanent', 'Permanent (No expiry date)'),
            ('temporary', 'Temporary (Has expiry date)')
        ],
        default='permanent'
    )
    
    expiry_date = DateField(
        'Expiry Date', 
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    
    renewal_required = RadioField(
        'Renewal Required',
        choices=[
            ('true', 'Yes'),
            ('false', 'No')
        ],
        default='false'
    )
    
    submit = SubmitField('Upload Document')
