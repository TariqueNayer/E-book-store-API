# E-book-store-API
### An eCommerce backend/browsable API for digital books. 
It is a Portfolio Project, therefore sandbox payments are used.
## Live Demo:
API Root: https://ebook-store-ico1.onrender.com/api/v1/ <br>
Schema: 
- Redoc: https://ebook-store-ico1.onrender.com/api/schema/redoc/
- Swagger: https://ebook-store-ico1.onrender.com/api/schema/swagger-ui/

## Features:
- Browse and purchase digital books via a fully browsable REST API
- Secure JWT authentication stored in httpOnly cookies
- Google OAuth2 sign-in, accessible directly from the browsable API
- Sandbox payments via Square — full purchase flow without real money
- PDF delivery via signed, time-limited Supabase URLs
- Dual-bucket Supabase storage — private for PDFs, public for cover images
- Auto-generated API schema with Swagger and Redoc


## Purchase flow:
Ideally this is an API project for a frontend. However, for testing purposes, a user can use the browsable API to purchase and download digital ebooks in PDF format.
To purchase a book you must create an 'order'. Each new order has a 'status'(payment status) set to Pending (represented by "WT") by default.
Then you must go to the pay url and pay.
The status of that order will be changed to Paid represented by "PD". Then you can download the book from that order via the order_download url.  
```   Order : status = WT --> Paid --> Order : status = PD --> Download Unlocked  ```
### Step by Step:
- Get book: Go to "..<domain>../api/v1/books/"(GET) to choose a book. and then copy the "ID" of the book. which is a UUID for the book instance in the Database.
- Order: Send a POST request to "/api/v1/orders/" with a JSON body that contains the book ID you copied. example:
```json
    { "book": "<book_id>" }
```
If using a browser to send the request, you may see the form on the rendered browsable page. afterwards an Order will be visible on "/api/v1/orders/"(GET) once created.
- Pay: Copy the pay url from the response. or copy the order's ID and just go to this "/api/v1/orders/<order_id>/pay/"(POST). a "pay_url"(a Payment link on Square) will be returned.
go to the link in your browser. and finish the sandbox payment prompts by clicking "next" and then "test payment". and the status of your order will be changed to Paid.
- Download: go to "/api/v1/orders/<order_id>/download/"(GET) and download the book from the order.  

## Authentication: 
- JWT authentication via the third party package `djangorestframework-simplejwt`
- __Social Authentication__ with __Google Oauth2__. 
- Django rest framework's session authentication.
- Session authentication is scoped only to the Google OAuth handshake. 
  JWT tokens are then stored in httpOnly cookies with CSRF protection enabled.
- The browsable API includes a Login / Signup with Google option in the top-left corner.

## Tech Stack
### API:
- Django
- Django Rest Framework
### Authentication:
- Django Allauth
- Dj_Rest_Auth
- [Google Oauth2](https://developers.google.com/identity/protocols/oauth2)
### Schema:
- DRF_Spectacular (swagger and redoc)
### Storage:
- [Supabase S3 compatible Storage](https://supabase.com/docs/guides/storage)
### Payment Gateway:
- [Square Payment Gateway service](https://developer.squareup.com/docs/devtools/sandbox/overview)
