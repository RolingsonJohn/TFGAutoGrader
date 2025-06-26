import os
import msal
import requests
import base64
from services.Config import Config as config
from pathlib import Path

class MailSender:
    """
        Módulo encargado de la emisión automática de
        la retroalimentación a los estudiantes del ejercicio enviado.
        Emplea la API msal de Microsoft Graph.
    """

    def __init__(self, endpoint, token= None):
        self.endpoint = endpoint
        self.token = token


    def authenticate(self):
        """
            Método que permite la autenticación
            del usuario en caso de no disponer de un
            token.
        """
        app = msal.PublicClientApplication(
            config.CLIENT_ID,
            authority=config.AUTHORITY,
        )

        result = app.acquire_token_interactive(scopes=config.SCOPES)
        print(config.CLIENT_ID, config.AUTHORITY, config.SCOPES, result)

        if 'access_token' in result:
            self.token = result['access_token']
        else:
            raise Exception(f"No se pudo obtener el token: {result.get('error_description')}")


    def create_attachment(self, data: str, attch_name: str) -> dict:
        """
            Método que permite adjuntar ficheros al mensaje a emitir
            Input:
                - data (str): Texto plano que se quiere emitir.
                - attch_name (str): Nombre del fichero.
        """

        encoded_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        attachment = {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": attch_name,
            "contentBytes": encoded_data,
            "contentType": "text/markdown"
        }

        return attachment
    

    def send_email(self, subject: str, body: str, attch: list, to_email: str):
        """
            Método encargado de enviar el correo especificando
            el destinatario, el asunto y el cuerpo del correo.
            Input:
                - subject (str): Asunto del correo
                - body (str): Cuerpo del mensaje.
                - to_email (str): Correo destinatario
        """

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        email_msg = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ],
                "attachments" : attch
            }
        }

        print(f"{headers}\n\n{email_msg}")
        response = requests.post(self.endpoint, headers=headers, json=email_msg)

        if response.status_code == 202:
            print('Correo enviado exitosamente.')
        else:
            print(f'Error enviando el correo: {response.status_code}')
            print(response.text)