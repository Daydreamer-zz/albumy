#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms import validators
from wtforms.validators import DataRequired, Email, Length, ValidationError
from albumy.forms.user import EditProfileForm
from albumy.models import User, Role


class EditProfileAdminForm(EditProfileForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    role = SelectField('Role', coerce=int)
    active = BooleanField('Active')
    confirmed = BooleanField('Confirmed')
    submit = SubmitField()

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, filed):
        if filed.data != self.user.email and User.query.filter_by(email=filed.data).first():
            raise ValidationError('The email is already in user.')
