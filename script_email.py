import yagmail

# Configuração do e-mail
sender_email = "minhavm109@gmail.com"
sender_password = "zbfx zmkl hgkg rliv" 
recipient_email = "minhavm109@gmail.com"
subject = "Arquivo Dados politecnicos"
body = "Segue o arquivo em anexo."
attachment = "dados_politecnicos/dados_politecnicos.zip"

try:
    yag = yagmail.SMTP(sender_email, sender_password)
    yag.send(
        to=recipient_email,
        subject=subject,
        contents=body,
        attachments=attachment
    )
    print("E-mail enviado com sucesso!")
except Exception as e:
    print(f"Erro ao enviar o e-mail: {e}")
