#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import click
from flask import Flask, render_template
from flask_login import current_user

from albumy.extensions import db, bootstrap, mail, moment, login_manager, dropzone, avatars, csrf, whooshee
from albumy.blueprints.main import main_bp
from albumy.blueprints.auth import auth_bp
from albumy.blueprints.user import user_bp
from albumy.blueprints.ajax import ajax_bp
from albumy.blueprints.api import api_bp
from albumy.blueprints.admin import admin_bp
from albumy.settings import config
from albumy.models import User, Role, Permission, roles_permissions, Photo, Collect, Tag, Notification, Follow, Comment


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('albumy')
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errorhandlers(app)
    register_shell_context(app)
    register_template_context(app)
    return app


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)
    dropzone.init_app(app)
    avatars.init_app(app)
    csrf.init_app(app)
    csrf.exempt(api_bp)
    whooshee.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ajax_bp, url_prefix='/ajax')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api/v1')




def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Photo=Photo, Tag=Tag,
                    Follow=Follow, Collect=Collect, Comment=Comment, Notification=Notification)


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
        else:
            notification_count = None
        return dict(notification_count=notification_count)


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        if drop:
            click.confirm('This operation will delete the database, do u want continue', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command()
    def init():
        click.echo('Initializing the database....')
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()

        click.echo('Done.')

    @app.cli.command()
    @click.option('--user', default=10, help='Quantity of users,default is 10.')
    @click.option('--follow', default=30, help='Quantity of follows,default is 30')
    @click.option('--photo', default=30, help='Quantity of photos,default is 30')
    @click.option('--tag', default=20, help='Quantity of tags,default is 20')
    @click.option('--collect', default=50, help='Quantity of collects,default is 50')
    @click.option('--comment', default=100, help='Quantity of comments,default is 100')
    def forge(user, follow, photo, tag, collect, comment):
        from albumy.fakes import fake_admin, fake_user, fake_photo, fake_tag, fake_comment, fake_collect, fake_follow

        db.drop_all()
        db.create_all()

        click.echo('Initializing the role and permissions...')
        Role.init_role()

        click.echo('Generating the administrator')
        fake_admin()

        click.echo(f'Generating {user} users...')
        fake_user(user)

        click.echo(f'Gnerrating {follow} follows...')
        fake_follow(follow)

        click.echo(f'Generating {tag} tags...')
        fake_tag(tag)

        click.echo(f'Generating {photo} photos...')
        fake_photo(photo)

        click.echo(f'Generating {collect} collects..')
        fake_collect(collect)

        click.echo(f'Generating {comment} comments...')
        fake_comment(comment)

        click.echo('Done.')
