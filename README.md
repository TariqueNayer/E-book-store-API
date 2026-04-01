# E-book-store-API
### A eCommerce backend/browsable API for digital books. 
It is a Portfolio Project, therefore it doesn't use real money during purchases.
## Live Demo:
API Root: https://ebook-store-ico1.onrender.com/api/v1/ <br>
Schema: 
- Redoc: https://ebook-store-ico1.onrender.com/api/schema/redoc/
- Swagger: https://ebook-store-ico1.onrender.com/api/schema/swagger-ui/

Ideally this is an API prroject for a frontend. However, because it is a Portfolio Project.<br> 
For testing purposes, A user can use the browsable API to purchase and download digital ebooks in PDF format.
### Purchase flow:
To purchase a book you must create an 'order'. each new order has a 'status'(payment status) set to Pending (represented by "WT") by default. <br>
then you must go to the pay url and pay. (Sandbox payment. No real money) <br>
The status of that order will be changed to Paid represented by "PD". then you can download the book from that order via the order_download url. <br>
"""   Created: Order : status = WT --> Paid: Order : status = PD --> Download Unlocked  """
#### Step by Step:
- Get book: Go to "..<domain>../api/v1/books/"(GET) to choose a book. and then copy the "ID" of the book. which is a UUID for the book instance in the Database.
- Order: Send a POST request to "/api/v1/orders/" with a JSON body that contains the book ID you copied. example: """ { 'book': '<book_id>' } """ <br>
If using a browser to send the request, you may see the form on the rendered browsable page. afterwards an Order will be visible on "/api/v1/orders/"(GET) once created.
- Pay: Copy the pay url from the response. or copy the order's ID and just go to this "/api/v1/orders/<order_id>/pay/"(POST). a "pay_url"(a Payment link on Sqaure) will be returned.<br>
go to the link in your browser. and finish the sandbox payment prompts by clicking "next" and then "test payment". and the status of your order will be changed to Paid.
- Download: got to "/api/v1/orders/<order_id>/download/"(GET) and download the book from the order.<br>

### Authentication: 
- I used JWT authentication via the third party package "djangorestframework_simplejwt"
- I have implemented __Social Authentication__ with __Google Oauth2__. 
- I used Django rest framework's session authentication for the __Google Oauth Handshake__ to login users.<br>
in the browsable API pages on top left corner, I made an option for browsable users to Login or Signup using their Google account.
- in order to keep the session authentication limited to the handshake. I used httpOnly cookies and enabled CSRF protection. so the JWT tokens can be stored in cookies.

## Tools.
#### API:
Django.<br>
Django Rest Framework.<br>
#### Authentication:
Django Allauth.<br>
Dj_Rest_Auth.<br>
Google Oauth2 authentication.<br>
#### Schema:
DRF_Spectacular. (swagger and redoc)<br>
## Integration:
#### Storage:
[Supabase S3 compatible Storage](https://supabase.com/docs/guides/storage).<br>
#### Social authentication:
[Google Oauth2](https://developers.google.com/identity/protocols/oauth2).<br>
#### Payment Gateway:
[Square Payment Gateway service.](https://developer.squareup.com/docs/devtools/sandbox/overview) Sandbox Payments.
