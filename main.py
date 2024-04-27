import os

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
# app.config['SECRET KEY'] = 'saitousite40912901092oewiorweoui'
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# DATABASE =====================================================================
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))


class Lists(db.Model):
    __tablename__ = "lists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, unique=False, nullable=False)
    list: Mapped[str] = mapped_column(String(50), unique=False, nullable=False)
    task = relationship("Tasks", back_populates="parent_list")
    total_tasks: Mapped[int] = mapped_column(Integer, nullable=True)


class Tasks(db.Model):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("lists.id"))
    parent_list = relationship("Lists", back_populates="task")
    list: Mapped[str] = mapped_column(String(50), unique=False, nullable=False)
    task: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(150), nullable=True)
    img: Mapped[str] = mapped_column(String(300), nullable=True)


with app.app_context():
    db.create_all()

# FORMS ===========================================================================
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class ListForm(FlaskForm):
    list = StringField("List Name")
    submit = SubmitField('Submit List')


class TaskForm(FlaskForm):
    task = StringField("Task")
    description = StringField("Description (optional)")
    img = StringField("Image URL (optional)")
    submit = SubmitField('Submit Task')

# GLOBALS ========================================================================


# FUNCTIONS ======================================================================

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # check if user already registered
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("Already has an account with that email, try login")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()

        if not user:
            flash("That email does not registered.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home')
def home():
    user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
    all_lists = db.session.execute(db.select(Lists).where(Lists.author_id == current_user.id)).scalars().all()
    db.session.commit()

    return render_template('index.html', all_lists=all_lists, user=user)

@app.route('/<list_name>/<int:list_id>', methods=['GET', 'POST'])
def new_task(list_name, list_id):
    current_list = db.get_or_404(Lists, list_id)
    task_form = TaskForm()
    if task_form.validate_on_submit():
        new_task = Tasks(
                list=list_name,
                parent_list=current_list,
                task=request.form.get("task"),
                description=request.form.get("description"),
                img=request.form.get("img"),
        )
        db.session.add(new_task)

        current_list_tasks = db.session.execute(db.select(Tasks).where(Tasks.list_id == list_id))
        list_total_tasks = len(current_list_tasks.scalars().all())
        update_list = db.get_or_404(Lists, list_id)
        update_list.total_tasks = list_total_tasks

        db.session.commit()
        return redirect(f'/{list_id}')

    user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
    all_lists = db.session.execute(db.select(Lists).where(Lists.author_id == current_user.id)).scalars().all()
    db.session.commit()

    return render_template('new-task.html', form=task_form, user=user, all_lists=all_lists)


@app.route('/new_list', methods=['GET', 'POST'])
def new_list():
    user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
    all_lists = db.session.execute(db.select(Lists).where(Lists.author_id == current_user.id)).scalars().all()
    db.session.commit()

    list_form = ListForm()
    if list_form.validate_on_submit():
        new_list = Lists(
                list=request.form.get("list"),
                author_id=current_user.id
        )
        db.session.add(new_list)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('new-list.html', user=user, form=list_form, all_lists=all_lists)


@app.route('/<int:list_id>')
def show_list(list_id):
    user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
    all_lists = db.session.execute(db.select(Lists).where(Lists.author_id == current_user.id)).scalars().all()
    db.session.commit()

    requested_list = db.get_or_404(Lists, list_id)
    list_tasks = db.session.execute(db.select(Tasks).where(Tasks.list_id == requested_list.id)).scalars().all()
    len_tasks = len(list_tasks)
    return render_template('show-list.html', user=user, list=requested_list, tasks=list_tasks, len_tasks=len_tasks, all_lists=all_lists)


@app.route('/delete_task/<task_id>')
def delete_task(task_id):
    task_to_delete = db.get_or_404(Tasks, task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(f'/{task_to_delete.list_id}')

@app.route('/delete_list/<list_id>')
def delete_list(list_id):
    list_to_delete = db.get_or_404(Lists, list_id)
    db.session.delete(list_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
