from website import create_app
from website.models import User
from website.models import Stats

def check_users():
    app = create_app()

    with app.app_context():
        # Query all users
        all_users = User.query.all()

        # Print email addresses
        for user in all_users:
            print(user.email)
            print(user.password)

if __name__ == '__main__':
    check_users()
