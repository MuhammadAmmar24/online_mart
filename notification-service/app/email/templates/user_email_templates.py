

def account_creation_email(full_name):
    subject = "Welcome to Ammar Mart - Account Created Successfully"
    message = f"""
Greetings {full_name},

Congratulations! Your account with Ammar Mart has been successfully created.

We're thrilled to have you on board and can't wait for you to explore the wide range of products we offer. Whether you're looking for the latest trends or everyday essentials, Ammar Mart is here to make your shopping experience enjoyable and rewarding.

If you have any questions or need assistance, our support team is here to help you.

Warm regards,
The Ammar Mart Team
    """
    return subject, message


def account_update_email(full_name):
    subject = "Your Ammar Mart Account Details Have Been Updated"
    message = f"""
Dear {full_name},

This is to inform you that your account details at Ammar Mart have been successfully updated.

If you did not request this change or believe there has been an error, please contact our support team immediately. We're here to ensure your account remains secure and up-to-date.

Thank you for choosing Ammar Mart!

Warm regards,
The Ammar Mart Team
    """
    return subject, message


def account_deletion_email(full_name):
    subject = "Your Ammar Mart Account Has Been Deleted"
    message = f"""
Dear {full_name},

We are writing to confirm that your account with Ammar Mart has been successfully deleted.

We’re sorry to see you go! If this was a mistake or if you have any concerns, please reach out to our support team. We're here to help and would love to have you back anytime.

Thank you for being a part of the Ammar Mart community.

Warm regards,
The Ammar Mart Team
    """
    return subject, message
