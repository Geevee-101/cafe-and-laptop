from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, URL, InputRequired, Length
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_gravatar import Gravatar


app = Flask(__name__)
app.config['SECRET_KEY'] = 'cafeAndLaptop'
Bootstrap5(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy()
db.init_app(app)

# login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Table format
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    # relationships
    cafe_posts = relationship("Cafe", back_populates="author")
    reviews = relationship("Review", back_populates="review_author")


class Cafe(db.Model):
    __tablename__ = "cafes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    map_url = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    coffee_price = db.Column(db.String(250), nullable=False)
    approval = db.Column(db.Integer)
    # relationships
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="cafe_posts")
    cafe_reviews = relationship("Review", back_populates="parent_cafe")


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    like = db.Column(db.Boolean, nullable=False)
    text = db.Column(db.Text, nullable=False)
    # relationships
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    review_author = relationship("User", back_populates="reviews")
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafes.id"))
    parent_cafe = relationship("Cafe", back_populates="cafe_reviews")


with app.app_context():
    db.create_all()


# Forms
class RegisterForm(FlaskForm):
    name = StringField(label="Username")
    email = StringField(label="Email")
    password = PasswordField(label="Password")
    submit = SubmitField(label="CREATE")


class LoginForm(FlaskForm):
    email = StringField(label="Email")
    password = PasswordField(label="Password")
    submit = SubmitField(label="LOG IN")


class CafeForm(FlaskForm):
    name = StringField('Cafe name', validators=[DataRequired()])
    map_url = StringField('Cafe location on Google Maps (URL)', validators=[DataRequired(), URL()])
    img_url = StringField('Cafe image (URL)', validators=[DataRequired(), URL()])
    location = StringField('Cafe location', validators=[DataRequired()])
    has_sockets = SelectField(
        'Has sockets',
        choices=[('True', 'Yes'), ('False', 'No')],
        validators=[InputRequired()],
        coerce=lambda x: x == 'True'
    )
    has_toilet = SelectField(
        'Has restrooms',
        choices=[('True', 'Yes'), ('False', 'No')],
        validators=[InputRequired()],
        coerce=lambda x: x == 'True'
    )
    has_wifi = SelectField(
        'Has wifi',
        choices=[('True', 'Yes'), ('False', 'No')],
        validators=[InputRequired()],
        coerce=lambda x: x == 'True'
    )
    can_take_calls = SelectField(
        'Can take calls',
        choices=[('True', 'Yes'), ('False', 'No')],
        validators=[InputRequired()],
        coerce=lambda x: x == 'True'
    )
    seats = StringField('How many seats (estimate)?', validators=[DataRequired()])
    coffee_price = StringField('Black coffee price (MYR)', validators=[DataRequired()])
    submit = SubmitField('SUBMIT')


class ReviewForm(FlaskForm):
    like = SelectField(
        'Do you recommend working from here?',
        choices=[('True', 'Yes'), ('False', 'No')],
        validators=[InputRequired()],
        coerce=lambda x: x == 'True'
    )

    text = TextAreaField('Tell us about your experience at this cafe', validators=[InputRequired(), Length(max=250)])
    submit = SubmitField("POST REVIEW")

class DeleteForm(FlaskForm):
    submit = SubmitField("YES, DELETE CAFE")

# Gravatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    new_register_form = RegisterForm()
    if new_register_form.validate_on_submit():
        email_input = new_register_form.email.data
        # result = db.session.execute(db.select(User).where(User.email == email_input))
        # user = result.scalar()
        user = User.query.filter_by(email=email_input).first()
        if user:
            flash("That email is already registered.")
            return redirect(url_for('register'))
        else:
            password_raw = new_register_form.password.data
            password_hash = generate_password_hash(password_raw, method='pbkdf2:sha256', salt_length=8)

            new_user = User()
            new_user.email = new_register_form.email.data
            new_user.password = password_hash
            new_user.name = new_register_form.name.data
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)

        return redirect(url_for("show_all_cafes"))

    return render_template("register.html", form=new_register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email_input = login_form.email.data
        password_input = login_form.password.data
        # result = db.session.execute(db.select(User).where(User.email == email_input))
        # user = result.scalar()
        user = User.query.filter_by(email=email_input).first()
        if user:
            if check_password_hash(user.password, password_input):
                login_user(user)
                return redirect(url_for('show_all_cafes'))
            else:
                flash("Email/Password is invalid", "danger")
                return redirect(url_for('login'))
        else:
            flash("Email/Password is invalid", "danger")
            return redirect(url_for('login'))

    return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/cafes", methods=["GET", "POST"])
def show_all_cafes():
    result = db.session.execute(db.select(Cafe))
    cafes = result.scalars().all()
    return render_template('all-cafes.html', all_cafes=cafes)


@app.route("/new-cafe", methods=["GET", "POST"])
@login_required
def add_new_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe()
        new_cafe.name = form.name.data
        new_cafe.map_url = form.map_url.data
        new_cafe.img_url = form.img_url.data
        new_cafe.location = form.location.data
        new_cafe.has_sockets = form.has_sockets.data
        new_cafe.has_toilet = form.has_toilet.data
        new_cafe.has_wifi = form.has_wifi.data
        new_cafe.can_take_calls = form.can_take_calls.data
        new_cafe.seats = form.seats.data
        new_cafe.coffee_price = form.coffee_price.data
        new_cafe.approval = None
        new_cafe.author = current_user

        db.session.add(new_cafe)
        db.session.commit()

        return redirect(url_for("show_all_cafes"))
    return render_template("add-cafe.html", form=form)


@app.route("/cafe/<int:cafe_id>")
def show_cafe(cafe_id):
    requested_cafe = db.get_or_404(Cafe, cafe_id)
    return render_template("cafe.html", cafe=requested_cafe)


@app.route("/cafe/<int:cafe_id>/edit-cafe", methods=["GET", "POST"])
@login_required
def edit_cafe(cafe_id):
    requested_cafe = db.get_or_404(Cafe, cafe_id)
    form = CafeForm()
    if request.method == 'GET':
        form.name.data = requested_cafe.name
        form.map_url.data = requested_cafe.map_url
        form.img_url.data = requested_cafe.img_url
        form.location.data = requested_cafe.location
        form.has_sockets.data = requested_cafe.has_sockets
        form.has_toilet.data = requested_cafe.has_toilet
        form.has_wifi.data = requested_cafe.has_wifi
        form.can_take_calls.data = requested_cafe.can_take_calls
        form.seats.data = requested_cafe.seats
        form.coffee_price.data = requested_cafe.coffee_price

    if form.validate_on_submit():
        requested_cafe.name = form.name.data
        requested_cafe.map_url = form.map_url.data
        requested_cafe.img_url = form.img_url.data
        requested_cafe.location = form.location.data
        requested_cafe.has_sockets = form.has_sockets.data
        requested_cafe.has_toilet = form.has_toilet.data
        requested_cafe.has_wifi = form.has_wifi.data
        requested_cafe.can_take_calls = form.can_take_calls.data
        requested_cafe.seats = form.seats.data
        requested_cafe.coffee_price = form.coffee_price.data

        db.session.commit()

        return redirect(url_for("show_cafe", cafe_id=requested_cafe.id))
    return render_template("edit-cafe.html", cafe=requested_cafe, form=form)


@app.route("/cafe/<int:cafe_id>/post-review", methods=["GET", "POST"])
@login_required
def post_review(cafe_id):
    requested_cafe = db.get_or_404(Cafe, cafe_id)
    review_form = ReviewForm()
    if review_form.validate_on_submit():
        new_review = Review()
        new_review.like = review_form.like.data
        new_review.text = review_form.text.data
        new_review.review_author = current_user
        new_review.parent_cafe = requested_cafe

        db.session.add(new_review)

        # calculate new approval
        like = 0
        dislike = 0
        for review in requested_cafe.cafe_reviews:
            if review.like:
                like = like + 1
            else:
                dislike = dislike + 1
        total = like + dislike
        new_approval = (like/total) * 100
        requested_cafe.approval = new_approval

        db.session.commit()

        return redirect(url_for("show_cafe", cafe_id=requested_cafe.id))
    return render_template("post-review.html", cafe=requested_cafe, form=review_form)


@app.route("/cafe/<int:cafe_id>/delete", methods=["GET", "POST"])
@login_required
def delete_cafe(cafe_id):
    requested_cafe = db.get_or_404(Cafe, cafe_id)
    form = DeleteForm()
    if form.validate_on_submit():
        db.session.delete(requested_cafe)

        # delete reviews associated with cafe as well (by deleting reviews with no values for cafe_id)
        result = db.session.execute(db.select(Review))
        cafe_reviews = result.scalars().all()
        for review in cafe_reviews:
            if not review.cafe_id:
                db.session.delete(review)

        db.session.commit()

        return redirect(url_for("show_all_cafes"))
    return render_template("delete-cafe.html", cafe=requested_cafe, form=form)


if __name__ == "__main__":
    app.run(debug=True)
