def order_creation_email(full_name, address, order_id, product_title, product_description, product_category, product_brand, quantity, total_amount, order_status):
    subject = f"Order Confirmation - Your Ammar Mart Order #{order_id} Has Been Placed"
    message = f"""
Dear {full_name},

Thank you for shopping with Ammar Mart! Your order has been successfully placed. Here are the details of your order:

ORDER ID:  {order_id}
PRODUCT:  {product_title}
DESCRIPTION:  {product_description}
CATEGORY:  {product_category}
BRAND:  {product_brand}
QUANTITY:  {quantity}
TOTAL AMOUNT:  ${total_amount}
ORDER STATUS:  {order_status}

Your order will be delivered to the following address:

DELIVERY ADDRESS:  
{address}

We will notify you when your order is on its way. Thank you for choosing Ammar Mart!

If you have any questions or need further assistance, please feel free to contact our customer support team.

Best regards,  
The Ammar Mart Team
    """
    return subject, message



def order_update_email(full_name, address, order_id, product_title, product_description, product_category, product_brand, quantity, total_amount, order_status):
    subject = f"Order Update - Your Ammar Mart Order #{order_id} Has Been Updated"
    message = f"""
Dear {full_name},

We wanted to inform you that your order #{order_id} has been updated. Below are the updated details:

Order ID:  {order_id}
Product:  {product_title}
Description:  {product_description}
Category:  {product_category}
Brand:  {product_brand}
Quantity:  {quantity}
Total Amount:  ${total_amount}
Order Status:  {order_status}

The delivery address for your order remains the same:

Delivery Address:  
{address}

Thank you for your continued trust in Ammar Mart. We hope to serve you again soon!

If you have any questions or need further assistance, please feel free to contact our customer support team.

Best regards,  
The Ammar Mart Team
    """
    return subject, message

    
def order_cancellation_email(full_name, order_id, product_title, product_description, product_category, product_brand, quantity, total_amount):
    subject = f"Order Cancellation - Your Ammar Mart Order #{order_id} Has Been Cancelled"
    message = f"""
Dear {full_name},

We regret to inform you that your order #{order_id} has been cance  lled. Below are the details of the cancelled order:

Order ID:  {order_id}
Product:  {product_title}
Description:  {product_description}
Category:  {product_category}
Brand:  {product_brand}
Quantity:  {quantity}
Total Amount:  ${total_amount}

If this cancellation was made by mistake or you have any concerns, please contact our customer support team immediately.

We apologize for any inconvenience this may have caused and hope to serve you better in the future.

Best regards,  
The Ammar Mart Team
    """
    return subject, message
