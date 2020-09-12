#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Blueprint, flash, render_template, request, current_app
from flask_login import login_required
from albumy.models import User, Role, Photo, Tag, Comment
from albumy.extensions import db
from albumy.utils import redirect_back
from albumy.decorators import permission_required, admin_required
from albumy.forms.admin import EditProfileAdminForm

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
@permission_required('MODERATE')
def index():
    user_count = User.query.count()
    lock_user_count = User.query.filter_by(locked=True).count()
    block_user_count = User.query.filter_by(active=False).count()
    photo_count = Photo.query.count()
    reported_photos_count = Photo.query.filter(Photo.flag > 0).count()
    tag_count = Tag.query.count()
    comment_count = Comment.query.count()
    reported_comments_count = Comment.query.filter(Comment.flag > 0).count()
    return render_template('admin/index.html', user_count=user_count, lock_user_count=lock_user_count,
                           block_user_count=block_user_count, photo_count=photo_count, reported_photos_count=reported_photos_count,
                           tag_count=tag_count, comment_count=comment_count, reported_comments_count=reported_comments_count)


@admin_bp.route('/profile/<int:user_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)  # 传出被修改的用户作为参数
    if form.validate_on_submit():
        user.name = form.name.data
        role = Role.query.get(form.role.data)
        if role.name == 'Locked':
            user.lock()
        user.role = role
        user.bio = form.bio.data
        user.website = form.website.data
        user.confirmed = form.confirmed.data
        user.active = form.active.data
        user.location = form.location.data
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        flash('Profile updated', 'success')
        return redirect_back()
    form.name.data = user.name
    form.role.data = user.role_id  # role字段存的是角色记录的id
    form.bio.data = user.bio
    form.website.data = user.website
    form.location.data = user.location
    form.username.data = user.username
    form.email.data = user.email
    form.confirmed.data = user.confirmed
    form.active.data = user.active
    return render_template('admin/edit_profile.html', form=form, user=user)


@admin_bp.route('/block/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.block()
    flash('Account blocked', 'info')
    return redirect_back()


@admin_bp.route('/unblock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unblock()
    flash('Block canceled', 'info')
    return redirect_back()


@admin_bp.route('/lock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def lock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.lock()
    flash('Account locked', 'info')
    return redirect_back()


@admin_bp.route('/unlock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unlock()
    flash('Lock canceled', 'info')
    return redirect_back()


@admin_bp.route('/delete/tag/<int:tag_id>', methods=['POST', 'GET'])
@login_required
@permission_required('MODERATE')
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash('Tag deleted.', 'info')
    return redirect_back()


@admin_bp.route('/manage/user')
@login_required
@permission_required('MODERATE')
def manage_user():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_MANAGE_USER_PER_PAGE']
    filter_rule = request.args.get('filter', 'all')
    administrator = Role.query.filter_by(name='Administrator').first()
    moderator = Role.query.filter_by(name='Moderator').first()

    if filter_rule == 'locked':
        filter_users = User.query.filter_by(locked=True)
    elif filter_rule == 'blocked':
        filter_users = User.query.filter_by(active=False)
    elif filter_rule == 'administrator':
        filter_users = User.query.filter_by(role=administrator)
    elif filter_rule == 'moderator':
        filter_users = User.query.filter_by(role=moderator)
    else:
        filter_users = User.query

    pagination = filter_users.order_by(User.member_since.desc()).paginate(page, per_page)
    users = pagination.items
    return render_template('admin/manage_user.html', pagination=pagination, users=users)


@admin_bp.route('/manage/photo', defaults={'order': 'by_flag'})
@admin_bp.route('/manage/photo/<order>')
@login_required
@permission_required('MODERATE')
def manage_photo(order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_MANAGE_PHOTO_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = Photo.query.order_by(Photo.timestamp.desc()).paginate(page, per_page)
        order_rule = 'time'
    else:
        pagination = Photo.query.order_by(Photo.flag.desc()).paginate(page, per_page)
    photos = pagination.items
    return render_template('admin/manage_photo.html', pagination=pagination, photos=photos, order_rule=order_rule)


@admin_bp.route('/manage/tag')
@login_required
@permission_required('MODERATE')
def manage_tag():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_MANAGE_TAG_PER_PAGE']
    pagination = Tag.query.order_by(Tag.id.desc()).paginate(page, per_page)
    tags = pagination.items
    return render_template('admin/manage_tag.html', pagination=pagination, tags=tags)


@admin_bp.route('/manage/comment', defaults={'order': 'by_flag'})
@admin_bp.route('/manage/comment/<order>')
@login_required
@permission_required('MODERATE')
def manage_comment(order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_MANAGE_COMMENT_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page)
        order_rule = 'time'
    else:
        pagination = Comment.query.order_by(Comment.flag.desc()).paginate(page, per_page)
    comments = pagination.items
    return render_template('admin/manage_comment.html', pagination=pagination, comments=comments, order_rule=order_rule)


