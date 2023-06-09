from typing import List

from matplotlib import pyplot as plt

from logic.repositories import UserRepository, AccountRepository, CategoryRepository, UserHasCategoryRepository, \
    TransactionRepository
from loguru import logger
from logic.datavalidation import DataValidation
from logic.entities import User, Account, Category, UserCategory, Transaction

import csv
import os


class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.user_category_repository = UserHasCategoryRepository()
        self.category_service = CategoryService()

    def register(self, login: str, password: str, confirm_password: str):

        logger.info(f"User with login {login} wants to register")
        if not (login and password and confirm_password):
            return False, "Fill all fields"
        if not DataValidation.is_passwords_are_same(password, confirm_password):
            return False, "Passwords don't match"
        logger.info(f"Passwords match")
        if self.is_user_exists(login):
            return False, "Such user has already been created"
        else:
            logger.info(f"New user creation...")
            user = User(login=login, password=DataValidation.encode_password(password))
            logger.info(f"Entity with login = {login} created")
            user = self.user_repository.create(user)
            list_cat = ["Food", "Other", "Transport"]

            for category_name in list_cat:
                self.add_category_user(user, category_name)
        return True, f"Successfully registered {login}"

    def login(self, login: str, password: str):
        logger.info(f"User with login {login} wants to login.")
        if not (login and password):
            return False, "Fill all fields"
        if self.is_user_exists(login, case_sensitive=True):
            user = self.user_repository.get_by_param(login)
            logger.info(f"User with {login} found.")
            if DataValidation.is_password_valid(user.password, password):
                user_db = self.user_repository.get_by_param(login)
                return user_db, "Successfully logged in"
            else:
                return False, "Incorrect password"
        else:
            return False, f"User with login {login} don't exist"

    def get_user_by_id(self, id: int):
        logger.info(f"Searching user with id = {id} ")
        return self.user_repository.get_by_param(id)

    def get_user_by_login(self, login: str):
        logger.info(f"Searching user with login = {login} ")
        return self.user_repository.get_by_param(login)


    def update(self, user: User, given_password: str, login: str = None, password: str = None):
        bd_user = self.get_user_by_id(user.id)
        logger.info(f"Update user {user.login}...")
        if not DataValidation.is_password_valid(bd_user.password,
                                                given_password):
            return False, "Given password is wrong"
        if login:
            if login == user.login:
                return False, "Credentials must be changed to update"
            if self.is_user_exists(login):
                return False, "Such login is unavailable"
            user.login = login
            logger.info("Login updated")
        if password:
            if DataValidation.is_password_valid(bd_user.password,
                                                password):
                return False, "Credentials must be changed to update"
            user.password = DataValidation.encode_password(password)
            logger.info("Password updated")
        if login or password:
            return True, self.user_repository.update(user)
        return False, "Empty credentials"


    def delete(self, user: User, given_password: str):
        bd_user = self.get_user_by_id(user.id)
        if not DataValidation.is_password_valid(bd_user.password,
                                                given_password):
            return False, "Given password is wrong"
        logger.info(f"Deleting user {user.login}...")
        if not self.is_user_exists(user.login):
            return False, f"User {user.login} doesn't exist"
        self.user_repository.delete(user)
        return True, f"User {user.login} successfully deleted"

    def is_user_exists(self, login: str, case_sensitive: bool = False) -> bool:
        user = self.user_repository.get_by_param(login, case_sensitive)
        if user:
            return True
        else:
            return False

    def get_user_categories(self, user: User) -> List[Category]:
        logger.info("Getting user repositories...")
        return self.user_category_repository.get_by_param(user)

    def is_user_has_category(self, user: User, category: Category) -> bool:
        result = self.user_category_repository.get_by_param([user, category])
        if result and result[0] > 0:
            return True
        else:
            return False

    def add_category_user(self, user: User, name: str):
        if not name:
            return False, "Name can't be null"
        category = Category(name=name)

        if self.category_service.is_category_exist(category.name):
            category.id = self.category_service.get_category_by_name(name).id
            if self.is_user_has_category(user, category):
                return False, f"Category {category.name} exists"
            return self.user_category_repository.create(
                UserCategory(user=user, category=category)), "Successfully created category"
        else:
            success, message = self.category_service.create(category.name)
            if success:
                return \
                    self.user_category_repository.create(
                        UserCategory(user=user, category=message)), "Successfully created category"
            return False, message

    def delete_category_from_user(self, user: User, category: Category):
        categorydb = self.category_service.get_category_by_name(category.name)
        user_category = UserCategory(user=user, category=categorydb)
        self.user_category_repository.delete(user_category)

        if self.category_service.get_category_count(category) == 0:
            self.category_service.delete(categorydb)


class AccountService:

    def __init__(self):
        self.account_repository = AccountRepository()
        self.transaction_repository = TransactionRepository()

    def create(self, name: str, user: User, balance: str = "0", description: str = ""):
        if not name:
            return False, "Name can't be null "
        if not DataValidation.isfloat(balance):
            return False, f"Wrong format of balance"
        current = float(balance)
        logger.info(f"Creating account with name {name}...")
        if self.is_account_exists(name, user):
            return False, f"Account {name} exists"
        account = Account(name=name, user=user, balance=current, description=description)
        return True, self.account_repository.create(account)

    def get_user_accounts(self, user: User) -> object:
        return self.account_repository.get_by_param(user)

    def get_account_by_id(self, id: int):
        return self.account_repository.get_by_param(id)

    def update(self, account: Account, name: str = None, description: str = None, balance: str = None):
        if not (name or description or balance):
            return False, "Credentials can't be null"

        if account.name == name and account.description == description and account.balance == balance:
            return False, "Credentials must be changed to update"
        logger.info("Updating account...")
        if name:
            if self.is_account_exists(name, account.user):
                return False, "Account with name {name} exist"
            account.name = name
            logger.info("Name updated")
        if description:
            account.description = description
            logger.info("Description updated")
        if balance:
            if not DataValidation.isfloat(balance):
                return False, "Error format"
            correction = float(balance) - account.balance

            success, transaction = self.create_transaction(amount=str(correction), account=account,
                                                           description="Correction")
            if not success:
                return False, "Error while correcting"

            logger.info("Balance updated")
            return True, self.account_repository.get_by_param(account.id)
        else:
            return True, self.account_repository.update(account)

    def delete(self, account: Account):
        if not self.is_account_exists(account.name, account.user):
            return False, f"Account {account.name} doesn't exist"
        self.account_repository.delete(account)
        return True, f"Account {account.name} successfully deleted"

    def is_account_exists(self, name: str, user: User) -> bool:
        user_accounts_names = []
        for account in self.account_repository.get_by_param(user):
            user_accounts_names.append(account.name)
        if len(user_accounts_names) == 0:
            return False
        if name in user_accounts_names:
            return True
        else:
            return False

    def create_transaction(self, amount: str, description: str, account: Account, category: Category = None):
        logger.info(f"Creating transaction...")
        if not amount:
            return False, f"Amount can't be null"
        if not DataValidation.isfloat(amount):
            return False, "Amount must be float"
        transactiondb = self.transaction_repository.create(
            Transaction(amount=float(amount), account=account, description=description, category=category))
        account.balance = account.balance + transactiondb.amount
        self.account_repository.update(account=account)

        return True, transactiondb

    def update_balance(self, account, balance):
        account.balance = balance
        return self.account_repository.update(account)

    def delete_transaction(self, transaction: Transaction):
        self.transaction_repository.delete(transaction)
        return self.update_balance(account=transaction.account,
                                   balance=transaction.account.balance - transaction.amount)

    def update_transaction(self, transaction: Transaction, amount: str = None, description: str = None,
                           category: Category = None):
        if not (amount or description or category):
            return False, f"Credentials can't be null"
        if amount and not DataValidation.isfloat(amount):
            return False, "Amount must be float"
        if amount:
            if not DataValidation.isfloat(amount):
                return False, "Amount must be float"
            famount = float(amount)
            correction = famount - transaction.amount
            transaction.amount = famount
            transaction.account.balance = transaction.account.balance + correction
            self.account_repository.update(transaction.account)
        if description:
            transaction.description = description
        if category:
            transaction.category = category

        return True, self.transaction_repository.update(transaction)

    def get_account_transactions(self, account: Account):
        return self.transaction_repository.get_by_param(account)

    def create_csv_file(self, account):
        filename = f"{account.name}_transactions.csv"
        path = "exports"
        if not os.path.exists(path):
            os.makedirs(path)

        file_path = fr"{path}/{filename}"
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter=',')

            writer.writerow(['id', 'category', 'amount', 'date', 'description'])
            id = 1
            for transaction in self.get_account_transactions(account):
                writer.writerow(
                    [id, transaction.category.name if transaction.category else "None", transaction.amount,
                     transaction.date, transaction.description])
                id += 1

    def generate_average_transactions_plot(self, account):
        transactions = self.get_account_transactions(account)
        categories = {}
        averages = []

        for transaction in transactions:
            category = transaction.category.name if transaction.category else "None"
            if category in categories:
                categories[category].append(transaction.amount)
            else:
                categories[category] = [transaction.amount]

        for category, amounts in categories.items():
            average = sum(amounts) / len(amounts)
            averages.append((category, average))

        averages.sort(key=lambda x: x[1], reverse=True)
        categories = [item[0] for item in averages]
        averages = [item[1] for item in averages]

        plt.figure(figsize=(10, 6))
        plt.bar(categories, averages)
        plt.xlabel("Category")
        plt.ylabel("Average Transaction Amount")
        plt.title("Average Transactions by Categories")
        plt.xticks(rotation=45)
        plt.show()


class CategoryService:

    def __init__(self):
        self.category_repository = CategoryRepository()
        self.user_has_category_repository = UserHasCategoryRepository()

    def create(self, name):
        logger.info(f"Creating category with name {name}...")
        if self.is_category_exist(name):
            return False, f"Category {name} exists"
        category = Category(name)

        return True, self.category_repository.create(category)

    def get_category_by_id(self, id: int):
        return self.category_repository.get_by_param(id)

    def get_category_by_name(self, name: str):
        return self.category_repository.get_by_param(name)

    def update(self, category: Category, name: str):
        if not name:
            return False, "Updated name can’t be null"
        logger.info(f"Update category {category.name}...")
        if category.name == name:
            return False, "Credentials must be changed to update"
        if name:
            if self.is_category_exist(name):
                return False, "Such name is unavailable"
            category.name = name
            logger.info("Name updated")

        return True, self.category_repository.update(category)

    def delete(self, category: Category):
        if not self.is_category_exist(category.name):
            return False, f"Category {category.name} doesn't exist"
        self.delete(category)
        return True, f"Category {category.name} successfully deleted"

    def is_category_exist(self, name: str) -> bool:
        category = self.category_repository.get_by_param(name)
        if category:
            return True
        else:
            return False

    def get_category_count(self, category: Category):
        return self.user_has_category_repository.get_by_param(category)


class TransactionDetailsService:
    @staticmethod
    def to_string_short(transaction: Transaction):
        str = f"Amount: {transaction.amount}\nCategory:"
        if transaction.category is not None:
            str += f" {transaction.category.name}"
        else:
            str += f" System operation"
        return str

    @staticmethod
    def to_string_long(transaction: Transaction):
        str = f"Amount: {transaction.amount} \n" \
              f"Date: {transaction.date}\n" \
              f"Description: {transaction.description} \n"
        if transaction.category is not None:
            str += f"Category:  {transaction.category.name} \n"
        return str
